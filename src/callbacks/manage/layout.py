import logging

import dash
from dash import Input, Output, State, callback

from src.services import cases, templates

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
            "label": f"{c.case_id}# "
            f"{c.first_name} {c.last_name} {c.court_code}",
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
    "modal-court-submit",
    "modal-prosecutor-preview",
    "modal-prosecutor-submit",
    "modal-client-preview",
    "modal-client-submit",
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
