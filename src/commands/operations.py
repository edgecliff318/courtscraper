import logging

from src.loader.mycase import MyCase

logger = logging.Logger(__name__)


def sync_with_mycase():
    mycase = MyCase(url="", password="", username="")

    mycase.login()
