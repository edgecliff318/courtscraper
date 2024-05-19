import logging

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

from src.components.cases.communications import get_case_communications
from src.components.cases.details import get_case_details
from src.components.cases.documents import get_case_documents
from src.components.cases.events import get_case_events
from src.components.cases.next_steps import get_next_step_modal
from src.components.cases.payments import get_case_payments
from src.components.cases.search import get_case_search
from src.components.cases.summary import get_case_summary
from src.components.cases.timeline import get_case_timeline
from src.components.cases.workflow.workflow import get_case_workflow
from src.services import cases

logger = logging.Logger(__name__)

dash.register_page(__name__, order=3, path_template="/manage/cases/<case_id>")




def layout(case_id):
    if case_id is None or case_id == "#" or case_id == "none":
        return dbc.Row(
            [
                dbc.Col(
                    dmc.Paper(
                        get_case_search(),
                        shadow="xs",
                        p="md",
                        radius="md",
                    ),
                    width=12,
                    class_name="mb-2",
                )
            ]
        )

    return html.Div(
        id="case-manage-details",
    )