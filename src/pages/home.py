import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html

dash.register_page(__name__, class_icon="ti ti-home", order=1, path="/")


def layout(data=None):
    return dmc.Card(
        dmc.CardSection(
            [
                html.H3("Welcome to Fubloo!", className="display-3"),
            ]
        )
    )
