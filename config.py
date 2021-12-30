import pathlib

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