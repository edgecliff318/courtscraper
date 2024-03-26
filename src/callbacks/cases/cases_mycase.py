import logging

import dash
import dash.html as html
import pandas as pd
from dash import Input, Output, State, callback

from src.components.toast import build_toast
from src.core.config import get_settings
from src.core.dynamic_fields import CaseDynamicFields
from src.loader.mycase import MyCase
from src.services import cases, leads

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("case-upload-to-mycase-button-status", "children"),
    Input("case-upload-to-mycase-button", "n_clicks"),
    State("case-id", "children"),
)
def upload_case_to_mycase(btn, case_id):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "case-upload-to-mycase-button":
        try:
            case_id = str(case_id)
            case_details = cases.get_single_case(case_id)
            lead_details = leads.get_single_lead(case_id)

            mycase = MyCase(url="", password="", username="")

            mycase.login()

            if case_details is None:
                toast = build_toast(
                    "Was unable to find the case in the database",
                    "An error occured ❌",
                    color="danger",
                )
                return toast

            if lead_details is None:
                toast = build_toast(
                    "Was unable to find the lead in the database",
                    "An error occured ❌",
                    color="danger",
                )
                return toast

            client_id = mycase.add_contact(lead_details, case_details)

            # Update the lead with the mycase client id
            leads.patch_lead(case_id, mycase_client_id=client_id)

            # Upload the case
            mycase.add_case(lead_details, case_details, client_id)

            # Add event to the case
            mycase_id = mycase.search_case(case_id=case_id)

            if mycase_id is None:
                toast = build_toast(
                    "Was unable to find the case in MyCase",
                    "An error occured ❌",
                    color="danger",
                )
                return toast

            mycase_id = mycase_id.get("record_id")

            case_data = {}
            case_data = CaseDynamicFields().update(case_details, case_data)

            event_time = case_data.get("court_time", "")
            event_date = case_data.get("court_date", "")

            start_date = event_date
            start_time = event_time
            end_date = event_date
            # Add 1 hour to the time
            end_time = pd.to_datetime(event_time) + pd.Timedelta(hours=1)
            end_time = end_time.strftime("%I:%M %p")

            location_name = (
                f"{case_data.get('location')} Court of {case_data.get('city')}"
            )

            sharing_rules = mycase.reload_sharing(mycase_id)
            event_details = {
                "name": (
                    f"{location_name} - {case_details.first_name}"
                    f" {case_details.last_name} - {case_id}"
                ),
                "description": case_details.case_desc,
                "start_date": start_date,
                "start_time": start_time,
                "end_date": end_date,
                "end_time": end_time,
                "location_name": location_name,
                "sharing_rules": sharing_rules.get("client_permissions", [])
                + [v.get("id") for v in sharing_rules.get("lawyers", [])],
            }

            mycase.add_event(
                mycase_case_id=mycase_id,
                event_details=event_details,
            )

            output = html.Div(
                [
                    build_toast(
                        "The case was successfully added to MyCase",
                        "Case added to MyCase ✅",
                    ),
                ],
            )
            return output
        except Exception as e:
            toast = build_toast(
                f"The case failed to upload to MyCase {e}",
                "An error occured ❌",
                color="danger",
            )
            return toast
