import datetime
import json
import logging

import dash
from dash import Input, Output, State, callback
from rich.console import Console

from src.components.toast import build_toast
from src.core.config import get_settings
from src.loader.leads import CaseNet
from src.models import cases as cases_model
from src.models import leads as leads_model
from src.services import cases as cases_service
from src.services import courts
from src.services import leads as leads_service
from src.services.settings import get_account

logger = logging.Logger(__name__)
console = Console()
settings = get_settings()


@callback(
    Output("court-selector-overview", "data"),
    Input("url", "pathname"),
)
def render_content_persona_details_selector(pathname):
    courts_list = courts.get_courts()
    options = [{"label": c.name, "value": c.id} for c in courts_list]
    return options


@callback(
    Output("search-results", "children"),
    Input("search-button", "n_clicks"),
    State("case-number", "value"),
    State("court-selector-overview", "value"),
    State("first-name-search", "value"),
    State("middle-name-search", "value"),
    State("last-name-search", "value"),
)
def refresh_case(btn, case_id, court_code, first_name, middle_name, last_name):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "search-button":
        try:
            case_id = str(case_id)
            case_details = {
                "caseNumber": case_id,
            }
            case_net_account = get_account("case_net_missouri")
            case_net = CaseNet(
                url=case_net_account.url,
                username=case_net_account.username,
                password=case_net_account.password,
            )
            if isinstance(court_code, list):
                court_code = court_code[0]

            court = courts.get_single_court(court_code)
            date = datetime.datetime.now().date()
            # US Format
            date_formatted = date.strftime("%m/%d/%Y")
            case = case_net.get_single_case(
                case_details,
                court=court,
                date=date_formatted,
            )

            try:
                case_parsed = cases_model.Case.parse_obj(case)
                cases_service.insert_case(case_parsed)
            except Exception as e:
                # Save the case in a file for a manual review
                with open(
                    f"cases_to_review/{date}_{court.code}_{case.get('case_id')}.json",
                    "w",
                ) as f:
                    # Transform PosixPath to path in the dict case
                    json.dump(case, f, default=str)
                console.log(f"Failed to parse case {case} - {e}")
            try:
                lead_parsed = leads_model.Lead.parse_obj(case)
                lead_loaded = leads_service.get_single_lead(
                    lead_parsed.case_id
                )
                if lead_loaded is None:
                    leads_service.insert_lead(lead_parsed)
            except Exception as e:
                console.log(f"Failed to parse lead {case} - {e}")

            toast = build_toast(
                "The case was retrieved successfully" "Case refreshed ✅",
            )
            return toast
        except Exception as e:
            toast = build_toast(
                f"The case could not be found {e}",
                "An error occurred ❌",
                color="danger",
            )
            return toast
