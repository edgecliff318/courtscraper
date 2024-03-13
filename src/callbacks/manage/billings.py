import logging
from ast import In

import dash
import dash_mantine_components as dmc
from dash import ALL, MATCH, Input, Output, State, callback, html

from src.components.cases import status
from src.connectors.payments import PaymentService, get_custom_fields
from src.core.config import get_settings
from src.core.dynamic_fields import CaseDynamicFields
from src.core.participants import attach_participants
from src.models.billings import Billing
from src.pages import leads
from src.services import cases
from src.services import leads as leads_service
from src.services.billings import BillingsService
from src.services.cases import CasesService

logger = logging.getLogger(__name__)
settings = get_settings()


def get_case_text(case):
    charges = case.charges
    charges_text = ""
    for charge in charges:
        charges_text += f"{charge.get('charge_filingdate')} - {charge.get('charge_description')}"

    case_data = case.model_dump()
    case_data = CaseDynamicFields().update(case, case_data)
    return (
        f"{case.case_id} {case.first_name} {case.middle_name} {case.last_name} - {case.birth_date} -"
        f" {charges_text} - Court: {case_data.get('court_date')} at {case_data.get('court_time')} "
    )


@callback(
    Output("case-attach-modal", "opened"),
    Output("case-attach-select", "value"),
    Output("case-attach-select-details-store", "data"),
    Input({"type": "case-attach-button", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def attach_button_click(n_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, False, dash.no_update
    else:
        button_id = ctx.triggered_id
        if not isinstance(button_id, dict):
            return dash.no_update, False, dash.no_update
        if button_id.get("type") == "case-attach-button":
            checkout_id = button_id.get("index")
            cases_service = CasesService()
            payment_service = PaymentService()
            checkout_single = payment_service.get_checkout(checkout_id)
            cases = cases_service.get_items(payment_id=checkout_single.id)

            attached_cases = [case.case_id for case in cases]

            data = {
                "checkout_id": checkout_id,
                "attached_cases": attached_cases,
            }

            if not attached_cases:
                attached_cases = get_custom_fields(checkout_single, "tickets")

            return (
                True,
                attached_cases,
                data,
            )
        return dash.no_update, False, dash.no_update


@callback(
    Output("case-attach-select", "data"),
    Output("case-attach-select", "select-error"),
    Input("case-attach-select", "searchValue"),
    Input("case-attach-select", "value"),
)
def case_select_data(search_value, value):
    if value is None or value == "":
        return dash.no_update, dash.no_update

    trigger = dash.callback_context.triggered[0]["prop_id"]
    search_cases = []
    if trigger == "case-attach-select.value":
        if isinstance(value, str):
            value = [value]
        if value:
            search_cases = cases.get_many_cases(value)
    elif trigger == "case-attach-select.searchValue":
        search_cases = cases.search_cases(search_value)

    if len(search_cases) == 0:
        return [
            {
                "label": "No cases found",
                "value": "no-cases",
            },
        ], "No cases found"
    return [
        {
            "label": get_case_text(c),
            "value": c.case_id,
        }
        for c in search_cases
    ], ""


@callback(
    Output({"type": "case-status-select-output", "index": MATCH}, "children"),
    Input({"type": "case-status-select", "index": MATCH}, "value"),
    prevent_initial_call=True,
)
def update_case_status(value):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, False, dash.no_update
    else:
        button_id = ctx.triggered_id
        if not isinstance(button_id, dict):
            return dash.no_update, False, dash.no_update
        if button_id.get("type") == "case-status-select":
            billings_service = BillingsService()
            checkout_id = button_id.get("index")
            billing_item = billings_service.get_single_item(checkout_id)
            if billing_item is None:
                billing_item = billings_service.set_item(
                    checkout_id,
                    Billing(
                        billing_id=checkout_id, status=value, customer_id=""
                    ),
                )
            else:
                billings_service.patch_item(checkout_id, {"status": value})
            return dmc.Alert(
                "Updated",
                color="green",
                duration=3000,
            )


@callback(
    Output("case-attach-select-details", "children"),
    Input("case-attach-payment-button", "n_clicks"),
    Input("case-attach-select", "value"),
    State("case-attach-select-details-store", "data"),
    prevent_initial_call=True,
)
def attach_select_details(n_clicks, value, data):
    if value is None or value == "":
        return dash.no_update

    ctx = dash.callback_context

    if ctx.triggered and ctx.triggered_id == "case-attach-payment-button":
        cases_service = CasesService()
        if isinstance(value, str):
            value = [value]

        if value is None or value == "":
            return dmc.Alert(
                "No cases selected",
                color="red",
            )

        checkout_details = PaymentService().get_checkout(
            data.get("checkout_id")
        )
        customer_details = checkout_details.get("customer_details", {})

        for case_id in value:
            cases_service.patch_item(
                case_id,
                {
                    "payment_id": data.get("checkout_id"),
                    "phone": customer_details.get("phone"),
                    "email": customer_details.get("email"),
                    "status": "paid",
                },
            )

            leads_service.patch_lead(
                case_id,
                phone=customer_details.get("phone"),
                email=customer_details.get("email"),
                status="won",
            )

            attach_participants(case_id)

        return dmc.Stack(
            [
                dmc.Alert(
                    "Cases attached and updated",
                    color="green",
                ),
                dmc.Text("Attached Cases"),
                dmc.Group(
                    [
                        html.A(
                            f"{case}",
                            href=f"/manage/cases/{case}",
                            target="_blank",
                        )
                        for case in value
                    ]
                ),
            ]
        )
    elif ctx.triggered and ctx.triggered_id == "case-attach-select":
        return dmc.Stack(
            [
                dmc.Text("Attached Cases"),
                dmc.Group(
                    [
                        html.A(
                            f"{case}",
                            href=f"/manage/cases/{case}",
                            target="_blank",
                        )
                        for case in data.get("attached_cases")
                    ]
                ),
            ]
        )
    return dash.no_update
