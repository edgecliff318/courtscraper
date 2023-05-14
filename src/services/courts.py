from src.db import db
from src.models import courts


def get_courts(enabled: bool = True):
    courts_list = (
        db.collection("courts").where("enabled", "==", enabled).stream()
    )
    return [courts.Court(**m.to_dict()) for m in courts_list]
