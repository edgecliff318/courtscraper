from datetime import datetime

import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify

from src.connectors import payments as payments_connector
from src.core.format import timestamp_to_date
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


def get_invoice_form():
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
        color="dark",
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
    return invoice_form


def get_invoice_widget(participants_list, role="client"):
    invoices_options = []
    if len(participants_list) == 0:
        invoice_form = dmc.Text("No participants found. Please add one.")
    elif len(participants_list) > 1:
        invoice_form = dmc.Text(
            "Multiple participants found. Please select one."
        )
    else:
        participant = participants_list[0]

        invoice_form = get_invoice_form()
        invoices = get_invoice_history(participant)

        invoices_options = [
            {
                "label": f"{timestamp_to_date(invoice.get('created'))} - {invoice.get('amount_due')/100:.2f} $",
                "value": invoice.get("id"),
            }
            for invoice in invoices
        ]

    invoice_section = dmc.Stack(
        [
            dmc.Title("Select an Invoice to Embed", order=4),
            dmc.MultiSelect(
                label="Invoices",
                placeholder="Select the invoices",
                data=[
                    {
                        "label": invoice.get("label"),
                        "value": invoice.get("value"),
                    }
                    for invoice in invoices_options
                ],
                value=[],
                id={"type": f"modal-{role}-pars", "index": "invoices"},
            ),
            dmc.Title("Create a New Invoice (if not already done)", order=5),
            invoice_form,
        ]
    )

    return invoice_section


def get_invoice_history(participant):
    participants_service = ParticipantsService()
    payments_service = payments_connector.PaymentService()

    if isinstance(participant, str):
        stripe_id = participant

    elif participant.stripe_id is None:
        if participant.email is None:
            raise ValueError("No Email found for the participant")
        customer = payments_service.get_or_customer(participant.email)
        participant.stripe_id = customer.id
        participants_service.patch_item(
            participant.id, {"stripe_id": customer.id}
        )
        stripe_id = customer.id
    else:
        stripe_id = participant.stripe_id

    invoice_history = payments_service.get_invoice_history(stripe_id)

    return invoice_history


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

    invoice_form = get_invoice_form()

    invoice_history = get_invoice_history(participant)

    # Get the payment history
    payment_history = payments_service.get_payment_history(
        participant.stripe_id
    )

    # Create a table with the payment history
    payment_history_table = generate_table(
        data=payment_history, columns=["created", "amount", "description"]
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
