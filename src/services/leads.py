import logging
from datetime import datetime, timedelta

import pandas as pd
from google.cloud.firestore_v1.base_query import And, FieldFilter, Or

from src.core.base import BaseService
from src.db import db
from src.models import leads

logger = logging.getLogger(__name__)


def get_leads(
    court_code_list=None,
    start_date=None,
    end_date=None,
    status=None,
    source=None,
):
    # Exclude the field "report" from the collection schema
    leads_list = db.collection("leads").select(
        [f for f in leads.Lead.model_fields.keys() if f != "report"]
    )
    if court_code_list is not None and court_code_list:
        if not isinstance(court_code_list, list):
            court_code_list = [
                court_code_list,
            ]
        leads_list = db.collection("leads").where(
            "court_code", "in", court_code_list
        )

    if start_date is not None:
        if source == "website":
            # Transform start_date to timestamp in ms
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            start_date = start_date.timestamp() * 1000
            leads_list = leads_list.where("creation_date", ">=", start_date)
        else:
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            leads_list = leads_list.where("case_date", ">=", start_date)

    if end_date is not None:
        if source == "website":
            # Transform end_date to timestamp in ms
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1)
            end_date = end_date.timestamp() * 1000
            leads_list = leads_list.where("creation_date", "<=", end_date)
        else:
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            leads_list = leads_list.where("case_date", "<=", end_date)

    if status is not None:
        leads_list = leads_list.where("status", "==", status)

    if source is not None:
        leads_list = leads_list.where("source", "==", source)

    leads_list = leads_list.stream()

    def get_lead_dict(lead):
        lead_dict = lead.to_dict()
        lead_dict["id"] = lead.id
        return lead_dict

    return [leads.Lead(**get_lead_dict(lead)) for lead in leads_list]


def get_single_lead(case_id):
    lead = (
        db.collection("leads")
        .select([f for f in leads.Lead.model_fields.keys() if f != "report"])
        .where(filter=FieldFilter("case_id", "==", case_id))
        .stream()
    )
    lead = list(lead)
    if not lead:
        return None
    lead = lead[0]
    return leads.Lead(**lead.to_dict())


def get_lead(lead_id, fields=None):
    lead = db.collection("leads").document(lead_id).get()
    if not lead.exists:
        return None

    return leads.Lead(**lead.to_dict())


def get_lead_by_phone(phone):
    selected_fields = [
        f for f in leads.Lead.__fields__.keys() if f != "report"
    ]
    queried_leads_in_list = list(
        db.collection("leads")
        .select(selected_fields)
        .where("phones", "array_contains", phone)
        .stream()
    )

    lead_objects = [
        leads.Lead(**doc.to_dict()) for doc in queried_leads_in_list
    ]

    if len(lead_objects) > 1:
        logger.warning(
            f"Found multiple leads with phone number {phone}."
            "Returning the first one."
        )

    return lead_objects[0] if lead_objects else None


