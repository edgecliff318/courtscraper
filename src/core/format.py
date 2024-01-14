from datetime import datetime


def humanize_phone(phone):
    try:
        # Convert +15555555555 to +1 (555) 555-5555
        # Check if the format is correct
        if len(phone) != 12:
            return phone
        return (
            phone[:2] + " (" + phone[2:5] + ") " + phone[5:8] + "-" + phone[8:]
        )
    except Exception:
        return phone


def timestamp_to_date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
