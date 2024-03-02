import logging

import dash
import dash_mantine_components as dmc
from dash import html


logger = logging.Logger(__name__)

dash.register_page(__name__, order=5, path_template="/manage/templates/<id>")


def layout(id):
    search_bar = dmc.Select(
        label="Templates",
        placeholder="Select templates",
        searchable=True,
        description="You can select the templates here.",
    )

    grid = dmc.Grid(
        children=[
            dmc.Col(html.Div("1"), span=3),
            dmc.Col(html.Div("2"), span=3),
            dmc.Col(html.Div("3"), span=3, offset=3),
        ],
        gutter="xl",
        my='md'
    )

    return dmc.Paper(
        children=[search_bar, grid],
        withBorder=True,
        p='lg'
    )
