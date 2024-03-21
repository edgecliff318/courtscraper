import logging
from datetime import datetime

import dash
import dash_mantine_components as dmc
import pandas as pd
import pytz
from dash import dcc, html
from dash_iconify import DashIconify

from src.connectors.payments import PaymentService, get_custom_fields
from src.core.dates import get_continuance_date
from src.core.dynamic_fields import CaseDynamicFields
from src.services.billings import BillingsService
from src.services.cases import CasesService, get_many_cases

logger = logging.Logger(__name__)

dash.register_page(
    __name__, order=5, path_template="/manage/payments/<payment_id>"
)


class PaymentsTable:
    def __init__(self):
        pass

    def render_header(self):
        return dmc.Grid(
            [
                dmc.Col(
                    dmc.Text(
                        "Billing",
                        color="dark",
                        weight=600,
                    ),
                    span=3,
                ),
                dmc.Col(
                    dmc.Text(
                        "Payment",
                        color="dark",
                        weight=600,
                    ),
                    span=3,
                ),
                dmc.Col(
                    dmc.Text(
                        "Cases",
                        color="dark",
                        weight=600,
                    ),
                    span=3,
                ),
                dmc.Col(
                    dmc.Text(
                        "Actions",
                        color="dark",
                        weight=600,
                    ),
                    span=3,
                ),
            ],
            style={"border-bottom": "1px solid #e1e1e1"},
        )

    def int_to_date(self, timestamp):
        date = datetime.fromtimestamp(timestamp)
        # Convert to Chicago timezone
        date = date.astimezone(pytz.timezone("America/Chicago"))
        return date.strftime("%Y-%m-%d %H:%M:%S")

    def render_billing_info(self, checkout):
        customer_details = checkout.get("customer_details", {})
        if customer_details is None:
            return dmc.Text("No customer details", size="sm")
        address = customer_details.get("address", {})

        address_render = []
        if address is not None:
            if address.get("line1"):
                address_render.append(
                    dmc.Text(f"{address.get('line1')}", size="xs")
                )
            if address.get("line2"):
                address_render.append(
                    dmc.Text(f"{address.get('line2')}", size="xs")
                )
            if (
                address.get("postal_code")
                or address.get("city")
                or address.get("state")
            ):
                address_render.append(
                    dmc.Text(
                        f"{address.get('postal_code', '')}, {address.get('city', '')}, {address.get('state', '')}",
                        size="xs",
                    )
                )

        return dmc.Stack(
            [
                dmc.Group(
                    [
                        dmc.Text(
                            f"{customer_details.get('name')}",
                            size="sm",
                            weight=600,
                            color="dark",
                        ),
                        dmc.Text(
                            get_custom_fields(checkout, "birthdate"),
                            size="sm",
                            weight=600,
                            color="dark",
                        ),
                    ],
                    position="apart",
                ),
                dmc.Group(
                    [
                        dmc.Text(customer_details.get("email"), size="xs"),
                        dmc.Text(customer_details.get("phone"), size="xs"),
                    ],
                    position="apart",
                ),
            ]
            + address_render,
            spacing="xs",
        )

    def render_checkout_info(self, checkout):
        return dmc.Stack(
            [
                dmc.Group(
                    [
                        dmc.Text("Amount", size="sm", weight=600),
                        dmc.Text(
                            f"{checkout.get('amount_total') / 100} $",
                            size="sm",
                        ),
                    ],
                    position="apart",
                    spacing="xs",
                ),
                dmc.Group(
                    [
                        dmc.Text("Date", size="sm", weight=600),
                        dmc.Text(
                            self.int_to_date(checkout.get("created")),
                            size="sm",
                        ),
                    ],
                    position="apart",
                    spacing="xs",
                ),
                dmc.Group(
                    [
                        dmc.Text("Status", size="sm", weight=600),
                        dmc.Badge(
                            checkout.get("status"),
                            size="sm",
                            color=(
                                "green"
                                if checkout.get("status") == "complete"
                                else "red"
                            ),
                        ),
                    ],
                    position="apart",
                    spacing="xs",
                ),
                dmc.Group(
                    [
                        dmc.Text("Driver Name", size="sm", weight=600),
                        dmc.Text(
                            get_custom_fields(
                                checkout, "nameofdriverifdifferentthanpayment"
                            ),
                            size="sm",
                        ),
                    ],
                    position="apart",
                    spacing="xs",
                ),
                dmc.Group(
                    [
                        dmc.Text("Tickets", size="sm", weight=600),
                        dmc.Text(
                            get_custom_fields(checkout, "tickets"),
                            size="sm",
                        ),
                    ],
                    position="apart",
                    spacing="xs",
                ),
            ],
            spacing="xs",
        )

    def render_actions(self, checkout):
        styles_locked = {
            "label": {
                "&[data-checked]": {
                    "&, &:hover": {
                        "backgroundColor": dmc.theme.DEFAULT_COLORS["dark"][9],
                        "color": "white",
                    },
                },
            }
        }
        styles_onboarded = {
            "label": {
                "&[data-checked]": {
                    "&, &:hover": {
                        "backgroundColor": dmc.theme.DEFAULT_COLORS["green"][
                            9
                        ],
                        "color": "white",
                    },
                },
            }
        }

        return dmc.Stack(
            [
                dmc.ChipGroup(
                    [
                        dmc.Chip(
                            "Locked",
                            value="locked",
                            color="dark",
                            styles=styles_locked,
                        ),
                        dmc.Chip(
                            "Onboarded",
                            value="onboarded",
                            color="green",
                            styles=styles_onboarded,
                        ),
                        dmc.Chip("Invoice", value="invoice", color="gray"),
                        dmc.Chip("Not Done", value="not_done", color="red"),
                    ],
                    value=checkout.billing.get("status"),
                    id={
                        "type": "case-status-select",
                        "index": checkout.get("id"),
                    },
                ),
                dmc.Group(
                    [
                        dmc.Button(
                            "Attach to case",
                            color="dark",
                            size="xs",
                            id={
                                "type": "case-attach-button",
                                "index": checkout.get("id"),
                            },
                            disabled=checkout.billing.get("status")
                            == "locked",
                        ),
                    ]
                ),
                html.Div(
                    id={
                        "type": "case-status-select-output",
                        "index": checkout.get("id"),
                    }
                ),
            ]
        )

    def get_case_information(self, case_id, cases_information):
        if case_id is None or case_id == "":
            return dmc.Text("No case", size="sm")
        city = cases_information.get(case_id, {}).get("city")
        court_date = cases_information.get(case_id, {}).get("court_date")
        court_time = cases_information.get(case_id, {}).get("court_time")

        court_date_dt = pd.to_datetime(court_date)

        color = "gray"

        suggested_motion_for_continuance = None

        if court_date_dt is not None:
            if court_date_dt > pd.to_datetime("today") + pd.Timedelta(
                "30 day"
            ):
                color = "dark"
            elif court_date_dt > pd.to_datetime("today") + pd.Timedelta(
                "7 day"
            ):
                color = "yellow"
                # Same day of the following month
                suggested_motion_for_continuance = get_continuance_date(
                    court_date_dt
                )
            elif court_date_dt >= pd.to_datetime("today"):
                color = "red"
                suggested_motion_for_continuance = get_continuance_date(
                    court_date_dt
                )
            else:
                color = "gray"
        if suggested_motion_for_continuance is None:
            return dmc.Text(
                f"{city} - Court: {court_date} at {court_time}",
                size="sm",
                color=color,
            )
        else:
            return dmc.Stack(
                [
                    dmc.Text(
                        f"{city} - Court: {court_date} at {court_time}",
                        size="sm",
                        color=color,
                    ),
                    dmc.Text(
                        f"Suggested Continuance: {suggested_motion_for_continuance.strftime('%m/%d/%Y')} at {court_time}",
                        size="sm",
                        color="dark",
                    ),
                ]
            )

    def render_cases(self, checkout, cases_information):
        cases_list = get_custom_fields(checkout, "tickets")
        if cases_list is None:
            return dmc.Text("No cases", size="sm")

        if len(cases_list) == 0:
            return dmc.Text("No cases", size="sm")

        cases_list = cases_list.replace(" ", "").replace("#", "").split(",")

        return dmc.Stack(
            [
                dmc.Group(
                    [
                        html.A(
                            dmc.Text(
                                case,
                                size="sm",
                                weight=600,
                            ),
                            href=f"/manage/cases/{case}",
                            target="_blank",
                        ),
                        dmc.Text(
                            self.get_case_information(case, cases_information),
                            size="sm",
                            weight=600,
                        ),
                    ]
                )
                for case in cases_list
            ]
        )

    def render_participants(self, checkout):
        return dmc.Stack(
            [
                dmc.Text("Cases", size="sm"),
                dmc.Group(
                    [
                        dmc.Text(
                            size="sm",
                        ),
                    ]
                ),
            ]
        )

    def render_row(self, checkout, cases_information):
        return dmc.Grid(
            [
                dmc.Col(
                    self.render_billing_info(checkout),
                    span=3,
                ),
                dmc.Col(
                    self.render_checkout_info(checkout),
                    span=3,
                ),
                dmc.Col(
                    self.render_cases(checkout, cases_information),
                    span=3,
                ),
                dmc.Col(
                    self.render_actions(checkout),
                    span=3,
                ),
            ],
            style={"border-bottom": "1px solid #e1e1e1"},
        )

    def render(self, checkouts, cases_information):
        return dmc.Stack(
            [
                self.render_header(),
            ]
            + [
                self.render_row(checkout, cases_information)
                for checkout in checkouts
            ]
        )


