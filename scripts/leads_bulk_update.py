from rich.console import Console
from rich.progress import track

from src.db import db

console = Console()

if __name__ == "__main__":
    # Retrieve 1000 leads at a time
    last_lead = None
    exit_loop = False
    while True:
        if last_lead is not None:
            leads_list = list(
                db.collection("leads")
                .select(["phone"])
                .start_after(last_lead)
                .order_by("phone", "DESCENDING")
                .limit(100)
                .stream()
            )
        else:
            leads_list = list(
                db.collection("leads")
                .select(["phone"])
                .order_by("phone", "DESCENDING")
                .limit(100)
                .stream()
            )
        if not leads_list:
            break
        batch = db.batch()
        for lead in track(
            leads_list, description="Processing a new batch of 500 leads..."
        ):
            lead_dict = lead.to_dict()
            if isinstance(lead_dict["phone"], str):
                batch.update(lead.reference, {"phones": [lead_dict["phone"]]})
            elif isinstance(lead_dict["phone"], dict):
                batch.update(
                    lead.reference,
                    {
                        "phones": [
                            p["phone"] for p in lead_dict["phone"].values()
                        ]
                    },
                )
            elif lead_dict["phone"] is None:
                console.log(f"Lead {lead.reference.id} has no phone number")
                exist_loop = True
        last_lead = leads_list[-1]
        console.log(f"Updating {len(leads_list)} leads...")
        batch.commit()
        console.log(f"Finished updating {len(leads_list)} leads")
        if exit_loop:
            break
