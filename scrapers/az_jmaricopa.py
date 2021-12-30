""" Scraper for Maricopa Justice Court """
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir) +'/libraries')
import requests
import json
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from base import NameNormalizer, TextNormalizer, ScraperBase, InitializedSession


class ScraperAZMaricopaJustice(ScraperBase):
    """ AZ Maricopa Justice Court scraper """

    COOKIE = '__cfduid=d53b4111ba1b8303210655e093b386d5e1588873745; ASP.NET_SessionId=z4xv3ru2yqugmcvpup1vuteo; pecan=4245741578.20480.0000; ASPSESSIONIDQQTDTQDQ=DEBHDILAJPOKKIHLLJMBBFLN; ASPSESSIONIDCQARQQBS=OJAEDJCCFEALFELBKKICDFND; ASPSESSIONIDAQBCCACC=ABHFDLDCCCNJBJILACGEDJDM'
    BASE_URL = 'http://justicecourts.maricopa.gov'
    SEARCH_RESULT_URL = 'http://justicecourts.maricopa.gov/FindACase/caseSearchResults.asp'

    def scrape(self, search_parameters):
        """ Entry point for lambda.

        Query should look like this:

        {
            "lastName": "Banks",
            "firstName": "Christina",
            "dob": "10/22/1978"
        }

        https://<endpoint>?queryStringParameters
        """
        print('jMaricopa:', search_parameters)
        last_name = search_parameters["lastName"]
        first_name = search_parameters["firstName"]
        dob = search_parameters["dob"]
        return self.search_in_jmaricopa_az(first_name, last_name, dob)

    # This should be the only session used in this module.
    GLOBAL_SESSION = InitializedSession(headers={'Cookie': COOKIE})

    def parse_case_information(self, soup):
        """ Parse initial case information using rendered HTML page.

        This function returns an object.
        """
        case_information_table = soup.find('table', {'id': 'tblForms'})
        if not case_information_table:
            return {}
        case_information_rows = case_information_table.findAll('tr')
        case_information = {}
        for row in case_information_rows:
            cells = row.findAll('td')
            if len(cells) > 2:
                case_information[cells[0].text.strip().replace(
                    ':', '')] = cells[1].text.strip()
                case_information[cells[2].text.strip().replace(
                    ':', '')] = cells[3].text.strip()
        return case_information

    def parse_party_information(self, soup):
        """ Parse party information of case detail using rendered HTML page.

        This function returns an object array.
        """
        party_information_table = soup.find('table', {'id': 'tblForms2'})
        if not party_information_table:
            return []
        party_information_rows = party_information_table.findAll('tr')
        party_information = []
        for row in party_information_rows:
            cells = row.findAll('td')
            if len(cells) > 3 and cells[0].text.strip() != 'Party Name':
                party = {}
                party['party_name'] = cells[0].text.strip()
                party['relationship'] = cells[1].text.strip()
                party['sex'] = cells[2].text.strip()
                party['attorney'] = cells[3].text.strip()
                party_information.append(party)
        return party_information

    def parse_disposition_information(self, soup):
        """ Parse disposition information of case detail using rendered HTML page.

        This function returns an object array.
        """
        disposition_information_table = soup.find('table', {'id': 'tblForms7'})
        if not disposition_information_table:
            return []
        disposition_information_rows = disposition_information_table.findAll(
            'tr')
        disposition_information = []
        for row in disposition_information_rows:
            cells = row.findAll('td')
            if len(cells) > 6 and cells[0].text.strip() != 'Party Name':
                disposition = {}
                disposition['party_name'] = cells[0].text.strip()
                disposition['ARScode'] = cells[1].text.strip()
                disposition['description'] = cells[2].text.strip()
                disposition['crime_date'] = cells[3].text.strip()
                disposition['disposition_code'] = cells[4].text.strip()
                disposition['disposition'] = cells[5].text.strip()
                disposition['date'] = cells[6].text.strip()
                disposition_information.append(disposition)
        return disposition_information

    def parse_case_document_information(self, soup):
        """ Parse case documents of case detail using rendered HTML page.

        This function returns an object array.
        """
        case_document_information_table = soup.find(
            'table', {'id': 'tblForms3'})
        if not case_document_information_table:
            return []
        case_document_information_rows = case_document_information_table.findAll(
            'tr')
        case_document_information = []
        for row in case_document_information_rows:
            cells = row.findAll('td')
            if len(cells) > 3 and cells[0].text.strip() != 'Filing Date':
                case_document = {}
                case_document['filing_date'] = cells[0].text.strip()
                case_document['description'] = cells[1].text.strip()
                case_document['docket_date'] = cells[2].text.strip()
                case_document['filing_party'] = cells[3].text.strip()
                case_document_information.append(case_document)
        return case_document_information

    def parse_case_calendar_information(self, soup):
        """ Parse calendar information of case detail using rendered HTML page.

        This function returns an object array.
        """
        case_calendar_information_table = soup.find(
            'table', {'id': 'tblForms4'})
        if not case_calendar_information_table:
            return []
        case_calendar_information_rows = case_calendar_information_table.findAll(
            'tr')
        case_calendar_information = []
        for row in case_calendar_information_rows:
            cells = row.findAll('td')
            if len(cells) > 3 and cells[0].text.strip() != 'Date':
                case_calendar = {}
                case_calendar['filing_date'] = cells[0].text.strip()
                case_calendar['description'] = cells[1].text.strip()
                case_calendar['docket_date'] = cells[2].text.strip()
                case_calendar['filing_party'] = cells[3].text.strip()
                case_calendar_information.append(case_calendar)
        return case_calendar_information

    def parse_events_information(self, soup):
        """ Parse events information of case detail using rendered HTML page.

        This function returns an object array.
        """
        events_information_table = soup.find('table', {'id': 'tblForms6'})
        if not events_information_table:
            return []
        events_information_rows = events_information_table.findAll('tr')
        events_information = []
        for row in events_information_rows:
            cells = row.findAll('td')
            if len(cells) > 3 and cells[0].text.strip() != 'Event Type':
                event = {}
                event['event_type'] = cells[0].text.strip()
                event['sub_type'] = cells[1].text.strip()
                event['result'] = cells[2].text.strip()
                event['result_date'] = cells[3].text.strip()
                events_information.append(event)
        return events_information

    def parse_judgement_information(self, soup):
        """ Parse judgement information of case detail using rendered HTML page.

        This function returns an object array.
        """
        judgement_information_table = soup.find('table', {'id': 'tblForms5'})
        if not judgement_information_table:
            return []
        judgement_information_rows = judgement_information_table.findAll('tr')
        judgement_information = []
        for row in judgement_information_rows:
            cells = row.findAll('td')
            if len(cells) > 6 and cells[0].text.strip() != 'Date':
                judgement = {}
                judgement['date'] = cells[0].text.strip()
                judgement['f/a'] = cells[1].text.strip()
                judgement['amount'] = cells[2].text.strip()
                judgement['frequency'] = cells[3].text.strip()
                judgement['type_costs'] = cells[4].text.strip()
                judgement['status'] = cells[5].text.strip()
                judgement_information.append(judgement)
        return judgement_information

    def get_case_detail(self, soup):
        """ Get case detail by using parse functions that return every information of case detail using rendered HTML page

        This function returns an object.
        """
        case = self.parse_case_information(soup)
        case['parties'] = self.parse_party_information(soup)
        case['dispositions'] = self.parse_disposition_information(soup)
        case['case_documents'] = self.parse_case_document_information(soup)
        case['case_calendar'] = self.parse_case_calendar_information(soup)
        case['events'] = self.parse_events_information(soup)
        case['judgements'] = self.parse_judgement_information(soup)
        return case

    def parse_search_results(self, soup, test=False):
        """ Scrape list of cases by rendered HTML page.

        If test is set to True, it will not get case detail for each case.

        This function either returns an object with
        a field called "cases" which is an array of cases, or
        an object with a field called "error" with a error string
        e.g. { "cases": [...] } or { "error": "..." }
        """
        cases = []
        case_table = soup.find('table', class_='zebraRowTable')
        if case_table:
            case_rows = case_table.findAll('tr')
            for case_row in case_rows:
                cells = case_row.findAll('td')
                if len(cells) > 0:
                    case_url = ''
                    if cells[0].find('a'):
                        case_url = cells[0].find('a').attrs['href']
                    case_detail = {}
                    if not test and case_url != '':
                        try:
                            r = self.GLOBAL_SESSION.get(
                                self.BASE_URL + case_url)
                        except requests.ConnectionError as e:
                            print("Connection failure : " + str(e))
                            print(
                                "Verification with InsightFinder credentials Failed")
                            return {'error':  str(e)}
                        # print(BASE_URL + case_url, r.text)
                        # html = open('s.html', 'w')
                        # html.write(r.text)
                        # html.close()
                        case_detail = self.get_case_detail(
                            BeautifulSoup(r.text, features="html.parser"))
                    # case_detail['case_url'] = case_url
                    cases.append(case_detail)

        return {'cases': cases}

    # main func
    def search_in_jmaricopa_az(self, first_name, last_name, dob):
        """ Scrape the web site using the given search criteria.

        This function either returns an object with
        a field called "result" which is an array of cases, or
        an object with a field called "error" with a error string
        e.g. { "result": [...] } or { "error": "..." }
        """
        first_name = NameNormalizer(first_name).normalized()
        last_name = NameNormalizer(last_name).normalized()
        if dob:
            dob = dob.strip()

        url = '{}?lastName={}&FirstName={}&DOB={}'.format(
            self.SEARCH_RESULT_URL, last_name, first_name, dob)
        try:
            r = self.GLOBAL_SESSION.get(url)
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {'error':  str(e)}
        print(url)
        self.GLOBAL_SESSION = InitializedSession(
            headers={'Cookie': self.COOKIE, 'Referer': url})

        soup = BeautifulSoup(r.text, features="html.parser")
        result = self.parse_search_results(soup)
        # print(json.dumps(result, indent=4, sort_keys=True))
        if 'error' in result:
            return {'error': result['error']}
        else:
            return {'result': result['cases']}


if __name__ == "__main__":
    #search_in_jmaricopa_az('Christina', 'Banks', '10/22/1978')
    # search_in_jmaricopa_az('Laurie', 'Wheeler', '10/07/1968')
    print(ScraperAZMaricopaJustice().scrape(
        search_parameters={'firstName': 'Christina', 'lastName': 'Banks', 'dob': '10/22/1978'})['result'])
    print('Done running', __file__, '.')
