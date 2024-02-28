import logging

import dash
import dash.html as html
import dash_mantine_components as dmc
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


def handle_send_message(prefix):
    @callback(
        Output(f"{prefix}-modal-content-sending-status", "children"),
        Input(f"{prefix}-send-all", "n_clicks"),
        Input(f"{prefix}-modal-content", "children"),
        State(f"{prefix}-memory", "data"),
        State("lead-single-message-modal", "value"),
        State("lead-media-enabled-modal", "value"),
        running=[
            (Output(f"{prefix}-send-all", "disabled"), True, False),
            (Output(f"{prefix}-all-cancel", "disabled"), False, True),
        ],
        cancel=[Input(f"{prefix}-all-cancel", "n_clicks")],
    )
    def send_many_message(*args, **kwargs):
        if ctx.triggered_id == f"{prefix}-send-all":
            df = ctx.states[f"{prefix}-memory.data"]["df"] or []
            template_msg = ctx.states["lead-single-message-modal.value"] or ""
            include_case_copy = (
                ctx.states["lead-media-enabled-modal.value"] or False
            )
            contacted_phone_nbs = set()
            skipped = False
            df = [{k.lower(): v for k, v in case.items()} for case in df]
            for case in df:
                # Dict keys to lower and replace spaces with underscores
                case = {
                    k.lower().replace(" ", "_"): v for k, v in case.items()
                }

                # first_name and last_name should be capitalized
                case["first_name"] = case.get("first_name", "").capitalize()
                case["last_name"] = case.get("last_name", "").capitalize()

                case_id = case.get("case_index")
                try:
                    # TODO: add a check validation of template sending SMS with the case data by Twilio
                    sms_message = template_msg.format(**case)
                    for phone in case["phone"].split(", "):
                        if phone in contacted_phone_nbs:
                            continue
                        try:
                            message_status = messages.send_message(
                                case_id,
                                sms_message,
                                phone,
                                media_enabled=include_case_copy,
                                force_send=prefix == "conversation"
                                or prefix == "monitoring"
                                or prefix == "communication",
                            )
                            if (
                                message_status == "queued"
                                or message_status == "accepted"
                            ):
                                leads.update_lead_status(case_id, "contacted")

                            elif message_status == "skipped":
                                logger.info(
                                    f"Skipping message to {phone} as it was recently sent. Use --force to send anyway"
                                )
                            else:
                                logger.error(
                                    f"An error occurred while sending the message. {message_status}"
                                )
                            contacted_phone_nbs.add(phone)
                        except Exception as e:
                            if "skipped" in str(e).lower():
                                skipped = True
                            else:
                                raise e

                except Exception as e:
                    logger.error(
                        f"An error occurred while sending the message. {e}"
                    )
                    message = (
                        f"An error occurred while sending the message {e}"
                    )
                    return dmc.Alert(
                        message,
                        color="danger",
                        className="mt-2",
                    )
            if skipped:
                message = "Messages sent successfully. Some messages were skipped as they were recently sent"
                return dmc.Alert(
                    message,
                    color="warning",
                    className="mt-2",
                )
            else:
                message = "Messages sent successfully"
                return dmc.Alert(
                    message,
                    color="success",
                    className="mt-2",
                )

        return ""

    @callback(
        Output(f"{prefix}-modal-content-generate-letters-status", "children"),
        Input(f"{prefix}-generate-letters", "n_clicks"),
        Input(f"{prefix}-modal-content", "children"),
        State(f"{prefix}-memory", "data"),
    )
    def generate_many_letters(*args, **kwargs):
        if ctx.triggered_id == f"{prefix}-generate-letters":
            df = ctx.states[f"{prefix}-memory.data"]["df"] or []
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
        Output(f"{prefix}-modal-lead-status-update-status", "children"),
        Input(f"{prefix}-modal-lead-status-update", "n_clicks"),
        State(f"{prefix}-memory", "data"),
        State(f"{prefix}-modal-lead-status", "value"),
    )
    def update_many_lead_status(*args, **kwargs):
        if ctx.triggered_id == f"{prefix}-modal-lead-status-update":
            df = ctx.states[f"{prefix}-memory.data"]["df"] or []
            case_ids = [c.get("case_index") for c in df]
            status = (
                ctx.states[f"{prefix}-modal-lead-status.value"] or "contacted"
            )

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


for prefix in ["outbound", "monitoring", "conversation", "communication"]:
    handle_send_message(prefix)
