from src.core.base import BaseService
from src.models import stats


class SalesService(BaseService):
    collection_name = "sales"
    serializer = stats.Sales


if __name__ == "__main__":
    import pandas as pd

    sales = SalesService()

    # Read the dataframe
    df = pd.read_csv("sales.csv")

    # Parse and insert
    df["customer_id"] = "ttd"

    df["id"] = df["customer_id"].map(lambda x: f"{x}_") + df["date"]

    df["count"] = df["count"].fillna(0).astype(int)
    df["amount"] = df["amount"].fillna(0.0).astype(float)

    for index, row in df.iterrows():
        print(row["id"])
        sales.set_item(row["id"], stats.Sales(**row.to_dict()))
