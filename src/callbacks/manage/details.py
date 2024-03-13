import logging

import dash
import dash_mantine_components as dmc
from dash import Input, Output, callback, dcc
from dash_iconify import DashIconify

import src.services.cases as cases_service
from src.core.config import get_settings
from src.core.participants import attach_participants
from src.services.participants import ParticipantsService

logger = logging.getLogger(__name__)
settings = get_settings()


@callback(
    Output("case-details-output", "children", allow_duplicate=True),
    Input("case-manage-insert-participants", "n_clicks"),
    Input("case-details-id", "data"),
    prevent_initial_call=True,
)
def edit_component(insert, case_id):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    if ctx.triggered[0]["prop_id"].startswith(
        "case-manage-insert-participants"
    ):
        output = attach_participants(case_id)

        return dmc.Stack(output)


@callback(
    Output("case-details-output", "children", allow_duplicate=True),
    Output("case-details-participants-selected-output", "children"),
    Input("case-details-id", "data"),
    Input("case-manage-participants", "value"),
    prevent_initial_call=True,
)
def update_participants(case_id, participants):

    participants_service = ParticipantsService()

    participants_all = participants_service.get_items()
    participants_selected = []
    if participants is not None:
        participants_selected = [
            dcc.Link(
                dmc.Button(
                    f"{p.role.capitalize()} - {p.first_name} {p.last_name}",
                    color="dark",
                    variant="light",
                    size="xs",
                    rightIcon=DashIconify(icon="carbon:view"),
                ),
                href=f"/manage/participants/{p.id}",
            )
            for p in participants_all
            if p.id in participants
        ]
    participants_selected = dmc.Group(participants_selected)

    if participants is None:
        return dash.no_update, participants_selected

    cases_service.patch_case(
        case_id=case_id, data={"participants": participants}
    )

    return (
        dmc.Alert(
            "Participants updated",
            color="green",
            variant="light",
            withCloseButton=True,
            duration=3000,
        ),
        participants_selected,
    )
