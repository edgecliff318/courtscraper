import logging

import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify

from src.components.inputs import generate_form_group

logger = logging.Logger(__name__)


def render_edit_component(fields, collection, item_id, new=True):
    # Update the id in fields
    for field in fields:
        field["label"] = field["id"].capitalize().replace("_", " ")
        field["placeholder"] = field["id"].capitalize().replace("_", " ")
        field["id"] = {
            "index": field["id"],
            "type": "edit-component-fields",
        }

    fields_form = [generate_form_group(**field) for field in fields]

    fields_columns = dmc.Grid(
        [
            dmc.GridCol(
                dmc.Stack(
                    [
                        field
                        for i, field in enumerate(fields_form)
                        if i < len(fields_form) / 2
                    ]
                ),
                span={"base": 12, "md": 6},
            ),
            dmc.GridCol(
                dmc.Stack(
                    [
                        field
                        for i, field in enumerate(fields_form)
                        if i >= len(fields_form) / 2
                    ]
                ),
                span={"base": 12, "md": 6},
            ),
        ]
    )

    output = [
        dmc.Group(
            [
                dmc.Button(
                    "Save",
                    color="dark",
                    id="edit-component-save",
                    leftSection=DashIconify(icon="material-symbols:save"),
                ),
                dmc.Button(
                    "Reset",
                    color="dark",
                    id="edit-component-reset",
                    leftSection=DashIconify(icon="material-symbols:reset"),
                ),
                dmc.Button(
                    "New",
                    color="dark",
                    id="edit-component-new",
                    leftSection=DashIconify(icon="carbon:reset"),
                    style={"display": "none" if new else "block"},
                ),
            ],
            justify="right",
        ),
        html.Div(id="edit-component-output"),
        dmc.Divider(),
        dcc.Store(id="edit-component-collection", data=collection),
        dcc.Store(id="edit-component-item-id", data=item_id),
        fields_columns,
    ]

    return dmc.Stack(output, className="mt-2")
