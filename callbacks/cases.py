import logging
import os
import sys
from datetime import datetime

from app import app
import pandas as pd
import dash
import dash_bootstrap_components as dbc
import dash.html as html
from dash.dependencies import Input, Output, State, ALL

import config

import components.tables
from components import content
from core import tools, storage
from loader.config import ConfigLoader
from loader.leads import CaseNet
from scrapers.missouri import ScraperMOCourt

logger = logging.Logger(__name__)

sys.setrecursionlimit(10000)


@tools.cached(storage=storage.PickleStorage())
def get_case_datails(case_id):
    case = {
        "case_number": case_id
    }
    results = ScraperMOCourt().get_case_detail(case)
    return results


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
            results = get_case_datails(case_id)
            if results.get('ticket', {}).get("image") is None:
                results = get_case_datails(case_id, no_cache=True)

            if results.get('ticket') is not None:
                ticket = content.process.page(results.get('ticket'),
                                              filemanager=False)
            else:
                logger.error(f"No ticket found for case {case_id}, "
                             f"received {results}")
                ticket = []
            year_of_birth = results['parties'].split("Year of Birth: ")
            if len(year_of_birth) > 1:
                try:
                    year_of_birth = int(year_of_birth[-1])
                except Exception:
                    year_of_birth = None

            name = results['parties'].split(", Defendant")
            if len(name) > 1:
                name = name[0]
                try:
                    first_name = " ".join(name.split(", ")[1:])
                    r = first_name.split(" ")
                    if len(r) >= 2:
                        first_name = r[0]
                        middle_name = r[1]
                    else:
                        middle_name = ""
                    last_name = " ".join(name.split(", ")[:1])
                except Exception:
                    first_name = None
                    last_name = None

            def get_beenverified_link(first_name=None, last_name=None,
                                      middle_name=None,
                                      year=None, state="MO"):
                state = "MO"
                url = f"https://www.beenverified.com/app/search/person?"
                if first_name is not None:
                    url += f"fname={first_name}&"
                if last_name is not None:
                    url += f"ln={last_name}&"
                if middle_name is not None:
                    url += f"mn={middle_name}&"
                if state is not None:
                    url += f"state={state}&"
                if year is not None:
                    age = datetime.now().year - year
                    url += f"age={age}"
                return url

            buttons = html.Div(
                [
                    dbc.Button(
                        "Find on BeenVerified", color="primary",
                        href=get_beenverified_link(
                            first_name, last_name, middle_name, year_of_birth),
                        external_link=True,
                        className="mb-2 ml-1"
                    ),
                    dbc.Button(
                        "Send SMS", color="primary",
                        href=get_beenverified_link(
                            first_name, last_name, year_of_birth),
                        external_link=True,
                        className="mb-2 ml-1"
                    ),
                    dbc.Button(
                        "Flag", color="primary",
                        href=get_beenverified_link(
                            first_name, last_name, year_of_birth),
                        external_link=True,
                        className="mb-2 ml-1"
                    ),
                ]
            )
            return [
                dbc.Col(
                    html.H2(
                        f"Case ID: {case_id}, Defendent: {first_name}, "
                        f"{last_name}, {year_of_birth}",
                        className="text-left"),
                    width=6
                ),
                dbc.Col(
                    buttons,
                    width=6
                ),
                dbc.Col(
                    get_table_data(
                        f"Case {results['details']['case_number']}",
                        results['case_header']),
                    width=6
                ),
                dbc.Col(
                    get_table_data(
                        "Charges",
                        results.get(
                            "charges", {}
                        ).get("Charge/Judgment", {})),
                    width=6
                ),
                *ticket
            ]
