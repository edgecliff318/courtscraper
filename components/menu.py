import dash_bootstrap_components as dbc
from dash import html

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H2("Ticket Flusher"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Welcome", href="/", active="exact"),
                dbc.NavLink("Process", href="/process",
                            active="exact"),
                dbc.NavLink("History",
                            href="/history",
                            active="exact")
            ],
            vertical=True,
            pills=True,
        )
    ],
    style=SIDEBAR_STYLE,
)
