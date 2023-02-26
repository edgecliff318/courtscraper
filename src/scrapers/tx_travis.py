""" Scraper for Travis Superior Court """
from bs4 import BeautifulSoup
from src.scrapers.base import NameNormalizer, TextNormalizer, ScraperBase, InitializedSession
import json
import requests
import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), os.pardir) + '/libraries')

sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), os.pardir))


class ScraperTXTravisSuperior(ScraperBase):
    """ TX Travis Superior Court scraper """

    HEADERS = {
        'Cookie': 'f5avrbbbbbbbbbbbbbbbb=LBGHFOKMEPDNFOKHHDHIKAEDJGLEGOBNLKIFKPOKCODJDMLPOIEFKMONINACBPOANDJIPDFDGJCDHKPDKKDHEILOMGEAFECEFECAKDCHELCHINONFFCCINOJGFPHFNIC; _ga=GA1.2.258218475.1588935386; _gid=GA1.2.448862907.1589269663; ASP.NET_SessionId=jai1q23npcy2tdauzpiqtagm; __RequestVerificationToken_L09ubGluZUNhc2VJbmZvcm1hdGlvbldlYg2=ewAYv6ywvlpgLYDkDQ7aC-mFUyP-8JgmXdtw5C_lMj9y14YrMHWZEaBHIZoiudakojLDVTHMm37gIEwG4yD169Uo7sC3c_hx6gp3mRneUtU1; TS01508fb5_28=01b2c09b80fd5264c3325b6b657e7a4ba0c56cf438812186c1622902c514feb41e738b8018160608672126e572749fcb0ad2fbb49e; TS01508fb5=01798eb63477113256840bed946de5b599cacf68a0c34359c86f4772fbc14b62a7da0fbc4bcf78b135987b0c0c9debc15bf23509ea193b52c03328c99fc8ffb89c3502da5bdf7789e90adf38f762f12dd524b70cb4ea9f0b3528bc60283708fc413c05b03be84a337fe0bef1713b8bcf149602fbdb; _gat=1',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    BASE_URL = 'https://public.traviscountytx.gov'
    SEARCH_RESULT_URL = 'https://public.traviscountytx.gov/OnlineCaseInformationWeb/'

    def scrape(self, search_parameters):
        """ Entry point for lambda.

        Query should look like this:

        {
            "lastName": "John",
            "firstName": "Washington",
            "dob": ""
        }
        https://<endpoint>?queryStringParameters
        """
        last_name = search_parameters["lastName"]
        first_name = search_parameters["firstName"]
        dob = search_parameters["dob"]
        return self.search_in_travis_tx(first_name, last_name, dob)

    GLOBAL_SESSION = InitializedSession(headers=HEADERS)

    def get_case_detail(self, soup):
        """ Get every information of case detail by parsing rendered HTML page

        This function returns an object.
        """
        case_detail = {}
        case_information_list = soup.find('dl', class_='dl-horizontal')
        case_information = []

        if case_information_list:
            for information in case_information_list.findAll('dd'):
                case_information.append(information.text.strip())
        if len(case_information) > 4:
            case_detail['case_number'] = case_information[0]
            case_detail['case_status'] = case_information[1]
            case_detail['case_style'] = case_information[2]
            case_detail['filed_date'] = case_information[3]
            case_detail['hearing_date'] = case_information[4]

        party_table = soup.find('table', class_='app-party-table')
        parties = []
        if party_table:
            party_rows = party_table.findAll('tr')
            for party_row in party_rows:
                cells = party_row.findAll('td')
                if len(cells) > 5:
                    attorney = cells[0].text.strip()
                    party_type = cells[1].text.strip()
                    full_business_name = cells[2].text.strip()
                    first_name = cells[3].text.strip()
                    middle_name = cells[4].text.strip()
                    last_name = cells[5].text.strip()
                    parties.append({
                        'attorney': attorney,
                        'type': party_type,
                        'full/business_name': full_business_name,
                        'first_name': first_name,
                        'middle_name': middle_name,
                        'last_name': last_name
                    })
        case_detail['parties'] = parties

        event_table = soup.find('table', class_='app-event-table')
        events = []
        if event_table:
            event_rows = event_table.findAll('tr')
            for event_row in event_rows:
                cells = event_row.findAll('td')
                if len(cells) > 2:
                    event_date = cells[0].text.strip()
                    party_type = cells[1].text.strip()
                    description = cells[2].text.strip()
                    events.append({
                        'event_date': event_date,
                        'party_type': party_type,
                        'description': description,
                    })
            case_detail['events'] = events

        return case_detail

    def parse_search_results(self, soup, fn, ln, test=False):
        """ Parse rendered HTML page for search result and get matched cases using given firstName and lastName

        If test is set to parsed HTML, like what BeautifulSoup provides,
        the code will not attempt a lookup on the web site,
        but will instead use that HTML.

        This function returns an array.
        """
        cases = []
        case_table = soup.find('table', class_='app-sres-table')
        if not case_table:
            return []
        case_rows = case_table.findAll('tr')
        for case_row in case_rows:
            cells = case_row.findAll('td')
            if len(cells) > 7:
                case_number = cells[0].text.strip()
                full_business_name = cells[1].text.strip()
                first_name = cells[2].text.strip()
                middle_name = cells[3].text.strip()
                last_name = cells[4].text.strip()
                case_status = cells[5].text.strip()
                file_date = cells[6].text.strip()
                case_url = ''
                if cells[7].find('a'):
                    case_url = cells[7].find('a').attrs['href']

                # check whether this case is matched or not
                if 'DC' in case_number and first_name.lower() == fn.lower() and last_name.lower() == ln.lower():
                    case_detail = {}
                    if not test and case_url != '':
                        try:
                            r = self.GLOBAL_SESSION.get(
                                self.BASE_URL + case_url)
                        except requests.ConnectionError as e:
                            print("Connection failure : " + str(e))
                            print(
                                "Verification with InsightFinder credentials Failed")
                            return {'error': str(e)}

                        case_detail = self.get_case_detail(
                            BeautifulSoup(r.text, features="html.parser"))

                    cases.append({
                        'case_number': case_number,
                        'full/business_name': full_business_name,
                        'first_name': first_name,
                        'middle_name': middle_name,
                        'last_name': last_name,
                        'case_status': case_status,
                        'file_date': file_date,
                        'case_url': case_url,
                        'case_detail': case_detail
                    })
        return {'cases': cases}

    def search_in_travis_tx(self, first_name, last_name, dob):
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

        try:
            r = self.GLOBAL_SESSION.post(self.SEARCH_RESULT_URL, {
                '__RequestVerificationToken': 'CK9zRat6YvIJa7mJUeCaJcMPhEd1kiAOIyqmbsYoWeoBXsJby2IenB9Oo0uzamnqItLWfmpbMnQJ-9LzRSV77ej5RpVchiRg4Odzq-hvlP81',
                "CourtType": "D",
                "CourtLocation": "1",
                "CauseType": "",
                "CauseYear": "",
                "CauseNumber": "",
                "LastOrBusinessName": last_name,
                "FirstName": first_name,
                "SearchYearText": "",
                "FormSubmitButton": "Search",
            })
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {'error': str(e)}
        soup = BeautifulSoup(r.text, features="html.parser")

        # parse html response and get the matched cases
        result = self.parse_search_results(soup, first_name, last_name)
        # print(json.dumps(result, indent=4, sort_keys=True))
        if 'error' in result:
            return {'error': result['error']}
        else:
            return {'result': result['cases']}


if __name__ == "__main__":
    print(json.dumps(ScraperTXTravisSuperior().scrape(search_parameters={
          'firstName': 'John', 'lastName': 'Washington', 'dob': None})['result'], indent=4, sort_keys=True))
    print('Done running', __file__, '.')
