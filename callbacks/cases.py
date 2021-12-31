import logging
import os

from app import app
import pandas as pd
import dash
import dash_bootstrap_components as dbc
import dash.html as html
from dash.dependencies import Input, Output, State, ALL

import config

import components.tables
from loader.config import ConfigLoader
from loader.leads import CaseNet
from scrapers.missouri import ScraperMOCourt

logger = logging.Logger(__name__)


@app.callback(
    Output("court-selector", "options"),
    Input("url", "pathname"),
)
def render_content_persona_details_selector(pathname):
    config_loader = ConfigLoader(
        path=os.path.join(config.config_path, "config.json"))

    courts = config_loader.load()['courts']
    options = [
        {"label": c.get("label"), "value": c.get("value")}
        for c in courts
    ]
    return options


@app.callback(
    Output("cases-data", "children"),
    Input('search-button', "n_clicks"),
    Input("court-selector", "value"),
    Input("date-selector", "date")
)
def render_results(search, court_code_list, date):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    results = "Empty"
    data = []
    if trigger_id == "search-button":
        for case_type in ("Traffic%2FMunicipal", "Infraction"):
            for court_code in court_code_list:
                config_loader = ConfigLoader(
                    path=os.path.join(config.config_path, "config.json"))
                court = config_loader.get_court_details(court_code)

                case_net = CaseNet(
                    url=config.case_net_url, username=config.case_net_username,
                    password=config.case_net_password
                )
                courts_data = case_net.get_leads(
                    court_code, court.get("countycode"), date,
                    case_type
                )
                data.append(pd.DataFrame.from_dict(courts_data['data']))
        df = pd.concat(data)
        df = df.drop(
            columns=[
                "confidentialFlag", "caseTypeCode", "predCode",
                "courtAvailableFlag", "dbSource", "src", "caseSecurity",
                "locnCode"]).set_index(
            "caseNumber"
        )
        results = components.tables.make_bs_table(df)
    return [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H3("Cases",
                                className="card-title"),
                        results,
                    ]
                ),
            ),
            width=12
        )
    ]


def get_table_data(name, details):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3(name, className="card-title"),
                dbc.Table(
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(
                                        k,
                                        style={"font-weight": "700"}
                                    ),
                                    html.Td(v)
                                ]
                            )
                            for k, v in details.items()
                        ]
                    ),
                    hover=True,
                    responsive=True,
                ),
            ]
        ),
    )


@app.callback(
    Output("lead-single", "children"),
    Input("url", "pathname")
)
def render_case_details(pathname):
    if "/leads/single" in pathname:
        case_id = pathname.split("/")[-1]
        error = False
        message = ""
        try:
            case_id = int(case_id)
        except:
            message = "Case ID must be a number"
            error = True

        if error:
            return [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("An Error Occurred",
                                        className="card-title"),
                                html.P(message),
                            ]
                        ),
                    ),
                    width=12
                )
            ]

        else:
            case = {
                "case_number": case_id
            }
            results = ScraperMOCourt().get_case_detail(case)
            return [
                dbc.Col(
                    get_table_data(
                        f"Case {results['details']['case_number']}",
                        results['case_header']),
                    width=6
                ),
                dbc.Col(
                    get_table_data("Charges",
                                   results["charges"]["Charge/Judgment"]),
                    width=6
                ),
            ]
