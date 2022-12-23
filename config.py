import pathlib
import os

# Application title
title = "Ticket Washer"

# Parameter for the pathname configuration
pathname_params = dict()
pathname_params["routes_pathname_prefix"] = "/"
# pathname_params["requests_pathname_prefix"] = "/ext/dashboard/"


# Logging configuration
logging_level = 'DEBUG'

# Configuration file
config_filename = 'config.json'
config_test_filename = 'config_test.json'

# Root Path
root_path = pathlib.Path(__file__).parent
data_path = root_path.joinpath("./data").resolve()
config_path = root_path.joinpath("./configuration").resolve()
upload_path = root_path.joinpath("./data/upload").resolve()
output_path = root_path.joinpath("./data/output").resolve()

# Template
template = "plotly"
card_default_config = {
    "modal": True,
    "fullscreen": True,
    "modal_config": {'width': 80, 'height': 80}
}

# Salt
SALT = b'#F+M\x80\xd7?t"\x9e\x9aP\x9d\xe0e\xb8\x06%\xcdy\x83?\xef\xc5\x82' \
       b'\xad\x15!\xa7\x1f\xa0\xed'


# Case Net
case_net_url = "https://www.courts.mo.gov/cnet"
case_net_username = "smeyer4040"
case_net_password = "MASfirm2021!!!!"

#
production = os.environ.get("PRODUCTION", "true").lower() == "true"

# Remote Instance
remote_upload_url = "http://34.136.192.67:8060/upload?cache=true"
remote_data_upload_url = "http://34.136.192.67:8060/upload?cache=false"
remote_update_url = "http://34.136.192.67:8060/update"

# Twilio Configuration
twilio_account_sid = 'ACc675e16f153269ab1d8d4c5f3ae2ce8a'
twilio_auth_token = '095c5fb2a0eea27b7c4e46c1fd12cf45'
twilio_messaging_service_sid = 'MG3beed289e59b0417fc8d1c63894aa27e'
