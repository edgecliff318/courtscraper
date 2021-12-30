import dash_bootstrap_components as dbc
import dash_design_kit as ddk
from dash import dcc


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
            value=value,
            **kwargs
        )
    elif type == "Dropdown":
        field = dcc.Dropdown(
            id=id,
            options=options,
            value=value,
            **kwargs
        )
    elif type == "DatePickerSingle":
        field = dcc.DatePickerSingle(
            id=id,
            **kwargs
        )
    else:
        field = ""

    return field
