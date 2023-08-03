import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html, page_registry


@callback(
    Output("navbar-menu", "children"),
    Input("loaded", "children"),
)
def generate_menu(navbar):
    menu_elements = {}
    for _, page in page_registry.items():
        if page.get("exclude", False):
            continue
        path_url = page.get("path")
        path_url_split = path_url.split("/")

        if len(path_url_split) >= 3:
            menu_elements.setdefault(
                path_url_split[1],
                {
                    "name": path_url_split[1],
                    "children": [],
                    "multi": True,
                    "label": path_url_split[1],
                },
            ).get("children").append(
                dbc.DropdownMenuItem(
                    html.Div(page.get("name")),
                    href=page.get("path"),
                )
            )
        else:
            menu_elements[path_url_split[1]] = {
                "name": path_url_split[1],
                "children": dbc.NavItem(
                    dbc.NavLink(
                        html.Span(
                            [
                                html.I(
                                    className=page.get(
                                        "class_icon", "ti ti-circle"
                                    )
                                ),
                                html.Span(page.get("name"), className="ms-1"),
                            ],
                            className="d-flex align-items-top",
                        ),
                        href=page.get("path"),
                        class_name="ms-3",
                    )
                ),
                "multi": False,
            }
    navbar = dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.NavbarBrand("Fubloo", className="ms-2")
                            ),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="https://app.fubloo.com",
                    style={"textDecoration": "none"},
                ),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                dbc.Collapse(
                    [
                        dbc.Nav(
                            [
                                dbc.DropdownMenu(
                                    nav=True,
                                    in_navbar=True,
                                    label=v.get("label").capitalize(),
                                    children=v.get("children"),
                                    class_name="text-primary ms-3",
                                )
                                if v.get("multi")
                                else v.get("children")
                                for k, v in menu_elements.items()
                            ],
                            class_name="",
                            navbar=True,
                        ),
                    ],
                    id="navbar-collapse",
                    is_open=False,
                    navbar=True,
                ),
            ]
        ),
        color="light",
        sticky=True,
    )

    return navbar


@callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("url", "pathname", allow_duplicate=True),
    [Input("logout-button", "n_clicks")],
    [State("url", "pathname")],
    prevent_initial_call=True,
)
def logout(n_clicks, href):
    if n_clicks:
        return "logout"
    return None
