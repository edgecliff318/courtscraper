import logging
import os
import sys
from datetime import date, datetime

from app import app
import pandas as pd
import dash
import dash_bootstrap_components as dbc
import dash.html as html
from dash.dependencies import Input, Output

import config

import components.tables
from components import content
from loader.config import ConfigLoader
from loader.leads import CaseNet, LeadsLoader
from core.cases import get_case_datails, get_verified_link, get_lead_single_been_verified

logger = logging.Logger(__name__)

sys.setrecursionlimit(10000)


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
    Output("lead-single-message-selector", "options"),
    Input("url", "pathname"),
)
def render_message_selector(pathname):
    config_loader = ConfigLoader(
        path=os.path.join(config.config_path, "config.json"))

    messages = config_loader.load()['messages']
    options = [
        {"label": c.get("label"), "value": c.get("value")}
        for c in messages
    ]
    return options


@app.callback(
    Output("lead-single-message", "value"),
    Input("lead-single-message-selector", "value"),
)
def render_selected_message(message):
    return message


@app.callback(
    Output("lead-single-message-status", "children"),
    Input("url", "pathname"),
    Input("lead-single-send-sms-button", "n_clicks"),
    Input("lead-single-message", "value"),
)
def send_message(pathname, sms_button, message):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == "lead-single-send-sms-button":
        if "/leads/single" in pathname:
            case_id = pathname.split("/")[-1]
            error = False
            message = ""
            try:
                case_id = int(case_id)
            except:
                message = "Case ID must be a number"
                error = True

            if not error:
                lead_loader = LeadsLoader(
                    path=os.path.join(config.config_path, "leads.json")
                )
                data = lead_loader.load()

                # Send message

                # Save interaction
                data.setdefault(case_id, {})
                interactions = data.get(case_id, {}).get("interactions", [])
                interactions.append({
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "message": message,
                    "type": "sms",
                    "status": "sent"
                })
                data[case_id]["interactions"] = interactions
                lead_loader.save(data)
                message = dbc.Alert(
                    "Message sent",
                    color="success",
                    dismissable=True,
                    className="alert-dismissible fade show"
                )

            return message


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


@app.callback(
    Output("leads-data", "children"),
    Input('leads-button', "n_clicks"),
    Input("court-selector", "value"),
    Input("date-selector", "date")
)
def render_leads(search, court_code_list, date):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    results = "Empty"
    data = []
    if trigger_id == "leads-button":
        lead_loader = LeadsLoader(
            path=os.path.join(config.config_path, "leads.json")
        )
        data = lead_loader.load()
        df = pd.DataFrame(data.values())
        df["caseNumber"] = data.keys()
        df['interactions'] = df["interactions"].map(
            lambda i: True if not pd.isna(i) else False)
        df["case_date"] = pd.to_datetime(df["case_date"])

        if court_code_list is not None and court_code_list:
            df = df[df.court_code.isin(court_code_list)]
        if date is not None:
            df = df[df["case_date"].dt.date == date]

        results = components.tables.make_bs_table(
            df[['caseNumber', 'interactions', 'court_name', 'case_date', 'first_name', 'last_name', 'telephone', 'been_verified', 'age', 'charges']])
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


def get_interactions_data(name, interactions):
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
                                        i.get("interactionType"),
                                        style={"font-weight": "700"}
                                    ),
                                    html.Td(i.get("interactionMessage"), )
                                ]
                            )
                            for i in interactions
                        ]
                    ),
                    hover=True,
                    responsive=True,
                ),
            ]
        ),
    )


@app.callback(
    Output("lead-single-been-verified", "children"),
    Input("lead-single-been-verified-button", "href")
)
def render_lead_single_been_verified(link):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "lead-single-been-verified-button":
        try:
            data = get_lead_single_been_verified(link)
            output = get_table_data("Been Verified", data)
        except Exception as e:
            output = dbc.Alert(
                f"An error occurred while retrieving the information. {e}",
                color="danger"
            )
        return output
    return None


@app.callback(
    Output("lead-single", "children"),
    Output("lead-single-been-verified-trigger", "children"),
    Input("url", "pathname")
)
def render_case_details(pathname):
    if "/leads/single" in pathname:
        case_id = pathname.split("/")[-1]
        error = False
        message = ""
        try:
            case_id = str(case_id)
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
            if results.get('ticket') is None:
                results = get_case_datails(case_id, no_cache=True)
                if results.get('ticket') is not None:
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
            age = None
            if len(year_of_birth) > 1:
                try:
                    year_of_birth = int(year_of_birth[-1])
                    age = date.today().year - year_of_birth
                except Exception:
                    year_of_birth = None
                    age = None
            name = results['parties'].split(", Defendant")
            first_name, last_name, link = get_verified_link(
                name, year_of_birth
            )

            buttons = html.Div(
                [
                    dbc.Button(
                        "Find Manually on BeenVerified", color="primary",
                        href=link,
                        external_link=True,
                        className="mb-2 ml-1",
                        id="lead-single-been-verified-button"
                    )
                ]
            )

            return [
                dbc.Col(
                    html.H2(
                        f"Case ID: {case_id}, Defendent: {first_name}, "
                        f"{last_name}, {year_of_birth} ({age})",
                        className="text-left"),
                    width=8
                ),
                dbc.Col(
                    buttons,
                    width=4
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
            ], ""


@app.callback(
    Output("lead-single-interactions", "children"),
    Input("url", "pathname"),
    Input("lead-single-message-status", "children"),
)
def render_case_interactions(pathname, status):
    if "/leads/single" in pathname:
        case_id = pathname.split("/")[-1]
        error = False
        message = ""
        try:
            case_id = int(case_id)
        except:
            message = "Case ID must be a number"
            error = True

        if not error:
            lead_loader = LeadsLoader(
                path=os.path.join(config.config_path, "leads.json")
            )
            lead_loader.load()
            interactions = lead_loader.get_interactions(case_id)
            output = get_interactions_data("Interactions", interactions)
            return output