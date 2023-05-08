""" Tests maryland.py MD Court scraper. """
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
from scrapers import ScraperMDCourt

# It is important to read these with the correct encoding.
# If you get the encoding incorrect, the tests will fail on Unicode characters.
case_detail = BeautifulSoup(
    open("mocks/maryland/case_detail.html", "r+", encoding="utf-8").read(),
    features="html.parser",
)
search_results = BeautifulSoup(
    open("mocks/maryland/search_results.html", "r+", encoding="utf-8").read(),
    features="html.parser",
)
expected_result = json.loads(
    open("mocks/maryland/maryland.json", "r+", encoding="utf-8").read()
)


def test_parse_search_results_by_page_for_scraper():
    """Tests scraper parsing functionality."""
    actual = ScraperMDCourt().parse_search_results_by_page(search_results)[3]
    expected = expected_result[0]
    # We can't just check the entire result, because the case_detail is different

    # So instead, we look at all the specific fields except case_detail
    for field in [f for f in expected.keys() if f != "case_detail"]:
        assert expected[field] == actual[field]


def test_get_case_detail_for_scraper():
    """Tests scraper parsing functionality."""
    actual = ScraperMDCourt().get_case_detail(case_detail)
    expected = expected_result[0]["case_detail"]

    for field in [f for f in expected.keys()]:
        assert expected[field] == actual[field]


def test_search_in_md_for_lambda():
    """Tests scraper interaction with web site functionality through the scrape interface."""
    actual = ScraperMDCourt().scrape(
        search_parameters={
            "firstName": "Adam",
            "lastName": "Smith",
            "dob": "10/06/1969",
        }
    )["result"]
    expect = expected_result
    assert actual == expect
