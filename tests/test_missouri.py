""" Tests missouri.py MO Court scraper. """
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir) +'/libraries')
import json
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from scrapers import ScraperMOCourt

# It is important to read these with the correct encoding.
# If you get the encoding incorrect, the tests will fail on Unicode characters.
case_header = BeautifulSoup(open('mocks/missouri/case_header.html',
                                 'r+', encoding="utf-8").read(), features="html.parser")
dockets = BeautifulSoup(open('mocks/missouri/dockets.html',
                                'r+', encoding="utf-8").read(), features="html.parser")
charges = BeautifulSoup(open('mocks/missouri/charges.html',
                                'r+', encoding="utf-8").read(), features="html.parser")
services = BeautifulSoup(open('mocks/missouri/services.html',
                                'r+', encoding="utf-8").read(), features="html.parser")
search_results = BeautifulSoup(open(
    'mocks/missouri/search_results.html', 'r+', encoding="utf-8").read(), features="html.parser")
expected_result = json.loads(
    open('mocks/missouri/missouri.json', 'r+', encoding="utf-8").read())


def test_get_case_header_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperMOCourt().get_case_header(case_header)
    expected = expected_result[0]['case_detail']['case_header']
    for field in [f for f in expected.keys()]:
        assert expected[field] == actual[field]

def test_get_case_charges_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperMOCourt().get_case_charges(charges)
    expected = expected_result[0]['case_detail']['charges']
    for field in [f for f in expected.keys()]:
        assert expected[field] == actual[field]

def test_get_docket_entries_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperMOCourt().get_docket_entries(dockets)
    expected = expected_result[0]['case_detail']['dockets']
    assert len(expected) == len(actual)

def test_get_case_service_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperMOCourt().get_case_service(services, None)
    expected = expected_result[0]['case_detail']['services']
    assert len(expected) == len(actual)

def test_parse_search_results_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperMOCourt().parse_search_results(search_results)
    expected = expected_result
    # We can't just check the entire result, because the case_detail is different

    # So instead, we look at all the specific fields except case_detail
    for i in range(0, len(expected)):
        for field in [f for f in expected[i].keys() if f != 'case_detail']:
            assert expected[i][field] == actual[i][field]

def test_search_in_mo_for_lambda():
    """ Tests scraper interaction with web site functionality through the scrape interface. """
    actual = ScraperMOCourt().scrape(search_parameters={
          'firstName': 'Tony', 'lastName': 'Montana', 'dob': None})['result']
    expect = expected_result
    assert actual == expect