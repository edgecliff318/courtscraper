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

    if account_single is None:
        return None
    return settings.Account(**account_single)


def update_account(account_name: str, account: settings.Account):
    db.collection("accounts").document(account_name).set(account.model_dump())


class UserSettingsService(BaseService):
    collection_name = "userSettings"
    serializer = settings.UserSettings


class ScrapersService(BaseService):
    collection_name = "scrapers"
    serializer = settings.Scrapers
