import logging

import dash_mantine_components as dmc
from dash_iconify import DashIconify

from src.components.cases.workflow.client import get_client_section
from src.components.cases.workflow.court import get_court_section
from src.components.cases.workflow.prosecutor import get_prosecutor_section

logger = logging.Logger(__name__)


def get_case_workflow(case):
    if case.participants is None or len(case.participants) == 0:
        return dmc.Alert(
            "No participants found ! Please add the participants to the case",
            color="blue",
            title="No participants found",
            mt="xs",
        )
    return dmc.Accordion(
        children=[
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        "Work with the Court",
                        icon=DashIconify(
                            icon="tabler:gavel",
                            color="dark",
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
                            color="dark",
                            width=20,
                        ),
                    ),
                    dmc.AccordionPanel(
                        get_prosecutor_section(case),
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
                            color="dark",
                            width=20,
                        ),
                    ),
                    dmc.AccordionPanel(
                        get_client_section(case),
                    ),
                ],
                value="client",
            ),
        ],
    )
