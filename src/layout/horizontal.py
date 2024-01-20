from datetime import datetime

import dash
import dash.html as html
import dash_bootstrap_components as dbc
from dash import dcc


class Layout:
    def __init__(self):
        pass

    def build_menu(self):
        navbar = dbc.Navbar(
            dbc.Container(
                [
                    html.A(
                        # Use row and col to control vertical alignment of logo / brand
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.NavbarBrand("App", className="ms-2")
                                ),
                            ],
                            align="center",
                            className="g-0",
                        ),
                        href="https://plotly.com",
                        style={"textDecoration": "none"},
                    ),
                    dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                    dbc.Collapse(
                        html.Div(
                            id="navbar-menu",
                        ),
                        id="navbar-collapse",
                        is_open=False,
                        navbar=True,
                    ),
                ]
            )
        )
        return navbar

    def build_footer(self):
        footer_container = html.Div(
            [
                html.Div(
                    [
                        f"© {datetime.now().year} Made with ❤️ by ",
                        html.A(
                            "Fubloo",
                            href="https://app.fubloo.com",
                            target="_blank",
                            className="fw-semibold",
                        ),
                    ],
                    className="",
                ),
                html.Div(
                    html.A(
                        "Terms & Conditions",
                        href="https://app.fubloo.com/terms",
                        target="_blank",
                        className="footer-link me-4",
                    ),
                    className="",
                ),
            ],
            className="footer-container d-flex align-items-center justify-content-between py-2 flex-md-row flex-column",
        )
        footer = html.Footer(
            html.Div(footer_container, className="container-xxl"),
            className="content-footer footer bg-footer-theme",
            id="loaded",
        )
        return footer

    def render(self):
        content = html.Div(
            dash.page_container,
            className="container-xxl flex-grow-1 container-p-y",
            id="content",
        )
        content_backdrop = html.Div(className="content-backdrop fade")
        content_wrapper = html.Div(
            [
                dcc.Location(id="url", refresh="callback-nav"),
                dcc.Store(id="invoice-data-refresh"),
                dcc.Store(id="modal-next-step-trigger"),
                html.Div(id="navbar-menu"),
                content,
                self.build_footer(),
                content_backdrop,
            ],
            className="content-wrapper",
        )
        layout_page = html.Div(
            content_wrapper,
            className="layout-page",
        )

        layout_container = html.Div(
            [
                layout_page,
            ],
            className="layout-container",
        )
        layout = html.Div(
            layout_container,
            className="layout-wrapper layout-navbar-full layout-horizontal layout-without-menu",
        )
        return layout
