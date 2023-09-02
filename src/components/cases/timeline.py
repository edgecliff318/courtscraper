import logging


import dash_mantine_components as dmc
from src.models.cases import Case

logger = logging.Logger(__name__)


def get_case_timeline(case: Case):
    events = case.events

    timeline = dmc.Timeline(
        active=1,
        bulletSize=15,
        lineWidth=2,
        children=[
            dmc.TimelineItem(
                title="Case Created & Paid",
            ),
            dmc.TimelineItem(
                title="EOA",
                children=[
                    dmc.Text(
                        [
                            "EOA submitted by ",
                            dmc.Anchor("Shawn Meyer", href="#", size="sm"),
                            " on ",
                            dmc.Anchor("2021-01-01", href="#", size="sm"),
                        ],
                        color="dimmed",
                        size="sm",
                    ),
                ],
            ),
            dmc.TimelineItem(
                title="RFR Pending",
                lineVariant="dashed",
                children=[
                    dmc.Text(
                        [
                            "RFR submitted by ",
                            dmc.Anchor(
                                "Shawn Meyer",
                                href="#",
                                size="sm",
                            ),
                            " on ",
                            dmc.Anchor("2021-01-01", href="#", size="sm"),
                        ],
                        color="dimmed",
                        size="sm",
                    ),
                ],
            ),
            dmc.TimelineItem(
                title="RFR Approved",
                children=[
                    dmc.Text(
                        ["RFR to be approved by the client &  the attorney"],
                    )
                ],
            ),
            dmc.TimelineItem(
                title="RFR Signed",
                children=[
                    dmc.Text(
                        [
                            "RFR to be signed by the client",
                        ]
                    )
                ],
            ),
            dmc.TimelineItem(
                title="RFR Paid by Client",
                children=[
                    dmc.Text(
                        [
                            "RFR Agreement paid by the client",
                        ]
                    )
                ],
            ),
            dmc.TimelineItem(
                title="Court Acceptance",
                children=[
                    dmc.Text(
                        [
                            "Court to accept the RFR proposal",
                        ]
                    )
                ],
            ),
            dmc.TimelineItem(
                title="Case Closed",
                children=[
                    dmc.Text(
                        [
                            "Case closed and archived",
                        ]
                    )
                ],
            ),
        ],
    )
    return timeline
