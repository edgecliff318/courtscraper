from collections import defaultdict
from datetime import datetime
from typing import MutableMapping

from google.cloud.firestore_v1.base_query import And, FieldFilter, Or
from pydantic import ValidationError

from src.core.base import BaseService
from src.core.dynamic_fields import CaseDynamicFields
from src.db import db
from src.models import cases
from src.services.participants import ParticipantsService


def get_case_dict(case) -> dict:
    case_dict = case.to_dict()

    # Exclude the update_time and create_time
    case_dict["update_time"] = case.update_time
    case_dict["create_time"] = case.create_time

    return case_dict


def get_cases(
    court_code_list=None,
    start_date=None,
    end_date=None,
    disposition=None,
    source=None,
    flag=None,
    limit=None,
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

    if flag is not None:
        cases_list = cases_list.where(
            field_path="flag", op_string="==", value=flag
        )

    if limit is not None:
        # sort by update_time
        cases_list = cases_list.order_by("update_time", direction="DESCENDING")
        cases_list = cases_list.limit(limit)

    cases_list = cases_list.stream()

    return [cases.Case(**get_case_dict(m)) for m in cases_list]


def get_single_case(case_id) -> cases.Case:
    case = db.collection("cases").document(case_id).get()
    if not case.exists:
        return None
    return cases.Case(**get_case_dict(case))


def get_many_cases(case_ids: list) -> list:
    cases_list = (
        db.collection("cases").where("case_id", "in", case_ids).stream()
    )

    return [cases.Case(**get_case_dict(m)) for m in cases_list]


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

    outputs = [cases.Case(**get_case_dict(m)) for m in cases_list]
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
    case = get_single_case(case_id)
    case_data = case.model_dump()

    case_data = flatten(case_data)

    case_data = CaseDynamicFields().update(case, case_data)

    case_data = {f"case_{key}": value for key, value in case_data.items()}

    case_data["invoice_link"] = "{{invoice}}"

    if case_data.get("case_middle_name") is None:
        case_data["case_middle_name"] = ""

    # Adding the current date short
    case_data["current_date_short"] = (
        datetime.now().strftime("%B %d, %Y").upper()
    )

    # Transform to defaultdict
    case_data = defaultdict(lambda: default_value, case_data)

    return case_data


def get_mycase_id(case_id):
    case = get_single_case(case_id)
    participants_service = ParticipantsService()

    participants_list = participants_service.get_items(
        id=case.participants, role="defendant"
    )

    if len(participants_list) == 0:
        raise Exception("No defendant selected for this case")

    participant = participants_list[0]

    client_id = participant.mycase_id

    return participant, client_id


class CasesService(BaseService):
    collection_name = "cases"
    serializer = cases.Case
