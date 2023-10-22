from src.core.base import BaseService
from src.db import db
from src.models import settings


def get_settings(setting_name: str):
    settings_single = (
        db.collection("settings").document(setting_name).get().to_dict()
    )
    return settings.Settings(**settings_single)


def get_account(account_name: str):
    account_single = (
        db.collection("accounts").document(account_name).get().to_dict()
    )
    return settings.Account(**account_single)


class UserSettingsService(BaseService):
    collection_name = "userSettings"
    serializer = settings.UserSettings
