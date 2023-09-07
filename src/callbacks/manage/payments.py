import logging
import dash
from dash import ALL, Input, Output, State, callback

from src.connectors import payments as payments_connector
from src.components.cases.workflow.email import (
    get_email_params,
    get_preview,
    send_email,
)
import dash_mantine_components as dmc

from src.connectors.intercom import IntercomConnector
from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@callback(
    Output("case-manage-payments-price", "data"),
    Input("case-manage-payments-products", "value"),
)
def case_manage_payments_price(product_id):
    payments_service = payments_connector.PaymentService()
    prices = payments_service.get_prices(product_id)
    return [
        {"label": f'$ {str(price["unit_amount"]/100)}', "value": price["id"]}
        for price in prices
    ]


@callback(
    Output("case-manage-payments-status", "children"),
    Input("case-manage-payments-create-invoice", "n_clicks"),
    State("case-manage-payments-products", "value"),
    State("case-manage-payments-price", "value"),
    State("case-manage-payments-customer-id", "data"),
)
def case_manage_payments_send(n_clicks, product_id, price_id, customer_id):
    ctx = dash.callback_context

    # If button send clicked
    if (
        ctx.triggered[0]["prop_id"]
        == "case-manage-payments-create-invoice.n_clicks"
    ):
        payments_service = payments_connector.PaymentService()

        invoice = payments_service.send_invoice(
            customer_id=customer_id, product_id=product_id, price_id=price_id
        )

        return dmc.Alert(
            f"The invoice has been sent to the customer with id {invoice.id}",
            color="success",
            variant="light",
            title="Invoice sent",
        )
