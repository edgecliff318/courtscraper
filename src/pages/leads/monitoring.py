import logging

import dash
import dash_bootstrap_components as dbc
from dash import html
import dash_mantine_components as dmc

from src.components.filters import monitoring_controls
from src.components.conversation import conversation_model
from src.components.conversation import many_response_model

from dash import dcc, html

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti ti-phone", order=3)


def layout():
    
    
    summary_card = html.Div(
        dmc.Skeleton(
            visible=False,
            children=html.Div(id="messages-summary"),
        )
    )
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    monitoring_controls,
                                    html.Div(id="monitoring-status"),
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                                                            summary_card
,
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            
            
            
            html.Div(
                     id="message-monitoring",
                     ),
            
             html.Div(
                     id="leads-data",
                     ),
            
            
            
             html.Div([
                         conversation_model(),
                         many_response_model("monitoring"),
                        dcc.Store(id="monitoring-data", storage_type="memory"),
             ]

                     ),
            
            # dbc.Row(
            #     [
            #         dbc.Col(
            #             dbc.Card(
            #                 dbc.CardBody(
            #                     [
            #                         html.Div(
            #                             [
            #                                 dmc.Skeleton(
            #                                     visible=False,
            #                                     children=html.Div(
            #                                         id="graph-container-status-sms",
            #                                     ),
            #                                     mb=10,
            #                                 ),
            #                             ]
            #                         )
            #                     ]
            #                 ),
            #             ),
            #             width=12,
            #             className="mb-2",
            #         ),
            #     ]
            # ),
            # most recent error
            # dbc.Row(
            #     [
            #         dbc.Col(
            #             dbc.Card(
            #                 dbc.CardBody(
            #                     [
            #                         html.Div(
            #                             [
            #                                 dmc.Skeleton(
            #                                     visible=False,
            #                                     children=html.Div(
            #                                         id="graph-container-most-recent-error",
            #                                     ),
            #                                     mb=10,
            #                                 ),
            #                             ]
            #                         )
            #                     ]
            #                 ),
            #             ),
            #             width=12,
            #             className="mb-2",
            #         ),
            #     ]
            # ),
        ]
    )
