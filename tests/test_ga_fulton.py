""" Tests ga_fulton.py GA Fulton Superior Court scraper. """
import os.path
import sys

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    + "/libraries"
)
import json

from bs4 import BeautifulSoup

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
)
from scrapers import ScraperGAFultonSuperior

# It is important to read these with the correct encoding.
# If you get the encoding incorrect, the tests will fail on Unicode characters.
case_detail = BeautifulSoup(
    open("mocks/ga_fulton/case_detail.html", "r+", encoding="utf-8").read(),
    features="html.parser",
)
financial_information = BeautifulSoup(
    open(
        "mocks/ga_fulton/financial_information.html", "r+", encoding="utf-8"
    ).read(),
    features="html.parser",
)
search_results = open(
    "mocks/ga_fulton/search_results.html", "r+", encoding="utf-8"
).read()
expected_result = json.loads(
    open("mocks/ga_fulton/ga_fulton.json", "r+").read()
)


def test_get_search_result_for_scraper():
    """Tests scraper parsing functionality."""
    actual = ScraperGAFultonSuperior().get_search_result(search_results)
    expected = expected_result
    # We can't just check the entire result, because the CaseResults is different
    # So instead, we look at all the specific fields except CaseResults
    for i in range(0, len(expected) - 1):
        for field in [f for f in expected[i].keys() if f != "CaseResults"]:
            assert expected[i][field] == actual[i][field]


def test_get_financial_information_for_scraper():
    """Tests scraper parsing functionality."""
    actual = ScraperGAFultonSuperior().get_financial_information(
        financial_information
    )
    expected = expected_result[1]["CaseResults"][0]["CaseDetail"]["financials"]

    for i in range(0, len(expected) - 1):
        for field in [f for f in expected[i].keys()]:
            assert expected[i][field] == actual[i][field]


def test_get_events_information_for_scraper():
    """Tests scraper parsing functionality."""
    actual = ScraperGAFultonSuperior().get_events_information(case_detail)
    expected = expected_result[1]["CaseResults"][0]["CaseDetail"]["events"]
    for i in range(0, len(expected) - 1):
        assert expected[i] == actual[i]


def test_get_charge_information_for_scraper():
    """Tests scraper parsing functionality."""
    actual = ScraperGAFultonSuperior().get_charge_information(case_detail)
    expected = expected_result[1]["CaseResults"][0]["CaseDetail"]["charges"]
    for i in range(0, len(expected) - 1):
        for field in [f for f in expected[i].keys()]:
            assert expected[i][field] == actual[i][field]


def test_get_party_information_for_scraper():
    """Tests scraper parsing functionality."""
    actual = ScraperGAFultonSuperior().get_party_information(case_detail)
    expected = expected_result[1]["CaseResults"][0]["CaseDetail"]["party"]
    for i in range(0, len(expected) - 1):
        for field in [f for f in expected[i].keys()]:
            assert expected[i][field] == actual[i][field]


def test_get_disposition_information_for_scraper():
    """Tests scraper parsing functionality."""
    actual = ScraperGAFultonSuperior().get_disposition_information(case_detail)
    expected = expected_result[1]["CaseResults"][0]["CaseDetail"][
        "dispositions"
    ]
    for i in range(0, len(expected) - 1):
        for j in range(0, len(expected[i]) - 1):
            assert expected[i][j] == actual[i][j]


def test_get_case_information_for_scraper():
    """Tests scraper parsing functionality."""
    actual = ScraperGAFultonSuperior().get_case_information(case_detail)
    expected = expected_result[1]["CaseResults"][0]["CaseDetail"]
    for key in [
        "Case Number",
        "Case Status",
        "Case Type",
        "Court",
        "File Date",
        "Judicial Officer",
    ]:
        assert actual[key] == expected[key]


def test_search_in_fulton_ga_for_lambda():
    """Tests scraper interaction with web site functionality through the scrape interface."""
    actual = ScraperGAFultonSuperior().scrape(
        search_parameters={
            "firstName": "Stuart",
            "lastName": "Baker",
            "dob": "",
        }
    )["result"]
    expected = expected_result
    assert actual == expected
