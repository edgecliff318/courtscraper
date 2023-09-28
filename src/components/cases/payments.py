from datetime import datetime

import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify

from src.connectors import payments as payments_connector
from src.models.cases import Case
from src.services.participants import ParticipantsService


def format_table_row(row, column):
    if column.lower() == "created":
        # Format the data from timestamp 1696178121
        return datetime.fromtimestamp(row).strftime("%Y-%m-%d %H:%M:%S")
    else:
        return row


def generate_table(data, columns):
    header = [html.Thead(html.Tr([html.Th(c.capitalize()) for c in columns]))]

    rows = [
        html.Tr(
            [html.Td(format_table_row(e.get(c), column=c)) for c in columns]
        )
        for e in data
    ]

    body = [html.Tbody(rows)]

    return dmc.Table(
        header + body,
        highlightOnHover=True,
    )


def get_case_payments(case: Case):
    # Get the list of participants
    participants_service = ParticipantsService()

    if case.participants is None or len(case.participants) == 0:
        return dmc.Alert(
            "No participants found ! Please add participants to the case",
            color="red",
            title="No participants found",
        )

    participants_list = participants_service.get_items(
        id=case.participants, role="defendant"
    )

    if len(participants_list) == 0:
        return dmc.Alert(
            "No participants found",
            color="red",
            title="No participants found",
        )

    if len(participants_list) > 1:
        return dmc.Alert(
            "Multiple participants found",
            color="red",
            title="Multiple participants found",
        )

    participant = participants_list[0]

    # Get the list of payments
    payments_service = payments_connector.PaymentService()

    # Get the list of products
    products = payments_service.get_products()

    # Create a multi select with the products
    products_select = dmc.Select(
        data=[
            {"label": product["name"], "value": product["id"]}
            for product in products
        ],
        label="Products",
        placeholder="Select products",
        searchable=True,
        description="You can select the products here. ",
        id="case-manage-payments-products",
        creatable=True,
        value=products[0]["id"] if len(products) > 0 else None,
    )

    # Create an input money field for the price
    price_input = dmc.Select(
        label="Price",
        placeholder="Price",
        description="You can enter the price here. ",
        id="case-manage-payments-price",
        creatable=True,
        searchable=True,
    )

    # Create an invoice button
    invoice_create_button = dmc.Button(
        "Create Invoice",
        color="blue",
        variant="outline",
        id="case-manage-payments-create-invoice",
        leftIcon=DashIconify(icon="mdi:invoice-add"),
    )

    invoice_form = dmc.Stack(
        [
            dmc.Group(
                [
                    products_select,
                    price_input,
                ]
            ),
            dmc.Group(
                [
                    invoice_create_button,
                ]
            ),
        ]
    )

    if participant.stripe_id is None:
        if participant.email is None:
            return dmc.Alert(
                (
                    "Please update the participant in the case/details "
                    "section in order "
                    "to retrieve the data from Stripe on the payments"
                    " and send invoices."
                ),
                color="red",
                title="No email found",
            )
        customer = payments_service.get_or_customer(participant.email)
        participant.stripe_id = customer.id
        participants_service.patch_item(
            participant.id, {"stripe_id": customer.id}
        )

    # Get the payment history
    payment_history = payments_service
    payment_history = payments_service.get_payment_history(
        participant.stripe_id
    )

    # Create a table with the payment history
    payment_history_table = generate_table(
        data=payment_history, columns=["created", "amount", "description"]
    )

    invoice_history = payments_service.get_invoice_history(
        participant.stripe_id
    )

    # Create a table with the invoice history
    invoice_history_table = generate_table(
        data=invoice_history,
        columns=[
            "created",
            "amount_due",
            "amount_paid",
            "description",
            "due_date",
        ],
    )

    return dmc.Stack(
        [
            dmc.Title("Invoices", order=4),
            invoice_history_table,
            dmc.Divider(className="mt-4"),
            dmc.Title("Payments", order=4),
            payment_history_table,
            dmc.Divider(className="mt-4"),
            dmc.Title("Create a New Invoice", order=4),
            invoice_form,
            html.Div(id="case-manage-payments-status"),
            dcc.Store(
                id="case-manage-payments-customer-id",
                data=participant.stripe_id,
            ),
        ],
        className="mt-4",
    )
