import json
import logging

import httplib2
from oauth2client.client import (
    FlowExchangeError,
    OAuth2Credentials,
    flow_from_clientsecrets,
)

from src.core.config import get_settings
from src.db import db

settings = get_settings()

logger = logging.getLogger(__name__)


CLIENTSECRETS_LOCATION = settings.GOOGLE_GMAIL_API_CLIENT_SECRET
REDIRECT_URI = settings.GOOGLE_GMAIL_API_REDIRECT_URI
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.insert",
    "https://www.googleapis.com/auth/gmail.labels",
]


class GetCredentialsException(Exception):
    """Error raised when an error occurred while retrieving credentials.

    Attributes:
       authorization_url: Authorization URL to redirect the user to in order to
                                            request offline access.
    """

    def __init__(self, authorization_url):
        """Construct a GetCredentialsException."""
        self.authorization_url = authorization_url


class CodeExchangeException(GetCredentialsException):
    """Error raised when a code exchange has failed."""


class NoRefreshTokenException(GetCredentialsException):
    """Error raised when no refresh token has been found."""


class NoUserIdException(Exception):
    """Error raised when no user ID could be retrieved."""


def get_stored_credentials(user_id):
    """Retrieved stored credentials for the provided user ID.

    Args:
        user_id: User's ID.
    Returns:
        Stored oauth2client.client.OAuth2Credentials if found, None otherwise.
    Raises:
        NotImplemented: This function has not been implemented.
    """
    credentials = db.collection("emails_credentials").document(user_id).get()
    if not credentials.exists:
        return None
    else:
        credentials_dict = credentials.to_dict()

        # Transform to OAuth2Credentials object
        credentials = OAuth2Credentials.from_json(json.dumps(credentials_dict))
        return credentials


def refresh_credentials(user_id):
    """Retrieve new credentials for the provided user.

    Args:
        user_id: User's ID.
    Returns:
        oauth2client.client.OAuth2Credentials instance containing new
        credentials.
    Raises:
        GetCredentialsException: If no refresh token could be retrieved.
    """
    credentials = get_stored_credentials(user_id)
    if credentials is None:
        raise NoRefreshTokenException(None)
    if credentials.refresh_token is None:
        raise NoRefreshTokenException(None)
    credentials.refresh(httplib2.Http())
    return credentials


def store_credentials(user_id, credentials):
    """Store OAuth 2.0 credentials in the application's database.

    This function stores the provided OAuth 2.0 credentials using the user ID as
    key.

    Args:
        user_id: User's ID.
        credentials: OAuth 2.0 credentials to store.
    Raises:
        NotImplemented: This function has not been implemented.
    """

    credentials_dict = json.loads(credentials.to_json())
    db.collection("emails_credentials").document(user_id).set(credentials_dict)


def exchange_code(authorization_code):
    """Exchange an authorization code for OAuth 2.0 credentials.

    Args:
        authorization_code: Authorization code to exchange for OAuth 2.0
                                                credentials.
    Returns:
        oauth2client.client.OAuth2Credentials instance.
    Raises:
        CodeExchangeException: an error occurred.
    """
    flow = flow_from_clientsecrets(CLIENTSECRETS_LOCATION, " ".join(SCOPES))
    flow.redirect_uri = REDIRECT_URI
    try:
        credentials = flow.step2_exchange(authorization_code)
        return credentials
    except FlowExchangeError as error:
        logging.error("An error occurred: %s", error)
        raise CodeExchangeException(None)


def get_authorization_url(email_address=None, state=None):
    """Retrieve the authorization URL.

    Args:
        email_address: User's e-mail address.
        state: State for the authorization URL.
    Returns:
        Authorization URL to redirect the user to.
    """
    flow = flow_from_clientsecrets(CLIENTSECRETS_LOCATION, " ".join(SCOPES))
    flow.params["access_type"] = "offline"
    flow.params["approval_prompt"] = "force"
    # flow.params["user_id"] = email_address
    # flow.params["state"] = state
    return flow.step1_get_authorize_url(REDIRECT_URI)


def get_credentials(user_id):
    """Get credentials from database.

    Args:
        user_id: User's ID.
    Returns:
        oauth2client.client.OAuth2Credentials instance.
    Raises:
        GetCredentialsException: If no credentials could be retrieved.
    """
    credentials = get_stored_credentials(user_id)
    if credentials and credentials.access_token_expired:
        credentials = refresh_credentials(user_id)
        store_credentials(user_id, credentials)
    return credentials
