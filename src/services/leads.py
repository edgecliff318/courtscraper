import logging

import pandas as pd

from src.db import db
from src.models import leads

logger = logging.getLogger(__name__)


def get_leads(
    court_code_list=None, start_date=None, end_date=None, status=None
):
    # Exclude the field "report" from the collection schema
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

    leads_list = leads_list.stream()

    return [leads.Lead(**m.to_dict()) for m in leads_list]


def get_single_lead(case_id):
    lead = (
        db.collection("leads")
        .select([f for f in leads.Lead.__fields__.keys() if f != "report"])
        .where("case_id", "==", case_id)
        .stream()
    )
    lead = list(lead)
    if not lead:
        return None
    lead = lead[0]
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

    if leads_list:
        returned_list = []
        alcohol_related = [
            x for x in leads_list if "alcohol" in x.charges_description.lower()
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
