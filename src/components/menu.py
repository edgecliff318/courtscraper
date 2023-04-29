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
"""
<a class="d-flex align-items-center" href="ui-typography.html">
<span class="menu-title text-truncate" data-i18n="Typography">
Typography</span>
</a>

"""
a_class = "d-flex align-items-center"
sidebar = html.Div(
    [
        dbc.NavbarBrand(
            html.H3(
                [
                    html.Span("Ticket", className="font-weight-bold"),
                    "Washer.",
                    html.Span("com", style={"color": "#F8795D"})
                ],
                className="brand-text"
            )
        ),
        dbc.Nav(
            [
                dbc.NavLink("Welcome", href="/", active="exact",
                            className="justify-content-start"),
                dbc.NavLink("Leads", href="/leads",
                            active="exact",
                            className="justify-content-start"),
                dbc.NavLink("Stats", href="/stats",
                            active="exact",
                            className="justify-content-start"),
                dbc.NavLink("Process", href="/process",
                            active="exact",
                            className="justify-content-start"),
                dbc.NavLink("History",
                            href="/history",
                            active="exact",
                            className="justify-content-start"
                            )
            ],
            vertical=True,
            pills=True,
            className="flex-column"
        ),
        html.Hr()
    ],
    style=SIDEBAR_STYLE,
    className="main-menu menu-fixed menu-light menu-accordion menu-shadow "
              "expanded"
)
span_class = "menu-title text-truncate"
