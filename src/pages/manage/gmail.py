import logging

import dash
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify
from flask import session

from src.core.config import get_settings
from src.services import emails_auth

logger = logging.getLogger(__name__)
settings = get_settings()

dash.register_page(
    __name__, class_icon="ti ti-home", order=5, path="/connectors/gmail"
)


def layout(*args, **kwargs):
    user = session.get("profile", {}).get("name", None)
    revoke_access_card = dmc.Paper(
        [
            dmc.Text("You have authorized Gmail access"),
            html.A(
                dmc.Button(
                    "Revoke Gmail Access",
                    leftSection=DashIconify(icon="mdi:email-outline"),
                    color="red",
                    variant="filled",
                    className="mt-2",
                ),
            ),
        ],
        shadow="xs",
        p="md",
        radius="md",
    )

    get_access_card = dmc.Paper(
        [
            dmc.Text("Click the button below to authorize Gmail access"),
            html.A(
                dmc.Button(
                    "Authorize Gmail",
                    leftSection=DashIconify(icon="mdi:email-outline"),
                    variant="filled",
                    color="dark",
                    className="mt-2",
                ),
                href=emails_auth.get_authorization_url(),
            ),
        ],
        shadow="xs",
        p="md",
        radius="md",
    )

    if user is None:
        # Redirect to login page
        return dash.no_update

    # Get the code from the callback URL
    if kwargs.get("code") is not None:
        code = kwargs.get("code")
        # Exchange the code for credentials
        try:
            credentials = emails_auth.exchange_code(code)
            # Store the credentials
            emails_auth.store_credentials(user, credentials)
        except emails_auth.CodeExchangeException as error:
            message = dmc.Alert(
                [
                    dmc.Text("An error occurred during code exchange."),
                    dmc.Text(
                        "Please try to authorize the Gmail connectivity again."
                    ),
                ],
                color="red",
            )
            logger.error("An error occurred during code exchange.")
            logger.error(error)
            return dmc.Stack([message, get_access_card])

        return dmc.Stack(
            [
                dmc.Paper(
                    dmc.Text("You have successfully authorized Gmail access"),
                )
            ]
        )

    # Get the credentials for Gmail of this user
    credentials = emails_auth.get_stored_credentials(user)

    if credentials is None:
        return get_access_card
    else:
        return revoke_access_card
