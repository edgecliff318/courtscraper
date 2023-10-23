from collections import defaultdict
from datetime import datetime
from typing import MutableMapping

from google.cloud.firestore_v1.base_query import And, FieldFilter, Or
from pydantic import ValidationError

from src.db import db
from src.models import cases


def get_cases(
    court_code_list=None,
    start_date=None,
    end_date=None,
    disposition=None,
    source=None,
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
            field_path="disposition", op_string="==", value=disposition
        )

    if source is not None:
        cases_list = cases_list.where(
            field_path="source", op_string="==", value=source
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
    db.collection("cases").document(case.case_id).set(case.model_dump())


def update_case(case: cases.Case) -> None:
    db.collection("cases").document(case.case_id).update(case.model_dump())


def patch_case(case_id: str, data: dict) -> None:
    db.collection("cases").document(case_id).update(data)


def search_cases(search_term: str) -> list:
    composed = search_term.split(" ")
    if len(composed) == 1 or composed[1] == "":
        filter_first_name = FieldFilter(
            "first_name", "==", str(search_term).upper()
        )
        filter_last_name = FieldFilter(
            "last_name", "==", str(search_term).upper()
        )
        filter_case_id = FieldFilter("case_id", "==", search_term)

        or_filter = Or(
            filters=[filter_first_name, filter_last_name, filter_case_id]
        )
    else:
        filter_first_name = FieldFilter(
            "first_name", "==", str(composed[0]).upper()
        )
        filter_last_name = FieldFilter(
            "last_name", ">=", str(composed[1]).upper()
        )

        and_filter = And(filters=[filter_first_name, filter_last_name])

        filter_first_name_inv = FieldFilter(
            "first_name", "==", str(composed[1]).upper()
        )
        filter_last_name_inv = FieldFilter(
            "last_name", ">=", str(composed[0]).upper()
        )
        and_filter_inv = And(
            filters=[filter_first_name_inv, filter_last_name_inv]
        )

        or_filter = Or(filters=[and_filter, and_filter_inv])

    cases_list = db.collection("cases").where(filter=or_filter).stream()

    def ignore_error(c):
        try:
            return cases.Case(**c.to_dict())
        except ValidationError:
            return None

    outputs = [cases.Case(**m.to_dict()) for m in cases_list]
    return [o for o in outputs if o is not None]


def flatten(dictionary, parent_key="", separator="_"):
    items = []
    for key, value in dictionary.items():
        new_key = parent_key + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(flatten(value, new_key, separator=separator).items())
        else:
            items.append((new_key, value))
    return dict(items)


def get_context_data(case_id, default_value="!!!TO_FILL!!!") -> defaultdict:
    case_data = get_single_case(case_id).model_dump()

    case_data = flatten(case_data)
    case_data = {f"case_{key}": value for key, value in case_data.items()}

    if case_data.get("case_middle_name") is None:
        case_data["case_middle_name"] = ""

    # Adding the current date short
    case_data["current_date_short"] = (
        datetime.now().strftime("%B %d, %Y").upper()
    )

    # Transform to defaultdict
    case_data = defaultdict(lambda: default_value, case_data)

    return case_data
