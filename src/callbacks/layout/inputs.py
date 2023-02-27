import logging
import os
import sys
from datetime import date, datetime

import dash
import dash.html as html
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback
from twilio.rest import Client

from src.components import tables
from src.core.cases import (
    get_case_datails,
    get_lead_single_been_verified,
    get_verified_link,
)
from src.core.config import get_settings
from src.loader.config import ConfigLoader
from src.services import courts, leads
from src.loader.leads import CaseNet, LeadsLoader

logger = logging.Logger(__name__)


@callback(
    Output("court-selector", "options"),
    Input("url", "pathname"),
)
def render_content_persona_details_selector(pathname):
    courts_list = courts.get_courts()
    options = [{"label": c.name, "value": c.code} for c in courts_list]
    return options
