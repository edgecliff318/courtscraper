import os

import dash_bootstrap_components as dbc
import dash.html as html
import pandas as pd
import dash_design_kit as ddk

import config


def make_bs_table(results, size='md'):
    """
    Function to generate a boostrap table from a dataframe
    :param size: Specify table size, options: 'sm', 'md', 'lg'.
    :param results: bootstrap table
    :type results: pd.Dataframe
    :return:
    :rtype:
    """
    table_header = [
        html.Thead(
            html.Tr([html.Th(c) for c in results.reset_index().columns]))
    ]

    table_body = [html.Tbody(
        list(
            html.Tr(list(
                html.Td(round(v, 4) if isinstance(v, float) else v) for v in
                data.values))
            for i, data in results.reset_index().iterrows()
        )
    )]

    table = dbc.Table(table_header + table_body, bordered=True, size=size)
    return table


def page(data=None):
    data_path = os.path.join(config.output_path, "data.csv")
    if os.path.exists(data_path):
        data = pd.read_csv(data_path).set_index("case_id")
    else:
        data = pd.DataFrame()
    return html.Div(

        dbc.Container(
            [
                dbc.Card(
                    ddk.DataTable(
                        id='table',
                        columns=[{"name": i, "id": i, "hideable": True} for i in data.columns],
                        data=data.to_dict("rows"),
                        editable=True,
                        hidden_columns=['offense'],
                        page_action="native",
                        export_columns='visible',
                        export_format='csv',
                    )
                )
            ],
            fluid=True,
            className="py-3",
        ),
        className="p-3 bg-light rounded-3",
    )
