import logging
import json
import os

import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, callback

from src.core.config import get_settings
from src.models import templates
from src.services.templates import get_single_template, get_templates

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


# # Callback for multiplage redirection when selecting the templates value
# @callback(
#     Output("url", "pathname", allow_duplicate=True),
#     Input("templatess-list", "value"),
#     prevent_initial_call=True,
# )
# def goto_templates(templates_id):
#     if templates_id is None:
#         return dash.no_update
#     return f"/manage/templatess/{templates_id}"


# @callback(
#     Output("template-selector", "data"),
#     Input("url", "pathname"),
# )
# def save_edit_template(url):
#     print("save_edit_template")
#     return dash.no_update

# @callback(
#     Output(
#         "output-template",
#         "children",
#     ),
#     Input(
#         "edit-template-save",
#         "n_clicks",
#     ),
#         [State(f'{field}', 'value') for field in templates.Template.__annotations__.keys() if field not in ["id", "creation_date", "update_date"]],

#     prevent_initial_call=True,
# )
# def save_edit_template(n_clicks ,*inputs):

#     print(inputs)
#     return "hello world"


@callback(
    Output("output-template", "children"),
    Input("edit-template-save", "n_clicks"),
    [
        State(f"{field}", "checked" if "bool" in str(field_info) else "value")
        for field, field_info in templates.Template.__annotations__.items()
        if field not in ["id", "creation_date", "update_date"]
    ],
    prevent_initial_call=True,
)
def save_edit_template(n_clicks, *inputs):
    # ctx = callback_context
    # if not ctx.triggered:
    #     # No field has been edited yet
    #     return "No field edited"
    # else:
    #     # Get the ID of the edited field
    #     field_id = ctx.triggered[0]['prop_id'].split('.')[0]
    #     print(f"Edited field ID: {field_id}")
    # return f"Edited field ID: {field_id}"
    ctx = dash.callback_context
    id = ctx.triggered[0]["prop_id"].split(".")[0]
    if id == "edit-template-save":
        print(inputs)
        template_dict = dict(
            zip(
                [
                    field
                    for field in templates.Template.__annotations__.keys()
                    if field not in ["id", "creation_date", "update_date"]
                ],
                inputs,
            )
        )
        print(template_dict)
        return "hello world"
    return dash.no_update


# # Callback for multiplage redirection when selecting the templates value
@callback(
    Output(
        "output-template-test",
        "children",
    ),
    Input("template-selector", "value"),
    # prevent_initial_call=True,
)
def render_template(templates_id):
    if templates_id is not None:
        template = get_single_template(templates_id)
    else:
        template = templates.Template() # noqa

        path_file = os.path.join(settings.CONFIG_PATH, "render.json")
        with open(path_file, "r") as f:
            data = json.load(f)

        grid = []
    for key, value in data.items():
        if value["type"] == "Switch":
            grid.append(
                dmc.Col(
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
                dmc.Col(
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
                dmc.Col(
                    dmc.Textarea(
                        label=value["label"],
                        value=getattr(template, key),
                        id=key,
                    ),
                    span=12,
                )
            )

        elif value["type"] == "JsonInput":
            grid.append(
                dmc.Col(
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
                dmc.Col(
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
