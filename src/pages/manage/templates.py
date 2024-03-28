import logging

import dash
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

logger = logging.Logger(__name__)

dash.register_page(__name__, order=5, path_template="/manage/templates")


def layout():
    search_bar = dmc.Select(
        label="Templates",
        placeholder="Select templates",
        searchable=True,
        description="You can select the templates here.",
        id="template-selector",
    )

    btn = dmc.Group(
        [
            html.Div(id="output-template"),
            dmc.Button(
                "Save",
                color="dark",
                id="edit-template-save",
                leftIcon=DashIconify(icon="material-symbols:save"),
            ),
            dmc.Button("Cancel", color="red", variant="subtle"),
        ],
        position="right",
    )

    return [
        dmc.Paper(children=[search_bar], withBorder=True, p="lg"),
        dmc.Paper(
            children=[btn, html.Div(id="output-template-edit")],
            withBorder=True,
            p="lg",
            mt="lg",
        ),
    ]
