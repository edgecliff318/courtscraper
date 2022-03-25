import base64
import os
import dash_bootstrap_components as dbc
from dash import html, dcc
import dash_design_kit as ddk

import config


def generate_form_group(label, id, placeholder, type="Input", options=None,
                        value=None, **kwargs):
    if type == "Input":
        field = dbc.Input(
            id=id,
            placeholder=placeholder,
            value=value,
            **kwargs
        )

    elif type == "Select":
        field = dbc.Select(
            id=id,
            options=options,
            value=value
            ** kwargs
        )
    elif type == "Dropdown":
        field = dcc.Dropdown(
            id=id,
            options=options,
            value=value,
            **kwargs
        )
    else:
        field = ""

    return ddk.ControlItem(
        field, label=label,
        label_style={"font-weight": "700"},
        label_position="left",
        className="mb-2"
    )


def page(data: dict = None, filemanager=True):
    if filemanager:
        file_manager_card = dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H5("Upload")
                        ),
                        dbc.CardBody(
                            [
                                dcc.Upload(
                                    id="upload-data",
                                    children=html.Div(
                                        [
                                            "Drag and drop or click to "
                                            "select a "
                                            "file "
                                            "to "
                                            "upload."]
                                    ),
                                    style={
                                        "width": "100%",
                                        "height": "60px",
                                        "lineHeight": "60px",
                                        "borderWidth": "1px",
                                        "borderStyle": "dashed",
                                        "borderRadius": "5px",
                                        "textAlign": "center",
                                        "margin": "10px",
                                    },
                                    multiple=True,
                                ),
                                html.H6("Files Detected"),
                                html.Ul(id="file-list"),
                            ]
                        )
                    ]
                )
            ),
            className="mb-2"
        )
    else:
        file_manager_card = None
    message_default = "Enter a value ..."

    buttons = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Button(
                        "Save",
                        id='ticket-save',
                        className="m-1"
                    ),
                    dbc.Button(
                        "Generate",
                        id="ticket-generate",
                        className="m-1"
                    ),
                    dbc.Button(
                        "Export",
                        id='ticket-export',
                        className="m-1",
                    )
                ],
                width=12,
            )
        ],
        justify="between"
    )

    form_card = html.Div(
        [
            ddk.ControlCard(
                [
                    html.Div(
                        [
                            generate_form_group(
                                label=e.get('field-label'),
                                id={
                                    'type': 'parser',
                                    'index': f"parser-{e.get('field-id')}"
                                },
                                placeholder=message_default,
                                value=e.get('field-value')
                            ) for e in data.get('form', [])
                        ]
                    ),

                ],
                orientation='horizontal',
                label_position='left',
                control_position='right'
            ),
            buttons,
            html.Div(id="results-save"),
            html.Div(id="results-generate"),
        ]
    )

    image_filename = config.data_path.joinpath(
        data.get("image").name)  # replace with your own image
    if image_filename is not None:
        encoded_image = base64.b64encode(
            open(image_filename,
                 'rb').read())
        image = html.Img(src='data:image/png;base64,{}'.format(
            encoded_image.decode()),
            width="100%"
        )
    else:
        image = "No scan selected"

    parser_card = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H5(
                                "Form"
                            )
                        ),
                        dbc.CardBody(
                            form_card
                        )
                    ]
                )
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H5(
                                "Scan"
                            )
                        ),
                        dbc.CardBody(
                            image
                        )
                    ]
                )
            )
        ]
    )

    results = []

    if file_manager_card is not None:
        results.append(
            dbc.Col(
                file_manager_card, width=12
            )
        )
    results.append(
        dbc.Col(
            parser_card, width=12
        )
    )

    return results
