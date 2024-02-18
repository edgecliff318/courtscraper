import datetime

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc


def generate_form_group(
    id, placeholder, type="Input", options=None, value=None, **kwargs
):
    if type == "Input":
        field = dmc.TextInput(
            id=id, placeholder=placeholder, value=value, **kwargs
        )

    elif type == "Select":
        field = dmc.Select(id=id, data=options, value=value, **kwargs)
    elif type == "Dropdown":
        if kwargs.get("multi"):
            kwargs.pop("multi")
            field = dmc.MultiSelect(id=id, data=options, value=value, **kwargs)
        else:
            field = dmc.Select(id=id, data=options, value=value, **kwargs)

    elif type == "DateRangePicker":
        if kwargs.get("end_date") is None:
            kwargs["end_date"] = datetime.date.today()
        if kwargs.get("start_date") is None:
            kwargs["start_date"] = kwargs["end_date"] - datetime.timedelta(
                days=7
            )
        kwargs["value"] = [kwargs["start_date"], kwargs["end_date"]]
        kwargs.pop("start_date")
        kwargs.pop("end_date")
        field = dmc.DateRangePicker(id=id, inputFormat="DD/MM/YYYY", **kwargs)
    elif type == "DatePickerSingle":
        kwargs["value"] = kwargs.get("date", datetime.date.today())
        kwargs.pop("date")
        field = dmc.DatePicker(id=id, inputFormat="DD/MM/YYYY", **kwargs)
    elif type == "RadioItems":
        field = dcc.RadioItems(id=id, options=options, value=value, **kwargs)
    elif type == "Button":
        field = dbc.Button(id=id, children=placeholder, **kwargs)
    elif type == "Textarea":
        field = dmc.Textarea(
            id=id, placeholder=placeholder, value=value, **kwargs
        )
    else:
        field = ""

    return field
