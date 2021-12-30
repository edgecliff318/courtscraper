import uuid

from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

import components

session_id = str(uuid.uuid4())

# the styles for the main content position it to the right of the sidebar and
# add some padding.

navbar = html.Nav(
    dbc.Container(
        [
            html.Div(
                [
                    html.Span(
                        [
                            "Welcome, ",
                            html.A("Shawn Anthony")
                        ]
                    )
                ],
                className="justify-content-right"
            )
        ],
        className="navbar-container d-flex content"
    ),
    className="header-navbar navbar navbar-expand-lg align-items-center "
              "floating-nav navbar-light navbar-shadow"
)

menu = html.Div(
    components.menu.sidebar,
    className="main-menu menu-fixed menu-light menu-accordion menu-shadow"
)

footer = html.Footer(
    html.P(
        ["COPYRIGHT © 2022 ",
         html.A("Ticket Washer", href="https://www.ticketwasher.com"),
         ". All rights reserved."]),
    className="footer footer-light"
)

content = html.Div(
    [
        html.Div(
            html.Div(id="page-content"),
            className="content-wrapper"
        ),
        footer
    ],
    className="app-content content"
)

layout = html.Div(
    [dcc.Location(id="url"), navbar, menu, content],
    className="vertical-layout vertical-menu-modern navbar-floating"
)
