from src.db import db
from src.models import courts


def get_courts(enabled: bool = True):
    courts_list = (
        db.collection("courts").where("enabled", "==", enabled).stream()
    )
    return [courts.Court(id=m.id, **m.to_dict()) for m in courts_list]


def get_single_court(court_id: str):
    court = db.collection("courts").document(court_id).get()
    return courts.Court(**court.to_dict())


if __name__ == "__main__":
    # Update the courts collection
    for court in db.collection("courts").stream():
        db.collection("courts").document(court.id).update({"enabled": True})
