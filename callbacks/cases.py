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
        results = components.tables.make_bs_table(pd.concat(data))
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


def retrieve():
    import requests

    url = "https://www.courts.mo.gov/cnet/searchResult.do"

    payload = {
        "draw": 1,
        "columns": [
            {
                "data": 0,
            },
            {
                "data": "initFiling",
            },
            {
                "data": "caseNumber",
            },
            {
                "data": "caseStyle",
            },
            {
                "data": "caseType",
            },
            {
                "data": "countyDesc",
                "name": ""
            }
        ],
        "order": [
            {
                "column": 0,
                "dir": "asc"
            }
        ],
        "start": 0,
        "length": 2000
    }

    headers = {
        'Connection': 'keep-alive',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google '
                     'Chrome";v="96"',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/json;charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/96.0.4664.110 Safari/537.36',
        'sec-ch-ua-platform': '"macOS"',
        'Origin': 'https://www.courts.mo.gov',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.courts.mo.gov/cnet/searchResult.do'
                   '?countyCode=JAK&courtCode=CT16&startDate=12%2F13%2F2021'
                   '&caseStatus=A&caseType=All&locationCode=',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Cookie': 'JSESSIONID=0001w1CSXHk5xlqHY5AFHd2vrAF:-51GELP; '
                  'UJID=8c0198c1-c79a-48e0-8010-6840f10a9a7a; '
                  'UJIA=-1177887633; _ga=GA1.2.1015627111.1640115244; '
                  '_gid=GA1.2.1078078441.1640115244; '
                  'crowd.token_key=hC50te1J3FFVjuKdEmQvHw00; SameSite=None; '
                  '_gat_gtag_UA_109681667_1=1; '
                  'ADRUM_BTa=R:134|g:5dca8383-55e4-43c5-886e-36393e65b98a|n'
                  ':customer1_1fca79d6-9c6d-405b-ab6b-c0feb37078fb; '
                  'ADRUM_BT1=R:134|i:5482|e:60; '
                  'crowd.token_key=hC50te1J3FFVjuKdEmQvHw00'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
