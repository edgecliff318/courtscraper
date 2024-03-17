import dash_mantine_components as dmc
from dash import dcc

import src.models as models
import src.services.cases as cases_service
from src.core.dynamic_fields import CaseDynamicFields
from src.services.participants import ParticipantsService


def attach_participants(case_id):
    participants_service = ParticipantsService()
    case = cases_service.get_single_case(case_id)
    computed_fields = CaseDynamicFields().update(case, {})

    participants = case.parties
    if participants is None:
        return dmc.Alert(
            "No participants found", color="red", variant="filled"
        )

    output = []

    participants_ids = case.participants

    if participants_ids is None:
        participants_ids = []

    for participant_single in participants:
        mapping = {
            "desc": "role",
            "addr_city": "city",
            "addr_line1": "address",
            "addr_statcode": "state",
            "addr_zip": "zip_code",
            "birth_date": "date_of_birth",
            "formatted_telephone": "phone",
        }

        role_mapping = {
            "DFT": "defendant",
            "PA": "prosecutor",
        }

        participant_single = {
            mapping.get(k, k): v for k, v in participant_single.items()
        }

        participant_single["role"] = role_mapping.get(
            participant_single["desc_code"], "other"
        )

        participant_instance = models.Participant(**participant_single)

        if participant_instance.role == "prosecutor":
            participant_instance.first_name = "Prosecutor"
            location = computed_fields.get(
                "location", participant_instance.last_name
            )
            city = computed_fields.get("city", participant_instance.city)
            participant_instance.last_name = f"{location} Court - {city}"
            participant_instance.date_of_birth = None
            participant_instance.organization = f"{location} Court - {city}"

        # Check if another participan instance exists
        participant_exists = participants_service.get_items(
            first_name=participant_instance.first_name,
            last_name=participant_instance.last_name,
            date_of_birth=participant_instance.date_of_birth,
        )

        if len(participant_exists) > 0:
            links = []
            for participant_db in participant_exists:
                output_message = dcc.Link(
                    f"{participant_db.first_name} {participant_db.last_name} - {participant_db.role}",
                    href=f"/manage/participants/{participant_db.id} \n",
                )

                links += [output_message]

            output += [
                dmc.Alert(
                    [
                        "Participant already exists: ",
                    ]
                    + links,
                    color="red",
                    variant="filled",
                    withCloseButton=True,
                )
            ]

            continue

        participant_created = participants_service.create_item(
            participant_instance
        )

        item_link = dcc.Link(
            "Click here to edit participant",
            href=f"/manage/participants/{participant_created.id}",
        )

        participants_ids.append(participant_created.id)

        output_message = dmc.Alert(
            [
                (
                    "New Participant created, "
                    "you can update it in this screen: "
                ),
                item_link,
            ],
            color="green",
            title=f"{participant_instance.first_name} {participant_instance.last_name} added to the DB",
            variant="light",
            withCloseButton=True,
        )

        output.append(output_message)

    cases_service.patch_case(
        case_id=case_id, data={"participants": participants_ids}
    )

    return output
