import dash_bootstrap_components as dbc
from dash import dcc


def generate_form_group(
    label, id, placeholder, type="Input", options=None, value=None, **kwargs
):
    if type == "Input":
        field = dbc.Input(
            id=id, placeholder=placeholder, value=value, **kwargs
        )
    elif type == "Textarea":
        field = dbc.Textarea(
            id=id, placeholder=placeholder, value=value, **kwargs
        )

    elif type == "Select":
        field = dbc.Select(id=id, options=options, value=value, **kwargs)
    elif type == "Dropdown":
        field = dcc.Dropdown(id=id, options=options, value=value, **kwargs)
    elif type == "DatePickerSingle":
        field = dcc.DatePickerSingle(id=id, **kwargs)
    elif type == "DateRangePicker":
        field = dcc.DatePickerRange(id=id, **kwargs)
    else:
        field = ""

    return field
