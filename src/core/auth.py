import time
from os import environ as env
from urllib.parse import quote_plus, urlencode

import flask
from authlib.integrations.flask_client import OAuth
from flask import redirect, session, url_for

from src.core.config import get_settings

settings = get_settings()


class AdvancedAuth(object):
    def __init__(self, app, authorization_hook=None, _overwrite_index=True):
        self.app = app
        self._index_view_name = app.config["routes_pathname_prefix"]

        if _overwrite_index:
            self._overwrite_index()
            self._protect_views()
        self._index_view_name = app.config["routes_pathname_prefix"]
        self._auth_hooks = [authorization_hook] if authorization_hook else []

        self.app.server.config["SECRET_KEY"] = settings.SECRET_KEY

        self.oauth = OAuth(self.app.server)
        self.oauth.register(
            "auth0",
            client_id=settings.AUTH0_CLIENT_ID,
            client_secret=settings.AUTH0_CLIENT_SECRET,
            api_base_url=f"https://{settings.AUTH0_DOMAIN}",
            access_token_url=f"https://{settings.AUTH0_DOMAIN}/oauth/token",
            authorize_url=f"https://{settings.AUTH0_DOMAIN}/authorize",
            callback_url=settings.REDIRECT_URI,
            server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
            audience=settings.AUTH0_AUDIENCE,
            client_kwargs={
                "scope": "openid profile email",
            },
        )
        self.auth0 = self.oauth.auth0

        app.server.add_url_rule(
            settings.LOGIN_URL, view_func=self.login, methods=["GET"]
        )

        app.server.add_url_rule(
            settings.LOGOUT_URL, view_func=self.logout, methods=["GET"]
        )

        app.server.add_url_rule(
            "/callback",
            view_func=self.callback,
            methods=["GET", "POST"],
        )

    def _overwrite_index(self):
        original_index = self.app.server.view_functions[self._index_view_name]

        self.app.server.view_functions[self._index_view_name] = self.index_auth_wrapper(
            original_index
        )

    def _protect_views(self):
        for view_name, view_method in self.app.server.view_functions.items():
            if view_name != self._index_view_name:
                self.app.server.view_functions[view_name] = self.auth_wrapper(
                    view_method
                )

    def login(self):
        if self.auth0 is None:
            return redirect(settings.LOGIN_URL)

        return self.auth0.authorize_redirect(
            redirect_uri=url_for("callback", _external=True)
        )

    def logout(self):
        session.clear()
        # TODO: Use url joins instead of all of this
        return redirect(
            "https://"
            + settings.AUTH0_DOMAIN
            + "/v2/logout?"
            + urlencode(
                {
                    "client_id": env.get("AUTH0_CLIENT_ID"),
                },
                quote_via=quote_plus,
            )
        )

    def callback(self):
        """Callback handler"""
        if self.auth0 is None:
            return redirect(settings.LOGIN_URL)

        try:
            token = self.auth0.authorize_access_token()
        except Exception:
            return redirect(settings.LOGIN_URL)

        resp = self.auth0.get("userinfo")
        userinfo = resp.json()

        session["access_token"] = token["access_token"]
        session["created_at"] = time.time()
        session["expires_in"] = token["expires_in"]

        session[settings.JWT_PAYLOAD] = userinfo
        session[settings.PROFILE_KEY] = {
            "user_id": userinfo["sub"],
            "name": userinfo["name"],
            "picture": userinfo["picture"],
        }
        return redirect("/")

    def is_authorized(self) -> bool:
        """Verify the token is valid"""
        if flask.request.path == settings.CALLBACK_URL:
            return True
        token = session.get("access_token", None)
        if token is None:
            return False

        expires_in = session.get("expires_in", None)
        created_at = session.get("created_at", None)
        if expires_in is None or created_at is None:
            return False

        time_left = expires_in - ((time.time() - created_at) / 60)
        if time_left <= 0:
            return False

        return True

    def login_request(self):
        return redirect(settings.LOGIN_URL)

    def auth_wrapper(self, f):
        def wrap(*args, **kwargs):
            if not self.is_authorized():
                return self.login_request()
            response = f(*args, **kwargs)
            return response

        return wrap

    def index_auth_wrapper(self, original_index):
        def wrap(*args, **kwargs):
            if self.is_authorized():
                return original_index(*args, **kwargs)
            else:
                return self.login_request()

        return wrap
