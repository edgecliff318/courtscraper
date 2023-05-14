prompt = f"""
You work as an assistant to a lawyer in the USA,\
and your role is to generate messages that the lawyer can send to clients. These messages should include a \
copy of the case, along with the date, type, and status of the case, as well as any relevant message about the case
information of case of client.\
``{{'Case ID': '[140484751](/case/140484751)', 'Date': '03/24/2023', 'First Name': 'MARK', 'Last Name': 'CURTIS', 'Phone': '(417) 466-6506', 'Email': 'No email addresses found', 'Status': 'not_contacted', 'Age': 60, 'Charges': 'Driving While Revoked Or Suspended \\r{\\xa0Ordinance\\xa0RSMo:\\xa0Not Available\\xa0}', 'Disposition': None}}``
"""


response = f"""
As an assistant to the lawyer, I would draft the following message to be sent to the client:

Dear Mark Curtis,

I hope this message finds you well. I am writing to provide you with an update on your case with Case ID 140484751.

As per the information available to us, the case was initiated on 03/24/2023 and involves charges of Driving While Revoked or Suspended. At this time, the case status is "not_contacted", and no disposition has been made.

To help you stay informed, I am attaching a copy of the case for your reference. If you have any questions or concerns about your case, please do not hesitate to contact us.

Best regards,

[Lawyer's Name]
"""
