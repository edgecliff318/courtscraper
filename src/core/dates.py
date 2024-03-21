import pandas as pd


def get_continuance_date(court_date):
    # Check the type of court_date to make sure the code works in all situations
    if isinstance(court_date, str):
        court_date = pd.to_datetime(court_date)

    if not isinstance(court_date, pd.Timestamp):
        raise ValueError(
            "court_date must be a pandas Timestamp or a string that can be converted to a Timestamp"
        )

    # Get the same day next month for the same week number
    weekday = court_date.weekday()

    # Week of the month
    week_nb = court_date.day // 7 + 1

    # First day of the month
    new_date = court_date + pd.tseries.offsets.MonthBegin()

    new_month = new_date.month

    # Get the same business day next month
    new_date = new_date + pd.tseries.offsets.Week(week_nb, weekday=weekday)

    if new_date.month != new_month:
        # If there aren't enough weeks in the next month to fit an Nth weekday, just use the last of that weekday
        new_date = new_date - pd.tseries.offsets.Week(1)
    return new_date
