import datetime
import logging

import dash_ag_grid as dag
import dash_mantine_components as dmc

logger = logging.Logger(__name__)


def get_case_events(case):
    # Columns : template, document, date, subject, body, email,

    if case.events is None:
        return dmc.Alert(
            "No events found on this case.",
            color="gray",
            variant="filled",
            sx={"width": "100%"},
        )

    events = case.events

    for e in events:
        e["date"] = (
            e["date"].strftime("%Y-%m-%d - %H:%M:%S")
            if e["date"] is not None
            and isinstance(e["date"], datetime.datetime)
            else e["date"]
        )

    return dag.AgGrid(
        id="case-events",
        columnDefs=[
            {
                "headerName": "Template",
                "field": "template",
                "filter": "agTextColumnFilter",
                "sortable": True,
                "resizable": True,
                "flex": 1,
            },
            {
                "headerName": "Date",
                "field": "date",
                "editable": True,
                "filter": "agDateColumnFilter",
                "sortable": True,
                "resizable": True,
                "flex": 1,
            },
        ],
        rowData=events,
        dashGridOptions={
            "undoRedoCellEditing": True,
            "rowSelection": "multiple",
            "rowMultiSelectWithClick": True,
        },
    )
