import logging

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from dash import dcc, html
from src.components.filters import cases_controls


logger = logging.Logger(__name__)

dash.register_page(__name__, order=3, path_template="/manage/actions")



def layout():
    return dbc.Container([
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    cases_controls,
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
        ###
        html.Div(
            id="actions-data"
        ),
            
    dmc.Grid(
        children=[
            dmc.Col(
        dmc.Navbar(
            p="md",
            children=[
                html.H4("Pending", style={"marginTop": '4px', "textAlign": 'center'}),
                dmc.Divider(size="sm", style={"marginBottom": "10px"}),
                html.Div(  
                         id="case_card_col_1",
                    # [create_case_card(case) for case in cases],
                    style={
                        "overflowY": "auto"
                    }
                )
            ],
        ),
        xl=4, lg=4, md=12, sm=12, xs=12
    ),
            dmc.Col(
        dmc.Navbar(
            p="md",
            children=[
                html.H4( "To-do", style={"marginTop": '4px', "textAlign": 'center'}),
                dmc.Divider(size="sm", style={"marginBottom": "10px"}),
                html.Div(  
                    # [create_case_card(case) for case in cases],
                         id="case_card_col_2",
                    
                    style={
                        "overflowY": "auto"
                    }
                )
            ],
        ),
        xl=4, lg=4, md=12, sm=12, xs=12
    ),
            dmc.Col(
        dmc.Navbar(
            p="md",
            children=[
                html.H4("Closed Recently", style={"marginTop": '4px', "textAlign": 'center'}),
                dmc.Divider(size="sm", style={"marginBottom": "10px"}),
                html.Div(  
                    # [create_case_card(case) for case in cases],
                         id="case_card_col_3",
                    
                    style={
                        "overflowY": "auto"
                    }
                )
            ],
        ),
        xl=4, lg=4, md=12, sm=12, xs=12
    )
        ],
        justify="center",
        align="flex-start",
        gutter="xl",
    )
], style={"padding": "20px"})
    