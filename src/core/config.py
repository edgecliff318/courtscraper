import os
import pathlib
from functools import lru_cache
from typing import ClassVar, Dict

from pydantic_settings import BaseSettings, SettingsConfigDict

COLORS_MAPPING = {
    "AL": "#FF5733",
    "AK": "#33FF57",
    "AZ": "#3357FF",
    "AR": "#FF33FB",
    "CA": "#57FF33",
    "CO": "#F833FF",
    "CT": "#33FFF3",
    "DE": "#FFC433",
    "FL": "#33FFC4",
    "GA": "#FF5733",
    "HI": "#FF33A5",
    "ID": "#33A5FF",
    "IL": "#FF3333",
    "IN": "#33FF57",
    "IA": "#FF5733",
    "KS": "#3357FF",
    "KY": "#FF33FB",
    "LA": "#57FF33",
    "ME": "#F833FF",
    "MD": "#33FFF3",
    "MA": "#FFC433",
    "MI": "#33FFC4",
    "MN": "#FF5733",
    "MS": "#FF33A5",
    "MO": "#33A5FF",
    "MT": "#FF3333",
    "NE": "#33FF57",
    "NV": "#FF5733",
    "NH": "#3357FF",
    "NJ": "#FF33FB",
    "NM": "#57FF33",
    "NY": "#F833FF",
    "NC": "#33FFF3",
    "ND": "#FFC433",
    "OH": "#33FFC4",
    "OK": "#FF5733",
    "OR": "#FF33A5",
    "PA": "#33A5FF",
    "RI": "#FF3333",
    "SC": "#33FF57",
    "SD": "#FF5733",
    "TN": "#3357FF",
    "TX": "#6610F2",
    "UT": "#FF33FB",
    "VT": "#57FF33",
    "VA": "#F833FF",
    "WA": "#33FFF3",
    "WV": "#FFC433",
    "WI": "#33FFC4",
    "WY": "#FF5733",
    # Case Sources
    "IL Cook County": "#FF5733",
    "MO Casenet": "#33FF57",
    "MO Highway Patrol": "#3357FF",
    # leads status
    "not_prioritized": "#FF5733",
    "not_contacted": "#FFC300",
    "contacted": "#DAF7A6",
    "responded": "#28C76F",
    "not_found": "#C70039",
    "processing_error": "#900C3F",
    "not_valid": "#581845",
    "new": "#007BFF",
    "processing": "#FFC107",
    "stop": "#FF9F43",
    # calls
    "total": "#6610F2",
    "incoming": "#28C76F",
    "outgoing": "#053342",
}


