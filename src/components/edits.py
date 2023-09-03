import logging

import dash_mantine_components as dmc
from src.components.inputs import generate_form_group
from dash_iconify import DashIconify
from dash import html, dcc

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
            dmc.Col(
                dmc.Stack(
                    [
                        field
                        for i, field in enumerate(fields_form)
                        if i < len(fields_form) / 2
                    ]
                ),
                md=6,
                span=12,
            ),
            dmc.Col(
                dmc.Stack(
                    [
                        field
                        for i, field in enumerate(fields_form)
                        if i >= len(fields_form) / 2
                    ]
                ),
                md=6,
                span=12,
            ),
        ]
    )

    output = [
        dmc.Group(
            [
                dmc.Button(
                    "Save",
                    color="indigo",
                    id="edit-component-save",
                    leftIcon=DashIconify(icon="material-symbols:save"),
                ),
                dmc.Button(
                    "Reset",
                    color="indigo",
                    id="edit-component-reset",
                    leftIcon=DashIconify(icon="material-symbols:reset"),
                ),
                dmc.Button(
                    "New",
                    color="indigo",
                    id="edit-component-new",
                    leftIcon=DashIconify(icon="carbon:reset"),
                    style={"display": "none" if new else "block"},
                ),
            ],
            position="right",
        ),
        html.Div(id="edit-component-output"),
        dmc.Divider(),
        dcc.Store(id="edit-component-collection", data=collection),
        dcc.Store(id="edit-component-item-id", data=item_id),
        fields_columns,
    ]

    return dmc.Stack(output, className="mt-2")
