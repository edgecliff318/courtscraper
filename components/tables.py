import pandas as pd
from dash import dash_table
from dash import html
import dash_design_kit as ddk
import dash_bootstrap_components as dbc

def table_type(df_column):
    if isinstance(df_column.dtype, pd.DatetimeTZDtype):
        return 'datetime',
    elif (isinstance(df_column.dtype, pd.StringDtype) or
          isinstance(df_column.dtype, pd.BooleanDtype) or
          isinstance(df_column.dtype, pd.CategoricalDtype) or
          isinstance(df_column.dtype, pd.PeriodDtype)):
        return 'text'
    elif (isinstance(df_column.dtype, pd.SparseDtype) or
          isinstance(df_column.dtype, pd.IntervalDtype) or
          isinstance(df_column.dtype, pd.Int8Dtype) or
          isinstance(df_column.dtype, pd.Int16Dtype) or
          isinstance(df_column.dtype, pd.Int32Dtype) or
          isinstance(df_column.dtype, pd.Int64Dtype)):
        return 'numeric'
    else:
        return 'any'


def make_df_table(df, selected_rows=None):
    if selected_rows is None:
        selected_rows = []
    return ddk.DataTable(
        columns=[
            {'name': i, 'id': i, 'type': table_type(df[i])} for i in df.columns
        ],
        data=df.to_dict('records'),
        filter_action='native',
        css=[{
            'selector': 'table',
            'rule': 'table-layout: fixed'
        }],
        row_selectable="multi",
        selected_rows=selected_rows,
        id="funds-table",
        sort_action="native",
        sort_mode='multi',
        style_table={"fontSize": "0.95em"},
        style_cell={
            "textAlign": "left",
            "height": "fitContent",
            "whiteSpace": "pre-line",
            "wordWrap": "break-word",
        },
    )


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
