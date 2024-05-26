import json
import logging
import os

import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, callback

from src.core.config import get_settings
from src.models import templates
from src.services.templates import (
    get_single_template,
    get_templates,
    insert_template,
    patch_template,
)

logger = logging.getLogger(__name__)
settings = get_settings()


@callback(
    Output("template-selector", "data"),
    Input("url", "pathname"),
)
def get_templatess_list(url):
    print("get_templatess_list")

    templatess_all = get_templates()

    templatess_data = [
        {"label": f"{p.id} - {p.name}".replace("_", " "), "value": p.id}
        for p in templatess_all
    ]

    return templatess_data


@callback(
    Output("output-template", "children"),
    Input("template-selector", "value"),
    Input("edit-template-save", "n_clicks"),
    [
        State(f"{field}", "checked" if "bool" in str(field_info) else "value")
        for field, field_info in templates.Template.__annotations__.items()
        if field
        not in ["id", "creation_date", "update_date", "creator", "user"]
    ],
    prevent_initial_call=True,
)
def save_edit_template(templates_id, n_clicks, *inputs):
    ctx = dash.callback_context
    id = ctx.triggered_id
    if id == "edit-template-save":
        template_dict = dict(
            zip(
                [
                    field
                    for field in templates.Template.__annotations__.keys()
                    if field
                    not in [
                        "id",
                        "creation_date",
                        "update_date",
                        "creator",
                        "user",
                    ]
                ],
                inputs,
            )
        )
        if templates_id:
            patch_template(templates_id, **template_dict)
        else:
            insert_template(templates.Template(**template_dict))

        return dmc.Alert(
            "Template saved",
            color="green",
            duration=5000,
        )
    return dash.no_update


@callback(
    Output(
        "output-template-edit",
        "children",
    ),
    Input("template-selector", "value"),
)
def render_template(templates_id):
    if templates_id is not None:
        template = get_single_template(templates_id)
    else:
        template = templates.Template()  # noqa

    path_file = os.path.join(settings.CONFIG_PATH, "render.json")
    with open(path_file, "r") as f:
        data = json.load(f)

    grid = []
    for key, value in data.items():
        if value["type"] == "Switch":
            grid.append(
                dmc.GridCol(
                    dmc.Switch(
                        label=value["label"],
                        checked=getattr(template, key),
                        id=key,
                    ),
                    span=2,
                )
            )

        elif value["type"] == "Select":
            grid.append(
                dmc.GridCol(
                    dmc.Select(
                        label=value["label"],
                        data=value["data"],
                        value=getattr(template, key),
                        id=key,
                    ),
                    span=3,
                )
            )

        elif value["type"] == "Textarea":
            grid.append(
                dmc.GridCol(
                    dmc.Textarea(
                        label=value["label"],
                        value=getattr(template, key),
                        id=key,
                        style={"minWidth": 500},
                        autosize=True,
                        minRows=20,
                    ),
                    span=6,
                )
            )

        elif value["type"] == "JsonInput":
            grid.append(
                dmc.GridCol(
                    dmc.JsonInput(
                        label=value["label"],
                        value=getattr(template, key),
                        id=key,
                    ),
                    span=3,
                )
            )

        else:
            grid.append(
                dmc.GridCol(
                    dmc.TextInput(
                        label=value["label"],
                        placeholder=value["placeholder"],
                        value=getattr(template, key),
                        id=key,
                    ),
                    span=3,
                )
            )

    return dmc.Grid(children=grid, gutter="xl", my="md")
