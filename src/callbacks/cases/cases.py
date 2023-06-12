import logging

import dash
import dash.html as html
from dash import Input, Output, State, callback, ctx

from src.components.toast import build_toast
from src.core.config import get_settings
from src.services import leads, letters, messages

logger = logging.Logger(__name__)

settings = get_settings()


def send_message(case_id, sms_button, sms_message, phone, media_enabled):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "lead-single-send-sms-button":
        if case_id is None:
            return "No case ID found"
        error = False
        message = ""
        try:
            case_id = str(case_id)
        except Exception:
            message = "Case ID must be a number"
            error = True

        if not error:
            try:
                message = messages.send_message(
                    case_id, sms_message, phone, media_enabled=media_enabled
                )
            except Exception as e:
                message = f"An error occurred while sending the message. {e}"
                error = True

        return message


@callback(
    Output("modal-content-sending-status", "children"),
    Input("send-all-cases", "n_clicks"),
    Input("modal-content", "children"),
    State("memory", "data"),
    State("lead-single-message-modal", "value"),
    State("lead-media-enabled-modal", "value"),
    running=[
        (Output("send-all-cases", "disabled"), True, False),
        (Output("send-all-cases-cancel", "disabled"), False, True),
    ],
    cancel=[Input("send-all-cases-cancel", "n_clicks")],
)
def send_many_message(*args, **kwargs):
    if ctx.triggered_id == "send-all-cases":
        df = ctx.states["memory.data"]["df"] or []
        template_msg = ctx.states["lead-single-message-modal.value"] or ""
        include_case_copy = (
            ctx.states["lead-media-enabled-modal.value"] or False
        )
        for case in df:
            # Dict keys to lower and replace spaces with underscores
            case = {k.lower().replace(" ", "_"): v for k, v in case.items()}

            # first_name and last_name should be capitalized
            case["first_name"] = case["first_name"].capitalize()
            case["last_name"] = case["last_name"].capitalize()

            case_id = case["case_index"]
            phone = case["phone"]
            try:
                # TODO: add a check validation of template sending SMS with the case data by Twilio
                sms_message = template_msg.format(**case)
                message_status = messages.send_message(
                    case_id,
                    sms_message,
                    phone,
                    media_enabled=include_case_copy,
                )

                if message_status == "queued" or message_status == "accepted":
                    leads.update_lead_status(case_id, "contacted")

            except Exception as e:
                logger.error(
                    f"An error occurred while sending the message. {e}"
                )
                return f"An error occurred while sending the message {e}"
        return "Messages sent successfully"

    return ""


@callback(
    Output("modal-content-generate-letters-status", "children"),
    Input("generate-letters", "n_clicks"),
    Input("modal-content", "children"),
    State("memory", "data"),
)
def generate_many_latters(*args, **kwargs):
    if ctx.triggered_id == "generate-letters":
        df = ctx.states["memory.data"]["df"] or []
        case_ids = [c.get("case_index") for c in df]

        try:
            (
                media_url_envelope,
                media_url_letter,
            ) = letters.generate_many_letters(case_ids)

            leads.update_multiple_leads_status(
                case_ids=case_ids, status="mailed"
            )

            output = html.Div(
                [
                    html.H6(
                        "The zip files were generated : ",
                        className="card-title",
                    ),
                    # Small button
                    html.A(
                        "Download Envelope",
                        href=media_url_envelope,
                        target="_blank",
                        className="btn btn-primary m-1 btn-sm",
                    ),
                    html.A(
                        "Download Letter",
                        href=media_url_letter,
                        target="_blank",
                        className="btn btn-primary m-1 btn-sm",
                    ),
                    build_toast(
                        "The letter zip and envelopes zip were generated successfully",
                        "Letters and envelopes generated ✅",
                    ),
                ],
            )
            return output

        except Exception as e:
            toast = build_toast(
                "Letters could not be generated",
                f"An error occurred ❌ {e}",
                color="danger",
            )
            return toast

    return ""


@callback(
    Output("modal-lead-status-update-status", "children"),
    Input("modal-lead-status-update", "n_clicks"),
    State("memory", "data"),
    State("modal-lead-status", "value"),
)
def update_many_lead_status(*args, **kwargs):
    if ctx.triggered_id == "modal-lead-status-update":
        df = ctx.states["memory.data"]["df"] or []
        case_ids = [c.get("case_index") for c in df]
        status = ctx.states["modal-lead-status.value"] or "contacted"

        try:
            leads.update_multiple_leads_status(
                case_ids=case_ids, status=status
            )
            toast = build_toast(
                "Leads status updated successfully",
                "Leads status updated successfully ✅",
            )
            return toast

        except Exception as e:
            toast = build_toast(
                "Leads status could not be updated",
                f"An error occurred ❌ {e}",
                color="danger",
            )
            return toast

    return ""
