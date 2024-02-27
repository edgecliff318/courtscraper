import logging

import dash_mantine_components as dmc
from dash import dcc, html

from src.core.config import get_settings
from src.models.cases import Case

logger = logging.getLogger(__name__)
settings = get_settings()


def get_case_communications(case: Case):
    participant_select = dmc.Select(
        id="communication-participant-select",
        label="Select a participant",
        description="Select a participant to view their communications",
        data=[],
        value=None,
    )
    communication_details = html.Div(id="communication-details")
    prefix = "communication"
    return dmc.Stack(
        [
            dcc.Store(id=f"communication-memory", storage_type="memory"),
            participant_select,
            communication_details,
            html.Div(id=f"{prefix}-modal-content-sending-status"),
        ],
        mt="xs",
    )
