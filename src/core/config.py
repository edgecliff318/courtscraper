import os
import pathlib
from functools import lru_cache

from pydantic import BaseSettings


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

    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOGGING_LEVEL: str = os.getenv("LOGGING_LEVEL", "DEBUG")

    # Pathname configuration
    PATHNAME_PARAMS = dict()
    PATHNAME_PARAMS["routes_pathname_prefix"] = "/"

    # Configuration
    CONFIG_FILENAME: str = os.getenv("CONFIG_FILENAME", "config.json")
    CONFIG_TEST_FILENAME: str = os.getenv(
        "CONFIG_TEST_FILENAME", "config_test.json"
    )

    # Root Path
    ROOT_PATH = pathlib.Path(__file__).parent.parent.parent
    DATA_PATH = ROOT_PATH.joinpath("./data").resolve()
    CONFIG_PATH = ROOT_PATH.joinpath("./configuration").resolve()
    UPLOAD_PATH = ROOT_PATH.joinpath("./data/upload").resolve()
    OUTPUT_PATH = ROOT_PATH.joinpath("./data/output").resolve()

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
        "TWILIO_MESSAGE_SERVICE_SID", "MG3beed289e59b0417fc8d1c63894aa27e"
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
        "fubloo-1b0e8-firebase-adminsdk-5j6zr-6b8d8d1c0b.json",
    )

    # llm
    OPENAI_API_KEY: str = os.getenv(
        "OPENAI_API_KEY", "sk-2c2b2-2c2b2-2c2b2-2c2b2-2c2b2"
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
    GOTENBERG_URL: str = os.getenv("GOTENBERG_URL", "http://localhost:3001")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings():
    return Settings()
