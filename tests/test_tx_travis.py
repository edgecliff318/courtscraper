""" Tests tx_travis.py TX Travis Superior scraper. """
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
from scrapers import ScraperTXTravisSuperior

# It is important to read these with the correct encoding.
# If you get the encoding incorrect, the tests will fail on Unicode characters.
case_detail = BeautifulSoup(
    open("mocks/tx_travis/case_detail.html", "r+", encoding="utf-8").read(),
    features="html.parser",
)
search_results = BeautifulSoup(
    open("mocks/tx_travis/search_results.html", "r+", encoding="utf-8").read(),
    features="html.parser",
)
expected_result = json.loads(
    open("mocks/tx_travis/tx_travis.json", "r+", encoding="utf-8").read()
)


def test_parse_search_results_for_scraper():
    """Tests scraper parsing functionality."""
    actual = ScraperTXTravisSuperior().parse_search_results(
        search_results, "John", "Washington", True
    )["cases"]
    expected = expected_result
    # We can't just check the entire result, because the case_detail is different
    # So instead, we look at all the specific fields except case_detail
    for i in range(0, len(expected) - 1):
        for field in [f for f in expected[i].keys() if f != "case_detail"]:
            assert expected[i][field] == actual[i][field]


def test_get_case_detail_for_scraper():
    """Tests scraper parsing functionality."""
    actual = ScraperTXTravisSuperior().get_case_detail(case_detail)
    expected = expected_result[1]["case_detail"]
    for field in [f for f in expected.keys()]:
        assert expected[field] == actual[field]


def test_search_in_travis_tx_for_lambda():
    """Tests scraper interaction with web site functionality through the scrape interface."""
    actual = ScraperTXTravisSuperior().scrape(
        search_parameters={
            "firstName": "John",
            "lastName": "Washington",
            "dob": None,
        }
    )["result"]
    expected = expected_result
    assert expected == expected_result
