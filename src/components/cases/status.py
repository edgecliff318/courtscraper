case_statuses = {
    "filed": {
        "value": "filed",
        "label": "Case Filed on casenet",
        "color": "gray",
    },
    "paid": {
        "value": "paid",
        "label": "Client Paid",
        "color": "green",
    },
    "eoa": {
        "value": "eoa",
        "label": "Entry of Appearance",
        "color": "orange",
    },
    "rev_int": {
        "value": "rev_int",
        "label": "Internal Review",
        "color": "yellow",
    },
    "def_dev": {
        "value": "def_dev",
        "label": "Review with the client",
        "color": "yellow",
    },
    "rec_rfr": {
        "value": "rec_rfr",
        "label": "RFR Filing",
        "color": "orange",
    },
    "rec_rec": {
        "value": "rec_rec",
        "label": "Recommendation Received",
        "color": "lime",
    },
    "rec_rej": {
        "value": "rec_rej",
        "label": "Recommendation Rejected",
        "color": "red",
    },
    "rec_del": {
        "value": "rec_del",
        "label": "Recommendation Delayed",
        "color": "pink",
    },
    "rec_rev": {
        "value": "rec_rev",
        "label": "Recommendation Review",
        "color": "yellow",
    },
    "rec_prop": {
        "value": "rec_prop",
        "label": "Recommendation Proposed to Client",
        "color": "green",
    },
    "rec_sig": {
        "value": "rec_sig",
        "label": "Recommendation pending signature",
        "color": "orange",
    },
    "rec_sub": {
        "value": "rec_sub",
        "label": "Recommendation to submit to court",
        "color": "orange",
    },
    "rec_sub_rev": {
        "value": "rec_sub_rev",
        "label": "Recommendation Submission under Review by the Court",
        "color": "orange",
    },
    "app": {
        "value": "app",
        "label": "Court Appearance Required",
        "color": "red",
    },
    "close": {
        "value": "close",
        "label": "Close Case on Portal",
        "color": "lime",
    },
}


def get_case_status_color(status: str | None):
    if status is None:
        return "gray"
    return case_statuses[status]["color"]
