import logging


import dash
import dash_mantine_components as dmc
from dash import Input, Output, callback, dcc


import src.services.cases as cases_service
from src.core.config import get_settings
import src.models as models
from src.services.participants import ParticipantsService

logger = logging.getLogger(__name__)
settings = get_settings()


@callback(
    Output("case-details-output", "children", allow_duplicate=True),
    Input("case-manage-refresh", "n_clicks"),
    Input("case-manage-insert-participants", "n_clicks"),
    Input("case-details-id", "data"),
    prevent_initial_call=True,
)
def edit_component(refresh, insert, case_id):
    ctx = dash.callback_context

    participants_service = ParticipantsService()

    if not ctx.triggered:
        return dash.no_update

    if ctx.triggered[0]["prop_id"].startswith("case-manage-refresh"):
        # Refresh from casenet
        message = dmc.Alert(
            "Case Refreshed from CaseNet",
            color="green",
            variant="filled",
        )
        return message

    if ctx.triggered[0]["prop_id"].startswith(
        "case-manage-insert-participants"
    ):
        case = cases_service.get_single_case(case_id)

        participants = case.parties
        if participants is None:
            return dmc.Alert(
                "No participants found", color="red", variant="filled"
            )

        output = []

        participants_ids = case.participants

        if participants_ids is None:
            participants_ids = []

        for participant_single in participants:
            mapping = {
                "desc": "role",
                "addr_city": "city",
                "addr_line1": "address",
                "addr_statcode": "state",
                "addr_zip": "zip_code",
                "birth_date": "date_of_birth",
                "formatted_telephone": "phone",
            }

            role_mapping = {
                "DFT": "defendant",
                "PA": "prosecutor",
            }

            participant_single = {
                mapping.get(k, k): v for k, v in participant_single.items()
            }

            participant_single["role"] = role_mapping.get(
                participant_single["desc_code"], "other"
            )

            participant_instance = models.Participant(**participant_single)

            # Check if another participan instance exists
            participant_exists = participants_service.get_items(
                first_name=participant_instance.first_name,
                last_name=participant_instance.last_name,
                date_of_birth=participant_instance.date_of_birth,
            )

            if len(participant_exists) > 0:
                links = []
                for participant_db in participant_exists:
                    output_message = dcc.Link(
                        f"{participant_db.first_name} {participant_db.last_name} - {participant_db.role}",
                        href=f"/manage/participants/{participant_db.id} \n",
                    )

                    links += [output_message]

                output += [
                    dmc.Alert(
                        [
                            "Participant already exists: ",
                        ]
                        + links,
                        color="red",
                        variant="filled",
                        withCloseButton=True,
                    )
                ]

                continue

            participant_created = participants_service.create_item(
                participant_instance
            )

            item_link = dcc.Link(
                "Click here to edit participant",
                href=f"/manage/participants/{participant_created.id}",
            )

            participants_ids.append(participant_created.id)

            output_message = dmc.Alert(
                [
                    (
                        "New Participant created, "
                        "you can update it in this screen: "
                    ),
                    item_link,
                ],
                color="green",
                title=f"{participant_instance.first_name} {participant_instance.last_name} added to the DB",
                variant="light",
                withCloseButton=True,
            )

            output.append(output_message)

        cases_service.patch_case(
            case_id=case_id, data={"participants": participants_ids}
        )

        return dmc.Stack(output)


@callback(
    Output("case-details-output", "children", allow_duplicate=True),
    Input("case-details-id", "data"),
    Input("case-manage-participants", "value"),
    prevent_initial_call=True,
)
def update_participants(case_id, participants):
    if participants is None:
        return dash.no_update

    cases_service.patch_case(
        case_id=case_id, data={"participants": participants}
    )

    return dmc.Alert(
        "Participants updated",
        color="green",
        variant="light",
        withCloseButton=True,
        duration=3000,
    )
