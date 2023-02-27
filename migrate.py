import json
import logging
import os

import pandas as pd
from rich.console import Console
from rich.progress import track

from src.db import db
from src.models import cases, leads, messages

console = Console()

# Adding filehandler logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("migrate.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


# Loading the leads file
leads_list = json.load(open(os.path.join("configuration", "leads.json")))
config_dict = json.load(open(os.path.join("configuration", "config.json")))


count = 0
total = len(leads_list)
# Start the DB transaction
console.print("Loading messages...")

# Creating a new collection in Firestore
messages_collection = db.collection("messages")

# Multiple documents can be added at once
for message_dict in track(config_dict.get("messages")):
    message = messages.MessageTemplate(
        template_id=message_dict.get("label"),
        template_name=message_dict.get("label"),
        template_type=message_dict.get("type"),
        template_text=message_dict.get("value"),
        template_language=message_dict.get("language", "en"),
    )
    messages_collection.document(message.template_id).set(message.dict())

courts_collection = db.collection("courts")

# Loading the courts file
for court_dict in track(config_dict.get("courts")):
    court = courts.Court(
        code=court_dict.get("value"),
        type=court_dict.get("type"),
        availability=court_dict.get("availability"),
        description=court_dict.get("description"),
        message=court_dict.get("message"),
        country_code=court_dict.get("country_code"),
        name=court_dict.get("label"),
        enabled=court_dict.get("enabled"),
        state=court_dict.get("state"),
    )
    courts_collection.document(court.code).set(court.dict())


batch = db.batch()

# Creating a new collection in Firestore
leads_collection = db.collection("leads")
interactions_collection = db.collection("interactions")
cases_collection = db.collection("cases")


console.print("Loading leads...")
# Loading the contacted leads csv file
cases_contacted = pd.read_csv("configuration/contacted.csv")
cases_contacted["case_id"] = cases_contacted["case_id"].astype(str)
console.print(f"Total leads: {total}")
# Multiple documents can be added at once
for case_id, lead in track(leads_list.items()):
    try:
        ticket_form = lead.get("casenet", {}).get("ticket", {}).get("form", [])
        ticket_form_dict = {
            item["field-id"].replace("-", "_"): item["field-value"]
            for item in ticket_form
        }
        case = cases.Case(
            case_id=case_id,
            disposition=lead.get("casenet", {})
            .get("case_header", {})
            .get("Disposition"),
            judge=lead.get("casenet", {})
            .get("case_header", {})
            .get("Judge/Commissioner Assigned"),
            date_filed=lead.get("casenet", {})
            .get("case_header", {})
            .get("Date Filed"),
            location=lead.get("casenet", {})
            .get("case_header", {})
            .get("Location"),
            case_type=lead.get("casenet", {})
            .get("case_header", {})
            .get("Case Type"),
            state=ticket_form_dict.get("state"),
            court_type=ticket_form_dict.get("court_type"),
            court_city=ticket_form_dict.get("court_city"),
            court_jurisdiction=ticket_form_dict.get("court_jurisdiction"),
            court_phone=ticket_form_dict.get("court_phone"),
            court_time=ticket_form_dict.get("court_time"),
            client_birthdate=ticket_form_dict.get("client_birthdate"),
            client_driver_license=ticket_form_dict.get(
                "client_driver_license"
            ),
            offense=ticket_form_dict.get("offense"),
            ticket_speed=ticket_form_dict.get("ticket_speed"),
            ticket_posted_speed_limit=ticket_form_dict.get(
                "ticket_posted_speed_limit"
            ),
            current_date=ticket_form_dict.get("current_date"),
            charges=lead.get("casenet", {}).get("charges", {}),
            dockets=lead.get("casenet", {}).get("dockets_links", []),
            services=lead.get("casenet", {}).get("services", []),
            headers=lead.get("casenet", {}).get("case_header", {}),
            parties=lead.get("casenet", {}).get("parties", ""),
        )

        # Load the image from the file
        image_path = os.path.join("data", f"{case_id}.png")

        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                image = image_file.read()
                case.image = image

        # Adding the case to the database
        cases_collection.document(case_id).set(case.dict())

        # Lead status
        lead_status = lead.get("status", "not_contacted")

        interactions = lead.get("interactions", [])

        source = None

        last_updated = lead.get("last_updated", None)
        if interactions:
            lead_status = "contacted"
            source = "BeenVerified"
            for interaction_dict in interactions:
                interaction = messages.Interaction(
                    case_id=case_id,
                    creation_date=interaction_dict.get("date"),
                    message=interaction_dict.get("message"),
                    type=interaction_dict.get("type"),
                    phone=interaction_dict.get("phone"),
                    status=interaction_dict.get("status"),
                )
                last_updated = interaction_dict.get("date")
                interactions_collection.add(interaction.dict())

        if str(case_id) in cases_contacted["case_id"].values:
            lead_status = "converted"
        # Adding the lead to the database
        lead = leads.Lead(
            case_id=case_id,
            court_code=lead.get("court_code"),
            first_name=lead.get("first_name"),
            last_name=lead.get("last_name"),
            age=lead.get("age"),
            year_of_birth=lead.get("year_of_birth"),
            phone=lead.get("phone"),
            email=lead.get("email"),
            address=lead.get("address"),
            city=lead.get("city"),
            state=lead.get("state"),
            zip_code=lead.get("zip_code"),
            county=lead.get("county"),
            case_date=lead.get("case_date"),
            last_updated=lead.get("last_update", last_updated),
            status=lead_status,
            source=source,
            charges=lead.get("charges"),
            disposition=case.disposition,
        )

        leads_collection.document(case_id).set(lead.dict())
    except Exception as e:
        console.print(f"Failed to add case : {case_id} - {e}")
        logger.error(f"Failed to add case : {case_id} - {e}")
        continue
    count += 1

# Cases that are not in the cases contacted csv file
cases_not_contacted = cases_contacted[
    ~cases_contacted["case_id"].isin(leads_list.keys())
]

# Adding the cases that are not in the database
for case_id in cases_not_contacted["case_id"].values:
    try:
        lead = leads.Lead(
            case_id=case_id,
            court_code=None,
            first_name=None,
            last_name=None,
            age=None,
            year_of_birth=None,
            phone=None,
            email=None,
            address=None,
            city=None,
            state=None,
            zip_code=None,
            county=None,
            case_date=None,
            last_updated=None,
            status="converted",
            source=None,
            charges=None,
            disposition=None,
        )

        leads_collection.document(case_id).set(lead.dict())
    except Exception as e:
        console.print(f"Failed to add case : {case_id} - {e}")
        logger.error(f"Failed to add case : {case_id} - {e}")
        continue

batch.commit()
