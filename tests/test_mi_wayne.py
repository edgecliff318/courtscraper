""" Tests mi_wayne.py MI Wayne Superior scraper. """
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir) +'/libraries')
import json
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from scrapers import ScraperMIWayneSuperior

# It is important to read these with the correct encoding.
# If you get the encoding incorrect, the tests will fail on Unicode characters.
search_results = BeautifulSoup(open(
    'mocks/mi_wayne/search_results.html', 'r+', encoding="utf-8").read(), features="html.parser")
expected_result = json.loads(
    open('mocks/mi_wayne/mi_wayne.json', 'r+', encoding="utf-8").read())


def test_parse_search_results_page_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperMIWayneSuperior().parse_search_results_page(
        search_results, '9/20/1984')
    expected = [expected_result[0]]
    # We can't just check the entire result, because the case_detail is different
    # So instead, we look at all the specific fields except case_detail
    for i in range(0, len(expected)-1):
        for field in [f for f in expected[i].keys() if f != 'case_detail']:
            assert expected[i][field] == actual[i][field]


def test_get_case_detail_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperMIWayneSuperior().get_case_detail('1904547201', 0, 'Smith', 'Adam')
    expected = expected_result[0]['case_detail']
    for field in [f for f in expected.keys()]:
        assert expected[field] == actual[field]


# def test_search_in_wayne_mi_for_lambda():
#     """ Tests scraper interaction with web site functionality through the scrape interface. """
#     actual = ScraperMIWayneSuperior().scrape(search_parameters={
#         'firstName': 'Adam', 'lastName': 'Smith', 'dob': '09/20/1984'})['result']
#     expected = expected_result
#     assert expected == expected_result
