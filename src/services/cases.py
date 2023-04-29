from src.db import db
from src.models import cases


def get_cases(
    court_code_list=None, start_date=None, end_date=None, status=None
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
    if status is not None:
        cases_list = cases_list.where(
            field_path="status", op_string="==", value=status
        )

    cases_list = cases_list.stream()

    return [cases.Case(**m.to_dict()) for m in cases_list]


def get_single_case(case_id) -> cases.Case:
    case = db.collection("cases").document(case_id).get()
    return cases.Case(**case.to_dict())


def insert_case(case: cases.Case) -> None:
    db.collection("cases").document(case.case_id).set(case.dict())
