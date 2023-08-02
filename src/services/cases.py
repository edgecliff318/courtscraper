from google.cloud.firestore_v1.base_query import FieldFilter, Or
from pydantic import ValidationError

from src.db import db
from src.models import cases


def get_cases(
    court_code_list=None, start_date=None, end_date=None, disposition=None
):
    cases_list = db.collection("cases")
    if court_code_list is not None and court_code_list:
        if not isinstance(court_code_list, list):
            court_code_list = [
                court_code_list,
            ]
        cases_list = db.collection("cases").where(
            field_path="court_code", op_string="in", value=court_code_list
        )

    if start_date is not None:
        cases_list = cases_list.where(
            field_path="case_date", op_string=">=", value=start_date
        )
    if end_date is not None:
        cases_list = cases_list.where(
            field_path="case_date", op_string="<=", value=end_date
        )
    if disposition is not None:
        cases_list = cases_list.where(
            field_path="disposition", op_string="==", value=status
        )

    cases_list = cases_list.stream()

    return [cases.Case(**m.to_dict()) for m in cases_list]


def get_single_case(case_id) -> cases.Case:
    case = db.collection("cases").document(case_id).get()
    if not case.exists:
        return None
    return cases.Case(**case.to_dict())


def get_many_cases(case_ids: list) -> list:
    cases_list = (
        db.collection("cases").where("case_id", "in", case_ids).stream()
    )
    return [cases.Case(**m.to_dict()) for m in cases_list]


def insert_case(case: cases.Case) -> None:
    db.collection("cases").document(case.case_id).set(case.dict())


def update_case(case: cases.Case) -> None:
    db.collection("cases").document(case.case_id).update(case.dict())


def search_cases(search_term: str) -> list:
    filter_first_name = FieldFilter(
        "first_name", "==", str(search_term).upper()
    )
    filter_last_name = FieldFilter("last_name", "==", str(search_term).upper())
    filter_case_id = FieldFilter("case_id", "==", search_term)

    or_filter = Or(
        filters=[filter_first_name, filter_last_name, filter_case_id]
    )

    cases_list = db.collection("cases").where(filter=or_filter).stream()

    def ignore_error(c):
        try:
            return cases.Case(**c.to_dict())
        except ValidationError:
            return None

    outputs = [cases.Case(**m.to_dict()) for m in cases_list]
    return [o for o in outputs if o is not None]