def get_last_lead(
    court_code_list=None,
    start_date=None,
    end_date=None,
    status=None,
    limit=1,
    search_limit=1000,
):
    search_limit = int(search_limit)
    limit = int(limit)
    leads_list = db.collection("leads").select(
        [f for f in leads.Lead.__fields__.keys() if f != "report"]
    )
    if court_code_list is not None and court_code_list:
        if not isinstance(court_code_list, list):
            court_code_list = [
                court_code_list,
            ]
        leads_list = db.collection("leads").where(
            "court_code", "in", court_code_list
        )

    if start_date is not None:
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        leads_list = leads_list.where("case_date", ">=", start_date)
    if end_date is not None:
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        leads_list = leads_list.where("case_date", "<=", end_date)
    if status is not None:
        leads_list = leads_list.where("status", "==", status)

    leads_list = (
        leads_list.order_by("case_date", direction="DESCENDING")
        .select([f for f in leads.Lead.__fields__.keys() if f != "report"])
        .limit(search_limit)
        .stream()
    )
    leads_list = [leads.Lead(**m.to_dict()) for m in leads_list]

    leads_list = [l for l in leads_list if l.charges_description is not None]

    if status == "prioritized":
        leads_list = [l for l in leads_list]
        if leads_list:
            if limit == 1:
                return leads_list[0]
            return leads_list
        return None

    if leads_list:
        returned_list = []
        alcohol_related = [
            x
            for x in leads_list
            if "alcohol" in x.charges_description.lower()
            or "dui" in x.charges_description.lower()
            or "intoxicated" in x.charges_description.lower()
            or "dwi" in x.charges_description.lower()
        ]
        if alcohol_related:
            returned_list += alcohol_related
            if limit == 1:
                return returned_list[0]
            if len(returned_list) >= limit:
                return returned_list

        insurance_revoked = [
            x
            for x in leads_list
            if x.charges_description is not None
            and (
                "insurance" in x.charges_description.lower()
                or "license" in x.charges_description.lower()
            )
        ]
        if insurance_revoked:
            returned_list += insurance_revoked
            if limit == 1:
                return returned_list[0]
            if len(returned_list) >= limit:
                return returned_list

        careless_imprudent = [
            x
            for x in leads_list
            if x.charges_description is not None
            and (
                "careless" in x.charges_description.lower()
                or "imprudent" in x.charges_description.lower()
            )
        ]
        if careless_imprudent:
            returned_list += careless_imprudent
            if limit == 1:
                return returned_list[0]
            if len(returned_list) >= limit:
                return returned_list

        high_speeding = [
            x
            for x in leads_list
            if x.charges_description is not None
            and "20-25 mph over" in x.charges_description.lower()
        ]

        if high_speeding:
            returned_list += high_speeding
            if limit == 1:
                return returned_list[0]
            if len(returned_list) >= limit:
                return returned_list

        speeding = [
            x
            for x in leads_list
            if x.charges_description is not None
            and "speeding" in x.charges_description.lower()
        ]
        if speeding:
            returned_list += speeding
            if limit == 1:
                return returned_list[0]
            if len(returned_list) >= limit:
                return returned_list

        returned_list += leads_list
        if limit == 1:
            return returned_list[0]
        return returned_list

    else:
        return None


def insert_lead(lead: leads.Lead):
    db.collection("leads").document(lead.case_id).set(lead.model_dump())


def update_lead_status(case_id, status):
    db.collection("leads").document(case_id).update({"status": status})


def update_multiple_leads_status(case_ids, status):
    # Update multiple leads status in a single batch
    batch = db.batch()
    for case_id in case_ids:
        ref = db.collection("leads").document(case_id)
        batch.update(ref, {"status": status})

    batch.commit()


def update_lead(lead: leads.Lead):
    db.collection("leads").document(lead.case_id).update(lead.model_dump())


def patch_lead(case_id, **kwargs):
    db.collection("leads").document(case_id).update(kwargs)


def insert_lead_from_case(case):
    # Insert the lead in the leads table:
    try:
        lead_parsed = leads.Lead.model_validate(case)
        lead_loaded = get_single_lead(lead_parsed.case_id)
        if lead_loaded is None:
            insert_lead(lead_parsed)
            logger.info(f"Succeeded to insert lead for {case.get('case_id')}")
    except Exception as e:
        logger.error(f"Failed to parse lead {case} - {e}")


def delete_lead(lead_id):
    db.collection("leads").document(lead_id).delete()


class LeadsService(BaseService):
    collection_name = "leads"
    serializer = leads.Lead

    def get_leads_summary(self):
        # First timestamp of the day
        start_date = (
            datetime.now()
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .timestamp()
            * 1000
        )
        end_date = (
            datetime.now()
            .replace(hour=23, minute=59, second=59, microsecond=999)
            .timestamp()
            * 1000
        )

        filters_bases = [
            FieldFilter("last_updated", ">=", start_date),
            FieldFilter("last_updated", "<=", end_date),
        ]

        # Return dummy data

        return {
            "leads_added_today": 10,
            "leads_not_contacted": 5,
            "leads_converted": 2,
        }

        # Get all the leads for today
        leads_added_today = self.count_items(
            filters=And(filters=filters_bases)
        )

        # Get all the leads with a status not_contacted
        leads_not_contacted = self.count_items(
            filters=And(
                filters=filters_bases
                + [FieldFilter("status", "==", "not_contacted")]
            )
        )

        # Get all the leads that were converted
        leads_converted = self.count_items(
            filters=And(
                filters=filters_bases
                + [FieldFilter("status", "==", "converted")]
            )
        )

        return {
            "leads_added_today": leads_added_today,
            "leads_not_contacted": leads_not_contacted,
            "leads_converted": leads_converted,
        }


if __name__ == "__main__":
    today = datetime.now()
    lead = get_last_lead(
        start_date=today - timedelta(days=7),
        end_date=today + timedelta(days=1),
        status="new",
        limit=1,
    )
    print(lead)
