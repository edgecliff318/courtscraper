import logging

import dash
import dash_mantine_components as dmc
from dash import html


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
    from src.models import templates
    from dash_mantine_components import Col, TextInput, Switch
    fields = []

    # for key, field_info in templates.Template.__annotations__.items():
    #     if key not in ["id", "creation_date", "update_date"]:
    #         if field_info == bool:
    #             fields.append(Col(Switch(
    #                 label=f"{key.capitalize().replace('_', ' ')}",
    #                 checked=False,
    #                 id=key,
    #             ), span=3))
    #         else:
    #             fields.append(Col(TextInput(
    #                 label=f"{key.capitalize().replace('_', ' ')}",
    #                 placeholder=f"{key.capitalize().replace('_', ' ')}",
    #                 value="",
    #                 id=key,
    #             ), span=3))
    
    # bool_fields = ["enabled", "repeat", "sms"]
    # select_fields = ["type", "state" ]
    # text_area_fields = ["text"]
    # text_fields = ["name", "subject","category", "filepath", "user", "trigger", "next_case_status", "sms_message"]
    
    # for key, _ in templates.Template.__annotations__.items():
    #     if key not in ["id", "creation_date", "update_date"]:
    #         if key in bool_fields:
    #             fields.append(Col(Switch(
    #                 label=f"{key.capitalize().replace('_', ' ')}",
    #                 checked=False,
    #                 id=key,
    #             ), span=2))
    #         elif key in select_fields:
    #             fields.append(Col(dmc.Select(
    #                 label=f"{key.capitalize().replace('_', ' ')}",
    #                 placeholder=f"{key.capitalize().replace('_', ' ')}",
    #                 id=key,
    #             ), span=3))
    #         elif key in text_fields:
    #             fields.append(Col(TextInput(
    #                 label=f"{key.capitalize().replace('_', ' ')}",
    #                 placeholder=f"{key.capitalize().replace('_', ' ')}",
    #                 value="",
    #                 id=key,
    #             ), span=3))
    #         elif key in text_area_fields:
    #             fields.append(Col(dmc.Textarea(
    #                 label=f"{key.capitalize().replace('_', ' ')}",
    #                 placeholder=f"{key.capitalize().replace('_', ' ')}",
    #                 value="",
    #                 id=key,
    #             ), span=3))
    #         else:
    #             fields.append(Col(TextInput(
    #                 label=f"{key.capitalize().replace('_', ' ')}",
    #                 placeholder=f"{key.capitalize().replace('_', ' ')}",
    #                 value="",
    #                 id=key,
    #             ), span=3))
    
    
    config = {
        "enabled":{
            "label": "Enabled",
            "type": "Switch",
            "checked": False,
        },
          "repeat":{
            "label": "Repeat",
            "type": "Switch",
            "checked": False,
        },
        "sms":{
            "label": "Sms",
            "type": "Switch",
            "checked": False,
        },
        "name":{
            "label": "Name",
            "type": "TextInput",
            "placeholder": "Name",
            "value": "",
        },
        "category":{
            "label": "Category",
            "type": "TextInput",
            "placeholder": "Category",
            "value": "",
        },
        
        "type":{
            "label": "Type",
            "type": "Select",
            "placeholder": "Type",
            "value": "file",
            "data": [
                {"label": "File", "value": "file"},
                {"label": "Html", "value": "html"},
                {"label": "Text", "value": "text"},
                {"label": "Form", "value": "form"},
            ],
        },
        "creator":{
            "label": "Creator",
            "type": "TextInput",
            "placeholder": "Creator",
            "value": "",
        },
        "subject":{
            "label": "Subject",
            "type": "TextInput",
            "placeholder": "Subject",
            "value": "",
        },
       
        "filepath":{
            "label": "File path",
            "type": "TextInput",
            "placeholder": "Filepath",
            "value": "",
        },
        
       
        "state":{
            "label": "State",
            "type": "Select",
            "placeholder": "State",
            "value": "",
            "data": [
                {"label": "Draft", "value": "draft"},
                {"label": "Active", "value": "active"},
                {"label": "Inactive", "value": "inactive"},
            ],
        },
        "user":{
            "label": "User",
            "type": "TextInput",
            "placeholder": "User",
            "value": "",
        },
        "trigger":{
            "label": "Trigger",
            "type": "TextInput",
            "placeholder": "Trigger",
            "value": "",
        },
        
      
        "sms_message":{
            "label": "Sms message",
            "type": "TextInput",
            "placeholder": "Sms message",
            "value": "",
        },
        "next_case_status":{
            "label": "Next case status",
            "type": "TextInput",
            "placeholder": "Next case status",
            "value": "",
        },
         "parameters":{
            "label": "Parameters",
            "type": "JsonInput",
            "placeholder": "Parameters",
            "value": "",
            "validationError": "Invalid json",
            "formatOnBlur": True,
            "autosize": True,
            "minRows": 4,
        },
         "text":{
            "label": "Text",
            "type": "Textarea",
            "placeholder": "Text",
            "value": "",
         
        },
         
    }

    for key, value in config.items():
        if value["type"] == "Switch":
            fields.append(Col(Switch(
                label=value["label"],
                checked=value["checked"],
                id=key,
            ), span=2))
        elif value["type"] == "Select":
            fields.append(Col(dmc.Select(
                label=value["label"],
                placeholder=value["placeholder"],
                id=key,
                data=value["data"],
            ), span=3))
        elif value["type"] == "Textarea":
            fields.append(Col(dmc.Textarea(
                label=value["label"],
                placeholder=value["placeholder"],
                value=value["value"],
                id=key,
            ), span=3))
        elif value["type"] == "JsonInput":
            fields.append(Col(dmc.JsonInput(
                label=value["label"],
                placeholder=value["placeholder"],
                value=value["value"],
                id=key,
                validationError=value["validationError"],
                formatOnBlur=value["formatOnBlur"],
                autosize=value["autosize"],
                minRows=value["minRows"],
            ), span=3))
        else:
            fields.append(Col(TextInput(
                label=value["label"],
                placeholder=value["placeholder"],
                value=value["value"],
                id=key,
            ), span=8))
    
    from dash_iconify import DashIconify

    
    btn = dmc.Group(
    [
        dmc.Button("Save", color="dark", id="edit-template-save", leftIcon=DashIconify(icon="material-symbols:save")),
        dmc.Button("Cancel", color="red", variant="subtle"),
html.Div(id="output-template"),
      
    ]
    , position="right"
)

    grid = dmc.Grid(
        children=fields,
        gutter="xl",
        my='md'
    )

    return [
        
        dmc.Paper(
        children=[search_bar],
        withBorder=True,
        p='lg'
    ),
            dmc.Paper(
        children=[btn,grid,
                  
                  
                  html.Div(id="output-template-test")
                  ],
        withBorder=True,
        p='lg',
        mt='lg'
    )
            
    ]
