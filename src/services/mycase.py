from src.loader.mycase import MyCase
from src.models import messages
from src.services import cases
from src.services.messages import insert_interaction


def send_to_client_mycase(email, subject, message, attachments, case_id=None):
    mycase = MyCase(url="", password="", username="")
    mycase.login()

    participant, client_id = cases.get_mycase_id(case_id)
    mycase_cases = mycase.get_cases(client_id)

    if len(mycase_cases) == 0:

        raise Exception(
            f"No case found in MyCase with first name {participant.first_name}, last name {participant.last_name} and email {participant.email}. Please add the case to MyCase and update the participant details."
        )

    for case in mycase_cases:
        if case_id in case["name"]:
            mycase_id = case["id"]
            case_name = case["name"]
            break

    response = mycase.create_mycase_message(
        mycase_case_id=mycase_id,
        client_id=client_id,
        subject=subject,
        message=message,
        attachments=attachments,
        case_name=case_name,
    )

    return response


def send_sms_to_client_mycase(case_id, message, phone):
    mycase = MyCase(url="", password="", username="")
    mycase.login()

    participant, client_id = cases.get_mycase_id(case_id)
    mycase_cases = mycase.get_cases(client_id)

    if len(mycase_cases) == 0:
        raise Exception(
            f"No case found in MyCase with first name {participant.first_name}, last name {participant.last_name} and email {participant.email}. Please add the case to MyCase and update the participant details."
        )

    for case in mycase_cases:
        if case_id in case["name"]:
            mycase_id = case["id"]
            break

    response = mycase.create_text_message(
        mycase_case_id=mycase_id,
        message=message,
    )

    text_message = response.get("text_message", {})

    interaction = messages.Interaction(
        case_id=case_id,
        message=message,
        type="sms",
        status=text_message.get("status", "sent"),
        id=str(text_message.get("id", "not available")),
        direction="outbound",
        phone=phone,
    )

    insert_interaction(interaction)

    return response
