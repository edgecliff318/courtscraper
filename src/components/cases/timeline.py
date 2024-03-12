import logging

import dash_mantine_components as dmc

from src.components.cases.status import case_statuses
from src.models.cases import Case

logger = logging.Logger(__name__)


def get_event_text(state: str, events: list):
    text = []
    for e in events:
        if e.get("case_status") == state:
            text.append(
                dmc.Text(
                    [
                        f"{case_statuses.get(state, {}).get('label')} submitted by ",
                        dmc.Anchor(e.get("email"), href="#", size="sm"),
                        " on ",
                        dmc.Anchor(e.get("date"), href="#", size="sm"),
                    ],
                    color="dimmed",
                    size="sm",
                )
            )

    return text


def get_case_timeline(case: Case):
    case_events = case.events or []

    case_events_timeline = [
        status_id
        for status_id, status_details in case_statuses.items()
        if status_details.get("mandatory", True)
        or status_id in [c.get("case_status") for c in case_events]
    ]
    active = 0
    for order, status_key in enumerate(case_events_timeline):
        if status_key == case.status:
            active = order

    timeline = dmc.Timeline(
        active=active,
        bulletSize=15,
        lineWidth=2,
        children=[
            dmc.TimelineItem(
                title=status_details.get("short_description"),
                children=(
                    get_event_text(status_id, case.events)
                    if case.events is not None
                    else []
                ),
            )
            for status_id, status_details in case_statuses.items()
            if status_details.get("mandatory", True)
            or status_id in [c.get("case_status") for c in case_events]
        ],
    )

    button = dmc.Button(
        "Update Status",
        variant="filled",
        color="dark",
        id="update-status-button",
        size="sm",
    )
    return dmc.Stack(
        [
            dmc.Text("Case Timeline", weight=600, size="lg"),
            button,
            timeline,
        ]
    )
