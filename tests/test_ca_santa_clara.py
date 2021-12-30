""" Tests ca_santa_clara.py CA Santa Clara Superior scraper. """
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir) +'/libraries')
import json
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from scrapers import ScraperCASantaClaraSuperior

# It is important to read these with the correct encoding.
# If you get the encoding incorrect, the tests will fail on Unicode characters.
case_detail = json.loads(
    open('mocks/ca_santa_clara/case_detail.json', 'r+', encoding="utf-8").read())
search_results = open(
    'mocks/ca_santa_clara/search_results.json', 'r+', encoding="utf-8").read()
expected_result = json.loads(
    open('mocks/ca_santa_clara/ca_santa_clara.json', 'r+', encoding="utf-8").read())


def test_get_search_result_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperCASantaClaraSuperior().get_search_result(
        None, None, None, search_results)
    expected = expected_result
    # We can't just check the entire result, because the case_detail is different
    # So instead, we look at all the specific fields except case_detail
    for i in range(0, len(expected)-1):
        for field in [f for f in expected[i].keys() if f != 'case_detail']:
            assert expected[i][field] == actual[i][field]


def test_get_case_detail_for_site():
    """ Tests scraper parsing functionality. """
    actual = ScraperCASantaClaraSuperior().get_case_detail(json.loads(
        search_results)['data'][0]["caseId"])['case_detail']
    expected = case_detail['data']
    for field in [f for f in expected.keys()]:
        assert expected[field] == actual[field]


def test_search_in_santa_clara_ca_for_lambda():
    """ Tests scraper interaction with web site functionality through the scrape interface. """
    actual = ScraperCASantaClaraSuperior().scrape(search_parameters={
        'firstName': 'Stuart', 'lastName': 'Baker', 'dob': '10/27/1963'})['result']
    expected = expected_result
    assert actual == expected
