import logging

import dash
import dash.html as html
from dash import Input, Output, State, callback

from src.components.toast import build_toast
from src.core.config import get_settings
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
