import logging

import dash
import dash.html as html
from dash import Input, Output, State, callback, ctx

from src.components.toast import build_toast
from src.core.config import get_settings
from src.services import cases

logger = logging.Logger(__name__)


@callback(
    Output("case-select", "data"),
    Output("case-select", "select-error"),
    Input("case-select", "searchValue"),
)
def case_select_data(value):
    if value is None or value == "":
        return dash.no_update, dash.no_update

    search_cases = cases.search_cases(value)
    if len(search_cases) == 0:
        return [
            {
                "label": "No cases found",
                "value": "no-cases",
            },
        ], "No cases found"
    return [
        {
            "label": f"{c.case_id}# {c.first_name} {c.last_name} {c.court_code}",
            "value": c.case_id,
        }
        for c in search_cases
    ], ""
