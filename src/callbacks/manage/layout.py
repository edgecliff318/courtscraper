import logging
from calendar import c

import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, callback

from src.core.dynamic_fields import CaseDynamicFields
from src.services import cases, templates

logger = logging.Logger(__name__)


def get_case_text(case):
    charges = case.charges
    charges_text = ""
    for charge in charges:
        charges_text += f"{charge.get('charge_filingdate')} - {charge.get('charge_description')}"

    case_data = case.model_dump()
    case_data = CaseDynamicFields().update(case, case_data)
    return (
        f"{case.case_id} {case.first_name} {case.middle_name} {case.last_name} - {case.birth_date} -"
        f" {charges_text} - Court: {case_data.get('court_date')} at {case_data.get('court_time')} "
    )


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
            "label": get_case_text(c),
            "value": c.case_id,
        }
        for c in search_cases
    ], ""


# When selecting value from case select, update the case id in the URL
@callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("case-select", "value"),
    prevent_initial_call=True,
)
def goto_case(case_id):
    if case_id is None:
        return dash.no_update
    return f"/manage/cases/{case_id}"


def toggle_drawer(n_clicks, opened):
    return not opened


for modal in [
    "modal-court-preview",
    "modal-prosecutor-preview",
    "modal-client-preview",
]:
    callback(
        Output(modal, "opened"),
        Input(f"{modal}-button", "n_clicks"),
        State(modal, "opened"),
        prevent_initial_call=True,
    )(toggle_drawer)


@callback(
    Output("section-court-select-template", "data"),
    Output("section-prosecutor-select-template", "data"),
    Output("section-client-select-template", "data"),
    Input("case-select", "value"),
)
def render_select_template_options(case_id):
    templates_list = templates.get_templates()

    court_template_options = [
        {"label": t.name, "value": t.id}
        for t in templates_list
        if t.category == "court"
    ]

    prosecutor_template_options = [
        {"label": t.name, "value": t.id}
        for t in templates_list
        if t.category == "prosecutor"
    ]

    client_template_options = [
        {"label": t.name, "value": t.id}
        for t in templates_list
        if t.category == "client"
    ]

    return (
        court_template_options,
        prosecutor_template_options,
        client_template_options,
    )
