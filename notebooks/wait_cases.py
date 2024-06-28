from src.loader.leads import CaseNet
from src.models import cases as cases_model
from src.services import cases, leads
from src.services.leads import get_last_lead, patch_lead, update_lead_status
from src.services.settings import get_account


def refresh_from_casenet(case_id):
    try:
        case_id = str(case_id)
        case_details = cases.get_single_case(case_id)
        case_net_account = get_account("case_net_missouri_sam")
        case_net = CaseNet(
            url=case_net_account.url,
            username=case_net_account.username,
            password=case_net_account.password,
        )
        if case_details is None:
            case_details = {
                "case_id": case_id,
            }
            create = True
        else:
            case_details = case_details.model_dump()
            case_details["court_code"] = case_details.get("court_id")
            create = False

        case_refreshed = case_net.refresh_case(case_details, parties_only=True)
        print(f"Disposition : {case_refreshed['case_dispositiondetail']}")

        plea = case_refreshed.get("case_dispositiondetail", {}).get(
            "disposition_description"
        )

        if isinstance(plea, str) and "guilty" in plea.lower():
            patch_lead(
                case_id,
                status="rpr",
                charges_description=case_refreshed.get("charges_description"),
            )
        else:
            patch_lead(
                case_id,
                status="refreshed",
                charges_description=case_refreshed.get("charges_description"),
            )

        case_refreshed_obj = cases_model.Case.model_validate(case_refreshed)
        print(f"Disposition : {case_refreshed_obj.disposed}")

        if create is False:
            cases.update_case(case_refreshed_obj)
        else:
            cases.insert_case(case_refreshed_obj)
            leads.insert_lead_from_case(case_refreshed)
    except Exception as e:
        print(f"Error refreshing case {case_id}")


if __name__ == "__main__":
    # Get all leads that have been mailed in the last 7 days
    leads_not_found = get_last_lead(
        status="wait",
        limit=3000,
        search_limit=3000,
    )

    print(f"Leads not found {len(leads_not_found)}")

    for lead in leads_not_found:
        print(f"Processing {lead.case_id}")
        refresh_from_casenet(lead.case_id)
