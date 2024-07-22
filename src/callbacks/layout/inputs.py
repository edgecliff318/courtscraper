import logging

from dash import Input, Output, callback

from src.services import courts

logger = logging.Logger(__name__)


@callback(
    Output("court-selector", "data"),
    Input("url", "pathname"),
)
def render_content_persona_details_selector(pathname):
    courts_list = courts.get_courts()
    data = []
    for court in courts_list:
        if court.state in [d["group"] for d in data]:
            for d in data:
                if d["group"] == court.state:
                    if court.code not in [i["value"] for i in d["items"]]:
                        # TODO:Should be using a unique identifier here
                        d["items"].append(
                            {"label": court.name, "value": court.code}
                        )
        else:
            data.append(
                {
                    "items": [{"label": court.name, "value": court.code}],
                    "group": court.state,
                }
            )

    return data
