""" Scraper for San Diego Superior Court """
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir) +'/libraries')
from datetime import datetime
import requests
import json
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from base import NameNormalizer, TextNormalizer, ScraperBase, InitializedSession


class ScraperCASanDiegoSuperior(ScraperBase):
    """ CA San Diego Superior Court scraper """

    HEADERS = {
        'Cookie': 'f5avrbbbbbbbbbbbbbbbb=LBGHFOKMEPDNFOKHHDHIKAEDJGLEGOBNLKIFKPOKCODJDMLPOIEFKMONINACBPOANDJIPDFDGJCDHKPDKKDHEILOMGEAFECEFECAKDCHELCHINONFFCCINOJGFPHFNIC; _ga=GA1.2.258218475.1588935386; _gid=GA1.2.448862907.1589269663; ASP.NET_SessionId=jai1q23npcy2tdauzpiqtagm; __RequestVerificationToken_L09ubGluZUNhc2VJbmZvcm1hdGlvbldlYg2=ewAYv6ywvlpgLYDkDQ7aC-mFUyP-8JgmXdtw5C_lMj9y14YrMHWZEaBHIZoiudakojLDVTHMm37gIEwG4yD169Uo7sC3c_hx6gp3mRneUtU1; TS01508fb5_28=01b2c09b80fd5264c3325b6b657e7a4ba0c56cf438812186c1622902c514feb41e738b8018160608672126e572749fcb0ad2fbb49e; TS01508fb5=01798eb63477113256840bed946de5b599cacf68a0c34359c86f4772fbc14b62a7da0fbc4bcf78b135987b0c0c9debc15bf23509ea193b52c03328c99fc8ffb89c3502da5bdf7789e90adf38f762f12dd524b70cb4ea9f0b3528bc60283708fc413c05b03be84a337fe0bef1713b8bcf149602fbdb; _gat=1',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    BASE_URL = 'http://courtindex.sdcourt.ca.gov'
    SEARCH_RESULT_URL = 'http://courtindex.sdcourt.ca.gov/CISPublic/viewname'

    def scrape(self, search_parameters):
        """ Entry point for lambda.

        Query should look like this:

        {
            "lastName": "Zeus",
            "firstName": "Robles",
            "dob": "1986-07-03"
        }
        https://<endpoint>?queryStringParameters
        """
        last_name = search_parameters["lastName"]
        first_name = search_parameters["firstName"]
        dob = search_parameters["dob"]
        return self.search_in_san_diego_ca(first_name, last_name, dob)

    GLOBAL_SESSION = InitializedSession(headers=HEADERS)

    def parse_case_detail(self, soup):
        """ Get every information of case detail by parsing rendered HTML page

        This function returns an object.
        """
        case_detail = {}
        tables = soup.findAll('table')
        case_title = ''
        defendants = []
        imaged_cases = []
        microfilms = []
        if len(tables) > 3:
            case_title = tables[1].findAll(
                'tr')[0].text.replace('Case Title:', '').strip()

            defendants_rows = tables[2].findAll('tr')
            for row in defendants_rows:
                if 'bgcolor' not in row.attrs:
                    cells = row.findAll('td')
                    if len(cells) > 4:
                        last_name = cells[0].text.strip()
                        first_name = cells[1].text.strip()
                        birth_year = cells[2].text.strip()
                        aka = cells[3].text.strip()
                        da_number = cells[4].text.strip()
                        defendants.append({
                            'last_name': last_name,
                            'first_name': first_name,
                            'birth_year': birth_year,
                            'aka': aka,
                            'DA_number': da_number
                        })

            imaged_case_rows = tables[3].findAll('tr')
            for row in imaged_case_rows:
                if 'bgcolor' not in row.attrs:
                    imaged_cases.append(row.text.strip())

            microfilm_rows = tables[4].findAll('tr')
            for row in microfilm_rows:
                if 'bgcolor' not in row.attrs:
                    cells = row.findAll('td')
                    if len(cells) > 3:
                        microfilm_id = cells[0].text.strip()
                        location = cells[1].text.strip()
                        reel_number = cells[2].text.strip()
                        frame_number = cells[3].text.strip()

                        microfilms.append({
                            'microfilm_id': microfilm_id,
                            'location': location,
                            'reel_number': reel_number,
                            'frame_number': frame_number
                        })
        case_detail['case_title'] = case_title
        case_detail['defendants'] = defendants
        case_detail['microfilms'] = microfilms
        case_detail['imaged_cases'] = imaged_cases

        return case_detail

    def parse_search_results(self, soup):
        """ Parse rendered HTML page for search result and get matched cases

        This function returns an array.
        """
        cases = []
        case_table = soup.find('table', class_='data')
        if not case_table:
            return []
        case_rows = case_table.findAll('tr')
        count = 0
        for case_row in case_rows:
            if count == 0:
                count = 1
                continue
            cells = case_row.findAll('td')
            if len(cells) > 5:
                case_number = cells[0].text.strip()
                party_name = cells[1].text.strip()
                birth_year = cells[2].text.strip()
                case_location = cells[3].text.strip()
                case_type = cells[4].text.strip()
                date_filed = cells[5].text.strip()
                case_url = ''
                if cells[0].find('a'):
                    case_url = self.BASE_URL + cells[0].find('a').attrs['href']
                cases.append({
                    'case_number': case_number,
                    'party_name': party_name,
                    'birth_year': birth_year,
                    'case_location': case_location,
                    'case_type': case_type,
                    'date_filed': date_filed,
                    'case_url': case_url,
                })
        return cases

    def convertDobToStr(self, dob):
        """ Convert given dob to expected dob string
        expected dob for api is 1961-01-23 - YYYY-MM-DD

        This function returns string.
        """
        return datetime.strftime(datetime.strptime(dob, '%m/%d/%Y'), '%Y-%m-%d')

    def search_in_san_diego_ca(self, first_name, last_name, dob):
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

        dob_string = self.convertDobToStr(dob)
        print(dob_string)
        try:
            r = self.GLOBAL_SESSION.post(self.SEARCH_RESULT_URL, {
                'caseType': 'R',
                "site": "A",
                "partyType": "A",
                "fileDateBegin": "1974",
                "fileDateEnd": "2020",
                "lastname": last_name,
                "firstname": first_name,
                "dateOfBirth": dob_string,
                "page": "1",
            })
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {'error': str(e)}
        soup = BeautifulSoup(r.text, features="html.parser")

        # parse html response and get the matched cases
        cases = self.parse_search_results(soup)

        for case in cases:
            try:
                r = self.GLOBAL_SESSION.get(case['case_url'])
            except requests.ConnectionError as e:
                print("Connection failure : " + str(e))
                print("Verification with InsightFinder credentials Failed")
                return {'error': str(e)}

            case['case_detail'] = self.parse_case_detail(
                BeautifulSoup(r.text, features="html.parser"))
        return {'result': cases}


if __name__ == "__main__":
    print(json.dumps(ScraperCASanDiegoSuperior().scrape(search_parameters={
          'firstName': 'Zeus', 'lastName': 'Robles', 'dob': '07/03/1986'})['result'], indent=4, sort_keys=True))
    print('Done running', __file__, '.')
