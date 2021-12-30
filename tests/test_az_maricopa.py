""" Tests az_maricopa.py AZ Maricopa Superior Court scraper. """
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir) +'/libraries')
import json
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from scrapers import ScraperAZMaricopaSuperior

# It is important to read these with the correct encoding.
# If you get the encoding incorrect, the tests will fail on Unicode characters.
case_detail = BeautifulSoup(open('mocks/az_maricopa/case_detail.html',
                                 'r+', encoding="utf-8").read(), features="html.parser")
search_results = BeautifulSoup(open(
    'mocks/az_maricopa/search_by_dob.html', 'r+', encoding="utf-8").read(), features="html.parser")
expected_result = json.loads(
    open('mocks/az_maricopa/az_maricopa.json', 'r+', encoding="utf-8").read())

# scraper test


def test_search_by_dob_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperAZMaricopaSuperior().search_by_dob(
        None, None, None, search_results)['cases']
    expected = expected_result

    # We can't just check the entire result, because the case_detail is different
    #assert expected == actual

    # So instead, we look at all the specific fields except case_detail
    for i in range(0, len(expected)-1):
        for field in [f for f in expected[i].keys() if f != 'case_detail']:
            assert expected[i][field] == actual[i][field]


def test_get_case_detail_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperAZMaricopaSuperior().get_case_detail(
        None, case_detail)['case_detail']
    expected = expected_result[1]['case_detail']

    # We can't just check the entire result, because the url is different
    #assert expected == actual

    # So instead, we look at all the specific fields in the case detail except url
    for field in [f for f in expected.keys() if f != 'url']:
        assert expected[field] == actual[field]


def test_search_in_maricopa_az_for_site():
    """ Tests scraper interaction with web site functionality. """
    expected = expected_result
    actual = ScraperAZMaricopaSuperior().search_in_maricopa_az(
        'Christina', 'Banks', '10/22/1978')['result']
    assert actual == expected


def test_search_in_maricopa_az_for_lambda():
    """ Tests scraper interaction with web site functionality through the scrape interface. """
    actual = ScraperAZMaricopaSuperior().scrape(
        search_parameters={'firstName': 'Christina', 'lastName': 'Banks', 'dob': '10/22/1978'})['result']
    expected = expected_result
    assert actual == expected