def layout(payment_id, **kwargs):
    payment_service = PaymentService()
    if payment_id is not None and payment_id != "none":
        payment = payment_service.get_item(payment_id)

    else:
        starting_after = kwargs.get("starting_after")
        ending_before = kwargs.get("ending_before")
        checkouts = payment_service.get_last_checkouts(
            starting_after=starting_after, ending_before=ending_before
        )
        first_checkout = payment_service.get_last_checkouts(limit=1)

        cases_service = CasesService()
        billings_service = BillingsService()
        cases_details = []

        for checkout_single in checkouts:
            cases = cases_service.get_items(payment_id=checkout_single.id)
            billing = billings_service.get_single_item(checkout_single.id)
            if billing is not None:
                checkout_single["billing"] = billing.model_dump()
            else:
                checkout_single["billing"] = {}
            if len(cases) > 0:
                checkout_single["cases"] = cases
            else:
                checkout_single["cases"] = []

            cases_details += (
                get_custom_fields(checkout_single, "tickets")
                .replace(" ", "")
                .replace("#", "")
                .split(",")
                if get_custom_fields(checkout_single, "tickets") is not None
                else []
            )

        # Split cases into 30 cases per request
        cases_list = []
        for i in range(0, len(cases_details), 30):
            cases_list += get_many_cases(cases_details[i : i + 30])

        cases_information = {
            case.case_id: CaseDynamicFields().update(case, {})
            for case in cases_list
        }

        payments_table = PaymentsTable()
        if checkouts:
            starting_after_link = checkouts[-1].id
            ending_before_link = checkouts[0].id
        return dmc.Card(
            dmc.Stack(
                [
                    dmc.Group(
                        [
                            dmc.Text("Payments", size="xl"),
                            dmc.Text("Recent Payments", size="sm"),
                        ]
                    ),
                    dmc.Drawer(
                        children=[
                            dmc.Stack(
                                [
                                    dmc.Text("Attach this payment to a case"),
                                    dmc.Text("Select case"),
                                    dcc.Store(
                                        id="case-attach-select-details-store",
                                    ),
                                    dmc.LoadingOverlay(
                                        dmc.MultiSelect(
                                            id="case-attach-select",
                                            searchable=True,
                                        ),
                                    ),
                                    html.Div(
                                        id="case-attach-select-output",
                                    ),
                                    dmc.Button(
                                        "Attach",
                                        color="dark",
                                        id="case-attach-payment-button",
                                    ),
                                    dmc.LoadingOverlay(
                                        id="case-attach-select-details",
                                    ),
                                ],
                                spacing="xs",
                            ),
                        ],
                        id="case-attach-modal",
                        zIndex=10000,
                        position="right",
                        padding="md",
                        size="55%",
                    ),
                    payments_table.render(checkouts, cases_information),
                    dmc.Group(
                        [
                            html.A(
                                dmc.Button(
                                    "Load previous",
                                    leftIcon=DashIconify(
                                        icon="teenyicons:arrow-left-outline"
                                    ),
                                    color="dark",
                                    size="sm",
                                ),
                                hidden=(
                                    True
                                    if ending_before_link
                                    == first_checkout[0].id
                                    else False
                                ),
                                href=f"/manage/payments/none?ending_before={ending_before_link}",
                            ),
                            html.A(
                                dmc.Button(
                                    "Load more",
                                    rightIcon=DashIconify(
                                        icon="teenyicons:arrow-right-outline"
                                    ),
                                    color="dark",
                                    size="sm",
                                ),
                                href=f"/manage/payments/none?starting_after={starting_after_link}",
                                hidden=(
                                    True if len(checkouts) < 30 else False
                                ),
                            ),
                        ],
                        position="left",
                    ),
                ]
            )
        )
