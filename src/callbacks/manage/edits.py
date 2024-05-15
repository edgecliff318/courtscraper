import json
import logging

import dash
import dash_mantine_components as dmc
from dash import ALL, Input, Output, State, callback, dcc

import src.models as models
from src.core.base import BaseService
from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@callback(
    Output("edit-component-output", "children"),
    Output({"type": "edit-component-fields", "index": ALL}, "value"),
    Input("edit-component-save", "n_clicks"),
    Input("edit-component-reset", "n_clicks"),
    Input("edit-component-new", "n_clicks"),
    Input("edit-component-collection", "data"),
    Input("edit-component-item-id", "data"),
    State({"type": "edit-component-fields", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def edit_component(save, reset, new, collection, item_id, fields):
    ctx = dash.callback_context

    # TODO: Check security here

    if not ctx.triggered:
        return dash.no_update, dash.no_update

    serializer_mapping = {
        "participants": models.Participant,
    }
    serializer_model = serializer_mapping.get(collection)

    if serializer_model is None:
        raise ValueError(f"Invalid collection: {collection}")

    class GenericService(BaseService):
        collection_name = collection
        serializer = serializer_model

    service = GenericService()

    def extract_index_type(key):
        key_parsed = key.split(".")[0]
        key_parsed = json.loads(key_parsed)
        return key_parsed["index"], key_parsed["type"]

    fields_dict = {
        extract_index_type(key)[0]: value
        for key, value in ctx.states.items()
        if '"type":"edit-component-fields"' in key
    }

    if ctx.triggered[0]["prop_id"].startswith("edit-component-reset"):
        elements = service.get_single_item(item_id).model_dump()

        output_values = [elements.get(k) for k in fields_dict.keys()]
        output_message = dmc.Alert(
            "Refresh successful",
            color="green",
            variant="light",
            withCloseButton=True,
        )

        return output_message, output_values

    if ctx.triggered[0]["prop_id"].startswith("edit-component-save"):
        service.patch_item(item_id, fields_dict)

        output_message = dmc.Alert(
            "Save successful",
            color="green",
            variant="light",
            withCloseButton=True,
        )

        return output_message, fields

    if ctx.triggered[0]["prop_id"].startswith("edit-component-new"):
        new_item = serializer_model(**fields_dict)
        item = service.create_item(new_item)

        item_link = dcc.Link(
            f"{item.id}",
            href=f"/manage/{collection}/{item.id}",
        )

        output_message = dmc.Alert(
            [f"New {collection} created: ", item_link],
            color="green",
            variant="light",
            withCloseButton=True,
        )

        return output_message, fields
