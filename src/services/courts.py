from src.db import db
from src.models import courts


def get_courts(enabled: bool = True):
    courts_list = (
        db.collection("courts").where("enabled", "==", enabled).stream()
    )
    return [courts.Court(id=m.id, **m.to_dict()) for m in courts_list]


def get_single_court(court_id: str):
    court = db.collection("courts").document(court_id).get()
    if court.exists:
        return courts.Court(id=court.id, **court.to_dict())
    return None


def insert_court(court: courts.Court):
    court_dict = court.model_dump()
    court_dict["enabled"] = True
    db.collection("courts").document(court.code).set(
        {k: v for k, v in court_dict.items() if k != "id"}
    )


if __name__ == "__main__":
    # Update the courts collection
    for court in db.collection("courts").stream():
        db.collection("courts").document(court.id).update({"enabled": True})