class Settings(BaseSettings):
    """

    BaseSettings, from Pydantic, validates the data so that when we create an instance of Settings,
    environment and testing will have types of str and bool, respectively.

    Parameters:


    Returns:
    instance of Settings

    """

    VERSION: str = "2.5.0"
    DESCRIPTION: str = "Fubloo"
    PROJECT_NAME: str = "Fubloo"

    # DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOGGING_LEVEL: str = os.getenv("LOGGING_LEVEL", "INFO")

    # Configuration
    CONFIG_FILENAME: str = os.getenv("CONFIG_FILENAME", "config.json")
    CONFIG_TEST_FILENAME: str = os.getenv(
        "CONFIG_TEST_FILENAME", "config_test.json"
    )

    # Root Path
    # ROOT_PATH: pathlib.Path = pathlib.Path(__file__).parent.parent.parent
    ROOT_PATH: ClassVar[pathlib.Path] = pathlib.Path(
        os.getenv("ROOT_PATH", pathlib.Path(__file__).parent.parent.parent)
    )

    DATA_PATH: pathlib.Path = pathlib.Path(
        os.getenv("DATA_PATH", ROOT_PATH.joinpath("data"))
    ).resolve()
    CONFIG_PATH: pathlib.Path = pathlib.Path(
        os.getenv("CONFIG_PATH", ROOT_PATH.joinpath("configuration"))
    ).resolve()
    UPLOAD_PATH: pathlib.Path = pathlib.Path(
        os.getenv("UPLOAD_PATH", ROOT_PATH.joinpath("data", "upload"))
    ).resolve()
    OUTPUT_PATH: pathlib.Path = pathlib.Path(
        os.getenv("OUTPUT_PATH", ROOT_PATH.joinpath("data", "output"))
    ).resolve()

    # Template
    TEMPLATE: str = os.getenv("TEMPLATE", "plotly")

    # Case Net
    CASE_NET_URL: str = os.getenv(
        "CASE_NET_URL", "https://www.courts.mo.gov/cnet"
    )
    CASE_NET_USERNAME: str = os.getenv("CASE_NET_USERNAME", "smeyer4040")
    CASE_NET_PASSWORD: str = os.getenv("CASE_NET_PASSWORD", "MASdorm1993!MAS")

    # Production
    PRODUCTION: bool = os.getenv("PRODUCTION", "true").lower() == "true"

    # Site URL
    SITE_URL: str = os.getenv("SITE_URL", "https://app.fubloo.com")

    # Twilio
    TWILIO_ACCOUNT_SID: str = os.getenv(
        "TWILIO_ACCOUNT_SID", "ACc675e16f153269ab1d8d4c5f3ae2ce8a"
    )
    TWILIO_AUTH_TOKEN: str = os.getenv(
        "TWILIO_AUTH_TOKEN", "095c5fb2a0eea27b7c4e46c1fd12cf45"
    )
    TWILIO_MESSAGE_SERVICE_SID: str = os.getenv(
        "TWILIO_MESSAGE_SERVICE_SID", "MG2b12454f63e7ee70aaac25dd4b333898"
    )

    # API_KEY
    API_KEY: str = os.getenv("API_KEY", "KEF83291BF01JFJ238F")

    # AUTH0 Configuration
    AUTH0_DOMAIN: str = os.getenv("AUTH0_DOMAIN", "fubloo.us.auth0.com")
    AUTH0_AUDIENCE: str = os.getenv(
        "AUTH0_AUDIENCE", "https://fubloo.us.auth0.com"
    )
    AUTH0_CLIENT_ID: str = os.getenv("AUTH0_CLIENT_ID", "")
    AUTH0_CLIENT_SECRET: str = os.getenv("AUTH0_CLIENT_SECRET", "")
    AUTH0_CALLBACK_URL: str = os.getenv(
        "AUTH0_CALLBACK_URL", "http://localhost:8000/callback"
    )
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "")

    # flask
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret")
    SESSION_COOKIE_NAME: str = os.getenv("SESSION_COOKIE_NAME", "")
    SESSION_COOKIE_SECURE: bool = (
        os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    )
    SESSION_COOKIE_HTTPONLY: bool = (
        os.getenv("SESSION_COOKIE_HTTPONLY", "true").lower() == "true"
    )

    # pages
    LOGIN_URL: str = os.getenv("LOGIN_URL", "/login")
    LOGOUT_URL: str = os.getenv("LOGOUT_URL", "/logout")
    CALLBACK_URL: str = os.getenv("CALLBACK_URL", "/callback")
    REDIRECT_URI: str = os.getenv(
        "REDIRECT_URI", "http://localhost:8000/callback"
    )

    # keys session
    JWT_PAYLOAD: str = os.getenv("JWT_PAYLOAD", "jwt_payload")
    PROFILE_KEY: str = os.getenv("PROFILE_KEY", "profile")

    # firebase configuration
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        CONFIG_PATH.joinpath(
            "fubloo-1b0e8-firebase-adminsdk-5j6zr-6b8d8d1c0b.json"
        )
    )

    # llm
    OPENAI_API_KEY: str = os.getenv(
        "OPENAI_API_KEY", "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"
    )

    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "fubloo-data")

    # Ticket Configuration
    TICKET_DISCLAIMER_TEXT: str = os.getenv(
        "TICKET_DISCLAIMER_TEXT",
        "This citation was obtained through the Missouri Case Database. Disregard this solicitation if you have already engaged a lawyer in connection with the legal matter referred to in this solicitation. You may wish to consult your lawyer or another lawyer instead of us. The exact nature of your legal situation will depend on many facts not known to us at this time. You should understand that the advice and information in this solicitation is general and that your own situation may vary. This statement is required by rule of the Supreme Court of Missouri.",
    )

    # Beenverified Configuration
    BEEN_VERIFIED_EMAIL: str = os.getenv(
        "BEEN_VERIFIED_EMAIL", "ttdwoman@gmail.com"
    )
    BEEN_VERIFIED_PASSWORD: str = os.getenv(
        "BEEN_VERIFIED_PASSWORD", "0TTD2023!"
    )

    # Gotenberg Configuration
    GOTENBERG_URL: str = os.getenv("GOTENBERG_URL", "http://localhost:58864")

    # Selenium Service
    SELENIUM_STANDALONE_URL: str = os.getenv(
        "SELENIUM_STANDALONE_URL", "http://localhost:4444/wd/hub"
    )

    # GOOGLE GMAIL API
    GOOGLE_GMAIL_API_CLIENT_SECRET: str = os.getenv(
        "GOOGLE_GMAIL_API_CLIENT_SECRET",
        "configuration/client_secret_330426662227-qi4asjra43jl23obg4944d158t9khpeq.apps.googleusercontent.com.json",
    )

    GOOGLE_GMAIL_API_REDIRECT_URI: str = os.getenv(
        "GOOGLE_GMAIL_API_REDIRECT_URI",
        "http://localhost:3000/connectors/gmail",
    )
    # Intercom Config
    INTERCOM_API_KEY: str = os.getenv(
        "INTERCOM_API_KEY",
        "dG9rOjVkMzgxZDY2XzQxYjFfNDRmM19hZGE3XzAyODc4YzU4MzgxOToxOjA=",
    )

    # Stripe Config
    STRIPE_SECRET_KEY: str = os.getenv(
        "STRIPE_SECRET_KEY",
        "sk_test_51N4NCnDIQFEv26lp5VKLRnKZF44qvYYeQfcflNJHd6qPowZWW5QQHcvBWraNoPtp5JQsjDrGm7yzbWisCKlUlwZ100LpOEoBD1",
    )

    # Intercom Sender
    INTERCOM_SENDER_ID: str = os.getenv(
        "INTERCOM_SENDER_ID", "cooper@tickettakedown.com"
    )

    # SMS Email Sender
    SMS_EMAIL_SENDER_ID: str = os.getenv(
        "SMS_EMAIL_SENDER_ID", "ttdwoman@gmail.com"
    )

    # CloudTalk Config
    CLOUDTALK_API_KEY: str = os.getenv(
        "CLOUDTALK_API_KEY", "QAPAMJXG6CYT2SLOVRWQW5B"
    )
    CLOUDTALK_API_SECRET: str = os.getenv(
        "CLOUDTALK_API_SECRET", "ebsKYEo,Lt9GjAMIp3hx0miUZCuS8nBygNcqXkT1F24_R"
    )

    SENTRY_ENV: str = os.getenv(
        "SENTRY_ENV",
        "local",
    )

    SENTRY_DSN: str = os.getenv(
        "SENTRY_DSN",
        "https://ec102608c1c364997fb5e984240b8127@o4506412785795072.ingest.us.sentry.io/4507226899546112",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    colors_mapping: Dict = COLORS_MAPPING


@lru_cache
def get_settings():
    return Settings()
