import logging

import dash_mantine_components as dmc
from dash_iconify import DashIconify
from src.components.cases.workflow.client import get_client_section

from src.components.cases.workflow.court import get_court_section
from src.components.cases.workflow.prosecutor import get_prosecutor_section

logger = logging.Logger(__name__)


def get_case_workflow():
    return dmc.Accordion(
        children=[
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        "Work with the Court",
                        icon=DashIconify(
                            icon="tabler:gavel",
                            color=dmc.theme.DEFAULT_COLORS["blue"][6],
                            width=20,
                        ),
                    ),
                    dmc.AccordionPanel(get_court_section()),
                ],
                value="court",
            ),
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        "Work with the Prosecutor",
                        icon=DashIconify(
                            icon="tabler:analyze",
                            color=dmc.theme.DEFAULT_COLORS["blue"][6],
                            width=20,
                        ),
                    ),
                    dmc.AccordionPanel(
                        get_prosecutor_section(),
                    ),
                ],
                value="prosecutor",
            ),
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        "Work with the Client",
                        icon=DashIconify(
                            icon="tabler:user",
                            color=dmc.theme.DEFAULT_COLORS["blue"][6],
                            width=20,
                        ),
                    ),
                    dmc.AccordionPanel(
                        get_client_section(),
                    ),
                ],
                value="client",
            ),
        ],
    )
