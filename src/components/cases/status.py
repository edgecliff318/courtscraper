case_statuses = {
    "filed": {
        "value": "filed",
        "label": "Case Filed on casenet",
        "color": "gray",
        "section": None,
    },
    "paid": {
        "value": "paid",
        "label": "Client Paid",
        "color": "green",
        "section": "todo",
    },
    "eoa": {
        "value": "eoa",
        "label": "Entry of Appearance",
        "color": "orange",
        "section": "pending",
    },
    "continuance": {
        "value": "continuance",
        "label": "Motion for Continuance Requested",
        "color": "orange",
        "section": "pending",
        "show": False,
    },
    "court": {
        "value": "court",
        "label": "Court Submission",
        "color": "orange",
        "section": "pending",
        "show": False,
    },
    "court_response": {
        "value": "court",
        "label": "Court Submission",
        "color": "orange",
        "section": "pending",
        "show": False,
    },
    "customer": {
        "value": "customer",
        "label": "Customer Request",
        "color": "orange",
        "section": "pending",
        "show": False,
    },
    "rev_int": {
        "value": "rev_int",
        "label": "Internal Review",
        "color": "yellow",
        "section": "todo",
    },
    "def_dev": {
        "value": "def_dev",
        "label": "Review with the client",
        "color": "yellow",
        "section": "todo",
    },
    "rec_rfr": {
        "value": "rec_rfr",
        "label": "RFR Filing",
        "color": "orange",
        "section": "pending",
    },
    "rec_rec": {
        "value": "rec_rec",
        "label": "Recommendation Received",
        "color": "lime",
        "section": "todo",
    },
    "rec_rej": {
        "value": "rec_rej",
        "label": "Recommendation Rejected",
        "color": "red",
        "section": "todo",
        "show": False,
    },
    "rec_del": {
        "value": "rec_del",
        "label": "Recommendation Delayed",
        "color": "pink",
        "section": "todo",
        "show": False,
    },
    "rec_rev": {
        "value": "rec_rev",
        "label": "Recommendation Review",
        "color": "yellow",
        "section": "todo",
    },
    "rec_prop": {
        "value": "rec_prop",
        "label": "Recommendation Proposed to Client",
        "color": "green",
        "section": "pending",
    },
    "rec_sig": {
        "value": "rec_sig",
        "label": "Recommendation pending signature",
        "color": "orange",
        "section": "pending",
    },
    "rec_sub": {
        "value": "rec_sub",
        "label": "Recommendation to submit to court",
        "color": "orange",
        "section": "todo",
    },
    "rec_sub_rev": {
        "value": "rec_sub_rev",
        "label": "Recommendation Submission under Review by the Court",
        "color": "orange",
        "section": "pending",
    },
    "app": {
        "value": "app",
        "label": "Court Appearance Required",
        "color": "red",
        "section": "pending",
        "show": False,
    },
    "close": {
        "value": "close",
        "label": "Close Case on Portal",
        "color": "lime",
        "section": "closed",
    },
}


def get_case_status_color(status: str | None):
    if status is None:
        return "gray"
    return case_statuses[status]["color"]
