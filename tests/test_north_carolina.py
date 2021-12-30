""" Tests north_carolina.py NC Superior scraper. """
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir) +'/libraries')
import json
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from scrapers import ScraperNCSuperior

# It is important to read these with the correct encoding.
# If you get the encoding incorrect, the tests will fail on Unicode characters.
offender_detail = BeautifulSoup(open('mocks/north_carolina/offender_detail.html',
                                 'r+', encoding="utf-8").read(), features="html.parser")
search_results = BeautifulSoup(open(
    'mocks/north_carolina/search_results.html', 'r+', encoding="utf-8").read(), features="html.parser")
expected_result = json.loads(
    open('mocks/north_carolina/north_carolina.json', 'r+', encoding="utf-8").read())


def test_parse_search_results_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperNCSuperior().parse_search_results(search_results)
    expected = expected_result
    # We can't just check the entire result, because the detail is different
    # So instead, we look at all the specific fields except detail
    for i in range(0, len(expected)-1):
        for field in [f for f in expected[i].keys() if f != 'detail']:
            assert expected[i][field] == actual[i][field]

def test_parse_offender_information_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperNCSuperior().parse_offender_information(offender_detail)
    expected = expected_result[0]['detail']['offender_information']
    for field in [f for f in expected.keys()]:
        assert expected[field] == actual[field]

def test_parse_names_of_record_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperNCSuperior().parse_names_of_record(offender_detail)
    expected = expected_result[0]['detail']['names_of_record']
    for i in range(0, len(expected)):
        assert expected[i] == actual[i]

def test_parse_sentence_history_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperNCSuperior().parse_sentence_history(offender_detail)
    expected = expected_result[0]['detail']['sentence_history']
    for i in range(0, len(expected)):
        assert expected[i] == actual[i]

def test_get_offender_detail_detail_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperNCSuperior().get_offender_detail(offender_detail)
    expected = expected_result[0]['detail']
    for field in [f for f in expected.keys()]:
        assert expected[field] == actual[field]


def test_search_in_travis_tx_for_lambda():
    """ Tests scraper interaction with web site functionality through the scrape interface. """
    actual = ScraperNCSuperior().scrape(search_parameters={
        'firstName': 'Adam', 'lastName': 'Smith', 'dob': '12/19/1967'})['result']
    expected = expected_result
    assert expected == expected_result
