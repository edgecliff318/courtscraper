import logging

import dash
import dash_mantine_components as dmc
from dash import ALL, Input, Output, State, callback

from src.components.cases.payments import get_invoice_history
from src.connectors import payments as payments_connector
from src.core.config import get_settings
from src.core.format import timestamp_to_date

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
    Output("invoice-data-refresh", "data"),
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
    ) and price_id is not None:
        payments_service = payments_connector.PaymentService()

        invoice = payments_service.create_invoice(
            customer_id=customer_id, product_id=product_id, price_id=price_id
        )

        return (
            dmc.Alert(
                f"The invoice has been created for to the customer with id {invoice.id}",
                color="success",
                variant="light",
                title="Invoice Created",
            ),
            invoice.id,
        )

    return dash.no_update, None


@callback(
    Output({"type": "modal-client-pars", "index": "invoices"}, "data"),
    Output({"type": "modal-client-pars", "index": "invoices"}, "value"),
    Input("invoice-data-refresh", "data"),
    State("case-manage-payments-customer-id", "data"),
    State({"type": "modal-client-pars", "index": "invoices"}, "value"),
)
def update_invoice_list(invoice_date_refresh, customer_id, invoices_selected):
    if invoice_date_refresh is None:
        return dash.no_update, dash.no_update

    if customer_id is None:
        return dash.no_update, dash.no_update

    invoices = get_invoice_history(customer_id)

    invoices_options = [
        {
            "label": f"{timestamp_to_date(invoice.get('created'))} - {invoice.get('amount_due')/100:.2f} $",
            "value": invoice.get("id"),
        }
        for invoice in invoices
    ]

    if invoices_selected is None:
        invoices_selected = []

    invoices_selected.append(invoice_date_refresh)

    return invoices_options, invoices_selected
