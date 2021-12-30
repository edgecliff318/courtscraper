""" Tests az_jmaricopa.py AZ Maricopa Justice Court scraper. """
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir) +'/libraries')
import json
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from scrapers import ScraperAZMaricopaJustice

# It is important to read these with the correct encoding.
# If you get the encoding incorrect, the tests will fail on Unicode characters.
case_detail = BeautifulSoup(open('mocks/az_jmaricopa/case_detail.html',
                                 'r+', encoding="utf-8").read(), features="html.parser")
search_results = BeautifulSoup(open(
    'mocks/az_jmaricopa/search_results.html', 'r+', encoding="utf-8").read(), features="html.parser")
expected_result = json.loads(
    open('mocks/az_jmaricopa/az_jmaricopa.json', 'r+', encoding="utf-8").read())


def test_parse_search_results_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperAZMaricopaJustice().parse_search_results(
        search_results, True)['cases']
    assert len(actual) == len(expected_result)


def test_get_case_detail_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperAZMaricopaJustice().get_case_detail(case_detail)
    expected = expected_result[2]
    assert actual == expected


def test_parse_case_information_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperAZMaricopaJustice().parse_case_information(case_detail)
    expected = expected_result[2]
    for key in ['Case Number', 'Case Type', 'Location', 'Case Status']:
        assert actual[key] == expected[key]


def test_parse_party_information_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperAZMaricopaJustice().parse_party_information(case_detail)
    expected = expected_result[2]['parties']
    assert actual == expected


def test_parse_disposition_information_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperAZMaricopaJustice().parse_disposition_information(case_detail)
    expected = expected_result[2]['dispositions']
    assert actual == expected


def test_parse_case_document_information_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperAZMaricopaJustice().parse_case_document_information(case_detail)
    expected = expected_result[2]['case_documents']
    assert actual == expected


def test_parse_case_calendar_information_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperAZMaricopaJustice().parse_case_calendar_information(case_detail)
    expected = expected_result[2]['case_calendar']
    assert actual == expected


def test_parse_events_information_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperAZMaricopaJustice().parse_events_information(case_detail)
    expected = expected_result[2]['events']
    assert actual == expected


def test_parse_judgement_information_for_scraper():
    """ Tests scraper parsing functionality. """
    actual = ScraperAZMaricopaJustice().parse_judgement_information(case_detail)
    expected = expected_result[2]['judgements']
    assert actual == expected


def test_search_in_jmaricopa_az_for_lambda():
    """ Tests scraper interaction with web site functionality through the scrape interface. """
    actual = ScraperAZMaricopaJustice().scrape(
        search_parameters={'firstName': 'Christina', 'lastName': 'Banks', 'dob': '10/22/1978'})['result']
    expected = expected_result
    assert actual == expected
