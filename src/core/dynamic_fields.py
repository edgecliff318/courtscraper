from datetime import datetime

from src.models.cases import Case


class CaseDynamicFields:
    def __init__(self) -> None:
        pass

    def update_court_date(self, case: Case, case_data: dict):
        court_date = None
        court_time = None

        if case.dockets is not None:
            for docket in case.dockets:
                if (
                    docket.get("docket_code") == "SCHR"
                    or docket.get("docket_code") == "SCIR"
                ):
                    # Get the associated_docketscheduledinfo
                    schedule = docket.get("associated_docketscheduledinfo", {})
                    if isinstance(schedule, list) and len(schedule) > 0:
                        schedule = schedule.pop()
                    else:
                        schedule = {}
                    court_date = schedule.get("associated_date", "")
                    court_time = schedule.get("associated_time", "")
                    break

        case_data["court_date"] = court_date
        case_data["court_time"] = court_time
        return case_data

    def update_judge(self, case: Case, case_data: dict):
        judge = None

        if case.judge is not None:
            middle_name = case.judge.get("middle_name", None)
            if middle_name is None:
                judge = f"{case.judge.get('first_name', '')} {case.judge.get('last_name', '')}"
            else:
                judge = f"{case.judge.get('first_name', '')} {middle_name} {case.judge.get('last_name', '')}"

        case_data["judge"] = judge
        return case_data

    def update_charges(self, case: Case, case_data: dict):
        # Adding charges
        charges = case_data.get("charges", [{"charge_description": ""}])
        if charges:
            case_data["charges_description"] = charges[0].get(
                "charge_description", ""
            )
        else:
            case_data["charges_description"] = ""

        return case_data

    def update_current_date(self, case: Case, case_data: dict):
        case_data["current_date_short"] = (
            datetime.now().strftime("%B %d, %Y").upper()
        )
        return case_data

    def update_location(self, case: Case, case_data: dict):
        # Transform case location
        location = case.location
        if location is None:
            location = ""

        court_desc = case.court_desc
        if court_desc is None:
            court_desc = ""

        if (
            "municipal" in court_desc.lower()
            or "municipal" in location.lower()
        ):
            case_data["city"] = (
                location.lower().replace("municipal", "").upper()
            )
            case_data["location"] = "MUNICIPAL"
        elif "circuit" in court_desc.lower() or "circuit" in location.lower():
            case_data["city"] = location.lower().replace("circuit", "").upper()
            if "county" not in case_data["city"].lower():
                case_data["city"] += " COUNTY"
            case_data["location"] = "CIRCUIT"

        case_data["city"] = case_data.get("city", "").replace("COURT", "")
        return case_data

    def update(self, case: Case, case_data: dict):
        case_data = self.update_court_date(case, case_data)
        case_data = self.update_judge(case, case_data)
        case_data = self.update_charges(case, case_data)
        case_data = self.update_current_date(case, case_data)
        case_data = self.update_location(case, case_data)
        return case_data
