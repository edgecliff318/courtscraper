import logging

import dash
import dash_mantine_components as dmc
from dash import ALL, Input, Output, State, callback

from src.connectors import payments as payments_connector
from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@callback(
    Output("case-manage-payments-price", "value"),
    Output("case-manage-payments-price", "data"),
    Input("case-manage-payments-price", "data"),
    State("case-manage-payments-price", "value"),
    State("case-manage-payments-products", "value"),
)
def case_manage_payments_price_create(price_list, price_selected, product_id):
    payments_service = payments_connector.PaymentService()

    if (price_selected is None or "price_" in str(price_selected)) and (
        price_list is not None or price_list
    ):
        return dash.no_update, dash.no_update

    if price_selected is not None:
        if "price_" not in str(price_selected):
            # Create the price
            payments_service = payments_connector.PaymentService()
            price = payments_service.create_price(
                product_id=product_id,
                amount=int(price_selected) * 100,
            )

            price_selected = price["id"]

    prices = payments_service.get_prices(product_id)
    prices_outputs = [
        {"label": f'$ {str(price["unit_amount"]/100)}', "value": price["id"]}
        for price in prices
    ]

    return price_selected, prices_outputs


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
