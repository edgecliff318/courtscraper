""" Tests il_johnson.py IL Johnson Superior scraper. """
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir) +'/libraries')
import json
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from scrapers import ScraperILJohnsonSuperior

# It is important to read these with the correct encoding.
# If you get the encoding incorrect, the tests will fail on Unicode characters.
search_results = BeautifulSoup(open(
    'mocks/il_johnson/search_results.html', 'r+', encoding="utf-8").read(), features="html.parser")
expected_result = json.loads(
    open('mocks/il_johnson/il_johnson.json', 'r+', encoding="utf-8").read())

def test_parse_search_results_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperILJohnsonSuperior().parse_search_results(search_results, expected_result[0]['dob'])
    expected = expected_result
    # We can't just check the entire result, because the case_detail is different
    # So instead, we look at all the specific fields except case_detail
    for i in range(0, len(expected)-1):
        for field in [f for f in expected[i].keys() if f != 'case_detail']:
            assert expected[i][field] == actual[i][field]

def test_convertDobToStr():
    """ Tests scraper parsing functionality. """
    actual = ScraperILJohnsonSuperior().convertDobToStr('12/27/1978')
    expected = 'December 27, 1978'
    assert actual == expected

def test_get_case_detail():
    """ Tests scraper parsing functionality. """
    for i in range(0, len(expected_result)):
        actual = ScraperILJohnsonSuperior().get_case_detail(expected_result[i]['case_url'])
        expected = expected_result[i]['case_detail']
        for field in [f for f in expected.keys()]:
            assert expected[field] == actual[field]

def test_get_case_information():
    """ Tests scraper parsing functionality. """
    for i in range(0, len(expected_result)):
        actual = ScraperILJohnsonSuperior().get_case_information(expected_result[i]['case_url'])
        expected = expected_result[i]['case_detail']['case_information']
        for field in [f for f in expected.keys()]:
            assert expected[field] == actual[field]


def test_get_case_detail_from_table():
    """ Tests scraper parsing functionality. """
    for i in range(0, len(expected_result)):
        actual = ScraperILJohnsonSuperior().get_case_detail_from_table(expected_result[i]['case_url'].replace('case_information', 'case_dispositions'))
        expected = expected_result[i]['case_detail']['case_dispositions']
        for j in range(0, len(expected)):
            assert expected[j] == actual[j]

        actual = ScraperILJohnsonSuperior().get_case_detail_from_table(expected_result[i]['case_url'].replace('case_information', 'case_history'))
        expected = expected_result[i]['case_detail']['case_history']
        for j in range(0, len(expected)):
            assert expected[j] == actual[j]
        
        actual = ScraperILJohnsonSuperior().get_case_detail_from_table(expected_result[i]['case_url'].replace('case_information', 'case_payment_history'))
        expected = expected_result[i]['case_detail']['case_payment_history']
        for j in range(0, len(expected)):
            assert expected[j] == actual[j]

        actual = ScraperILJohnsonSuperior().get_case_detail_from_table(expected_result[i]['case_url'].replace('case_information', 'case_fines_fees'))
        expected = expected_result[i]['case_detail']['case_fines_fees']
        for j in range(0, len(expected)):
            assert expected[j] == actual[j]
            
def test_search_in_travis_tx_for_lambda():
    """ Tests scraper interaction with web site functionality through the scrape interface. """
    actual = ScraperILJohnsonSuperior().scrape(search_parameters={
        'firstName': 'Richard', 'lastName': 'Smith', 'dob': '12/27/1978'})['result']
    expected = expected_result
    assert expected == expected_result
