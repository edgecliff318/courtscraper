import logging
from datetime import datetime

import dash
import dash_mantine_components as dmc
import pytz

from src.connectors.payments import PaymentService

logger = logging.Logger(__name__)

dash.register_page(
    __name__, order=5, path_template="/manage/payments/<payment_id>"
)


def layout(payment_id):
    payment_service = PaymentService()
    if payment_id is not None and payment_id != "none":
        payment = payment_service.get_item(payment_id)

    else:
        payments = payment_service.get_last_payments()

        def int_to_date(timestamp):
            date = datetime.fromtimestamp(timestamp)
            # Convert to Chicago timezone
            date = date.astimezone(pytz.timezone("America/Chicago"))
            return date.strftime("%Y-%m-%d %H:%M:%S")

        header = dmc.Grid(
            [
                dmc.Col(
                    dmc.Text("Email", color="dark"),
                    span=2,
                ),
                dmc.Col(
                    dmc.Text("Amount", color="dark"),
                    span=1,
                ),
                dmc.Col(
                    dmc.Text("Date", color="dark"),
                    span=2,
                ),
                dmc.Col(
                    dmc.Text("Status", color="dark"),
                    span=2,
                ),
                dmc.Col(
                    dmc.Text("Actions", color="dark"),
                    span=5,
                ),
            ]
        )

        return dmc.Card(
            dmc.Stack(
                [
                    dmc.Group(
                        [
                            dmc.Text("Payments", size="xl"),
                            dmc.Text("Last payments", size="sm"),
                        ]
                    ),
                    header,
                ]
                + [
                    dmc.Grid(
                        [
                            dmc.Col(
                                dmc.Text(payment.receipt_email),
                                span=2,
                            ),
                            dmc.Col(
                                dmc.Text(f"{payment.amount / 100} $"),
                                span=1,
                            ),
                            dmc.Col(
                                dmc.Text(int_to_date(payment.created)),
                                span=2,
                            ),
                            dmc.Col(
                                dmc.Badge(
                                    payment.status,
                                    size="sm",
                                    color=(
                                        "green"
                                        if payment.status == "succeeded"
                                        else "red"
                                    ),
                                ),
                                span=2,
                            ),
                            dmc.Col(
                                dmc.Group(
                                    [
                                        dmc.Select(
                                            data=[
                                                {
                                                    "label": "123456789",
                                                    "value": "123456789",
                                                },
                                            ],
                                            size="xs",
                                        ),
                                        dmc.Button(
                                            "View",
                                            color="dark",
                                            size="xs",
                                            id="payment-view-button",
                                        ),
                                        dmc.Button(
                                            "Attach to case",
                                            color="dark",
                                            size="xs",
                                            id="payment-attach-button",
                                        ),
                                    ]
                                ),
                                span=5,
                            ),
                        ]
                    )
                    for payment in payments
                ]
            )
        )
