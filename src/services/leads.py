from src.db import db
from src.models import leads


def get_leads(court_code_list=None, start_date=None, end_date=None, status=None):
    leads_list = db.collection("leads")
    if court_code_list is not None and court_code_list:
        if not isinstance(court_code_list, list):
            court_code_list = [
                court_code_list,
            ]
        leads_list = db.collection("leads").where("court_code", "in", court_code_list)

    if start_date is not None:
        leads_list = leads_list.where("creation_date", ">=", start_date)
    if end_date is not None:
        leads_list = leads_list.where("creation_date", "<=", end_date)
    if status is not None:
        leads_list = leads_list.where("status", "==", status)

    leads_list = leads_list.stream()

    return [leads.Lead(**m.to_dict()) for m in leads_list]


def get_single_lead(case_id):
    lead = db.collection("leads").document(case_id).get()
    return leads.Lead(**lead.to_dict())


def insert_lead(lead: leads.Lead):
    db.collection("leads").document(lead.case_id).set(lead.dict())
