from src.core.base import BaseService
from src.models import stats


class SalesService(BaseService):
    collection_name = "sales"
    serializer = stats.Sales


if __name__ == "__main__":
    import pandas as pd

    from src.services.leads import get_leads

    sales = SalesService()

    # Read the dataframe
    df = pd.read_csv("sales_august_12.csv")

    # Parse and insert
    df["customer_id"] = "ttd"

    df["id"] = df["customer_id"].map(lambda x: f"{x}_") + df["date"]

    df["count"] = df["count"].fillna(0).astype(int)
    df["amount"] = df["amount"].fillna(0.0).astype(float)

    #
    df["date"] = pd.to_datetime(df["date"])
    start_date = df.date.min()
    end_date = df.date.max() + pd.Timedelta(hours=23, minutes=59, seconds=59)

    # Get the leads per day
    leads = get_leads(start_date=start_date, end_date=end_date)

    leads_df = pd.DataFrame([l.model_dump() for l in leads])
    leads_df["date"] = pd.to_datetime(leads_df["case_date"])

    leads_pivot = leads_df.pivot_table(
        index="date", columns="status", values="id", aggfunc="count"
    ).fillna(0)

    leads_pivot = leads_pivot.reset_index()

    # Remove UTC
    leads_pivot["date"] = leads_pivot["date"].dt.tz_localize(None)

    # Merge the dataframes
    df = df.merge(leads_pivot, on="date", how="left")

    # Total outbound actions
    columns_to_sum = ["responded", "won", "stop", "contacted", "won"]
    df["outbound_actions_count"] = (
        df[[c for c in columns_to_sum if c in df.columns]]
        .sum(axis=1)
        .fillna(0)
    )

    # df.loc[
    #     df["outbound_actions_count"] <= df["count"], "outbound_actions_count"
    # ] = df.loc[
    #     df["outbound_actions_count"] > df["count"], "outbound_actions_count"
    # ].mean()

    for index, row in df.iterrows():
        print(row["id"])
        sales.set_item(row["id"], stats.Sales(**row.to_dict()))
