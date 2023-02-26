""" Scraper for Riverside Superior Court """
from bs4 import BeautifulSoup
import csv
from src.scrapers.base import NameNormalizer, TextNormalizer, ScraperBase, InitializedSession
import json
import requests
from datetime import datetime
import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), os.pardir) + '/libraries')

sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), os.pardir))


class ScraperCARiversideSuperior(ScraperBase):
    """ CA Riverside Superior Court scraper """

    HEADERS = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    LOGON_URL = 'http://public-access.riverside.courts.ca.gov/OpenAccess/logon.asp?system=CRIMINAL'
    HOME_URL = 'http://public-access.riverside.courts.ca.gov/OpenAccess/CriminalMainMenu.asp'
    SEARCH_CASE_URL = 'http://public-access.riverside.courts.ca.gov/OpenAccess/Criminal/CriminalSearchByNameDOB.asp'
    CASE_DETAIL_URL = 'http://public-access.riverside.courts.ca.gov/OpenAccess/Criminal/CriminalCaseReport.asp'

    def scrape(self, search_parameters):
        """ Entry point for lambda.

        Query should look like this:

        {
            "lastName": "Joyce",
            "firstName": "Washington",
            "dob": "1/23/1961"
        }
        https://<endpoint>?queryStringParameters
        """

        last_name = search_parameters["lastName"]
        first_name = search_parameters["firstName"]
        dob = search_parameters["dob"]
        return self.search_in_riverside_ca(first_name, last_name, dob)

    GLOBAL_SESSION = InitializedSession(headers=HEADERS)

    def parse_case_detail(self, soup):
        """ Get every information of case detail by parsing rendered HTML page

        This function returns an object.
        """
        tables = soup.findAll('table')
        status = {}
        defendents = []
        charges = {}
        related_cases = []
        actions = []
        fine_information = {}

        for table in tables:
            if 'border' in table.attrs and 'width' not in table.attrs:
                rows = table.findAll('tr')
                if 'Next Court Date' in rows[0].text:
                    count = 0
                    for row in rows:
                        if count > 0:
                            # print(eatspace(row.prettify().replace('\n', '')).split('<td><font color="#000000" face="arial"><small>'))
                            cells = row.text.strip().split('\n')
                            # print(cells)
                            defendents.append({
                                'defendent': cells[1].split('  ')[0].strip(),
                                'next_court_date': cells[2].split('  ')[0].strip(),
                                'status': cells[3].split('  ')[0].strip(),
                                'agency_number': cells[4].split('  ')[0].strip(),
                                'arrest_date': cells[5].split('  ')[0].strip(),
                                'count1_charge': cells[6].split('  ')[0].strip(),
                                'violation_date': cells[7].split('  ')[0].strip()
                            })
                        count = count + 1
                elif 'Custody' in rows[0].text:
                    key = ''
                    for cell in table.text.strip().split('\n'):
                        if key != '' and cell != '':
                            status[key] = cell
                            key = ''
                        elif key == '':
                            key = cell
                    # print(status, '----------------')
                elif 'Warrant' in rows[0].text:
                    key = ''
                    row = rows[1].text.split('\n')
                    if len(row) == 7:
                        status['warrant'] = {
                            'type': row[2].strip(),
                            'status': row[3].strip(),
                            'issued': row[4].strip(),
                            'affidavit': row[5].strip()
                        }
                    row = rows[3].text.split('\n')
                    if len(row) == 6:
                        status['probation'] = {
                            'type': row[2].strip(),
                            'granted': row[3].strip(),
                            'expiration': row[4].strip()
                        }
                    row = rows[5].text.split('\n')
                    if len(row) == 6:
                        status['sentence'] = {
                            'convicted_date': row[2].strip(),
                            'fine_and_penalty': row[3].strip(),
                            'restitution_fine': row[4].strip()
                        }
                elif 'Filed Charges' in table.text:
                    if len(rows[2].text.split('\n')) > 1:
                        if len(rows[2].text.split('\n')[1].split('\xa0')) > 6:
                            row = rows[2].text.split('\n')[1].split('\xa0')
                            charges['count'] = row[0]
                            charges['charge'] = row[1]
                            charges['severity'] = row[2]
                            charges['description'] = row[3]
                            charges['violation_date'] = row[4]
                            charges['plea'] = row[5]
                            charges['status'] = row[6]
                elif 'Related Cases On Calendar' in table.text:
                    count = 0

                    for row in rows:
                        if count > 0:
                            related_cases.append(row.text)
                        count = count + 1
                elif 'Action Date' in table.text:
                    count = 0
                    action = {}
                    for row in rows:
                        if count > 0:
                            cells = row.findAll('td')

                            if len(cells) != 4:
                                action['minutes'] = []
                                for cell in row.text.strip().split('\n'):
                                    if 'Minutes' not in cell and cell.strip() != '':
                                        action['minutes'].append(cell.strip())
                                actions.append(action)
                                action = {}
                            else:
                                if action != []:
                                    actions.append(action)
                                    action = {}
                                action['action_date'] = cells[0].text.strip()
                                action['action_text'] = cells[1].text.strip()
                                action['disposition'] = cells[2].text.strip()
                                action['hearing_type'] = cells[3].text.strip()

                            # related_case.append(row.text)
                        count = count + 1
                elif 'Date To Pay' in table.text:
                    key = ''
                    for cell in table.text.strip().split('\n'):
                        if key != '' and cell.strip() != '':
                            fine_information[key.replace(
                                ':', '').strip()] = cell.strip()
                            key = ''
                        elif key == '' and cell.strip() != '':
                            key = cell

                elif 'Fine Number' in table.text:
                    fine_information['fine_list'] = []
                    count = 0
                    for row in rows:
                        if count > 0:
                            cells = row.text.strip().split('\n')
                            if len(cells) > 5:
                                fine_information['fine_list'].append({
                                    'fine_type': cells[1].strip(),
                                    'fine_description': cells[2].strip(),
                                    'original_amount': cells[3].strip(),
                                    'paid_to_date': cells[4].strip(),
                                    'current_date': cells[5].strip(),
                                })
                        count = count + 1

        return {
            'status': status,
            'defendents': defendents,
            'charges': charges,
            'related_cases': related_cases,
            'actions': actions,
            'fine_information': fine_information
        }

    def parse_search_results(self, soup):
        """ Parse rendered HTML page for search result and get matched cases

        This function returns an array.
        """
        cases = []
        search_matches_container = soup.find(
            'div', {'id': 'divNameSearchMatches'})
        if not search_matches_container:
            return []

        case_rows = search_matches_container.findAll('tr')

        count = 1
        for row in case_rows:
            if count > 1:
                cells = row.findAll('td')
                charges = []
                charges_list = cells[3].findAll('span', class_='charges')
                for item in charges_list:
                    charges.append(item.text.strip().replace('\u00a0', ' '))
                cases.append({
                    'case_number': cells[0].text.strip(),
                    'name': cells[1].text.strip(),
                    'filing_date': cells[2].text.strip(),
                    'charges': charges,
                    'next_hearing': cells[4].text.strip().replace('\u00a0', ' '),
                    'jurisdiction': cells[5].text.strip()
                })
            count = count + 1
        return cases

    def convertDobToStr(self, dob):
        """ Convert given dob to expected dob string
        expected dob for api is 19610123 - YYYYMMDD

        This function returns string.
        """
        return datetime.strftime(datetime.strptime(dob, '%m/%d/%Y'), '%Y%m%d')

    def search_in_riverside_ca(self, first_name, last_name, dob):
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
            r = self.GLOBAL_SESSION.get(self.HOME_URL)
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {'error': str(e)}

        try:
            r = self.GLOBAL_SESSION.get(self.LOGON_URL)
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {'error': str(e)}

        try:
            r = self.GLOBAL_SESSION.post(self.LOGON_URL, {
                'validatelogon': 'Y',
                'system': 'CRIMINAL',
                'Typed': '',
                'courtcode': '',
                'username': '',
                'password': ''
            })
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {'error': str(e)}

        try:
            r = self.GLOBAL_SESSION.post(self.SEARCH_CASE_URL, {
                "hidDOB": dob_string,
                "hidCourtCode": "B",
                "hidCourtCodeNumber": "1",
                "hidRivInd": "IND",
                "ShowMatches": "TRUE",
                "hidRowIDList": "ODAAAsncAAcAAAQYeAAb,ODAAAsncAAcAAAPtCAA9,ODAAAsncAAcAAAHx5AA4",
                "ReturnToURL": "http%3A%2F%2Fpublic%2Daccess%2Eriverside%2Ecourts%2Eca%2Egov%2FOpenAccess%2FCriminalSearchByNameDOB%2Easp%3FtxtLastName%3D{}%26txtFirstName%3D{}%26txtMiddleName%3D%26ShowMatches%3DFalse%26MatchNumber%3D%26optPerBusInd%3DPER%26hidRivInd%3DIND%26hidDOB%3D{}".format(last_name, first_name, dob_string),
                "MatchNumber": "1",
                "hidPerBusInd": "PER",
                "hidNameSearchMatches": "",
                "Typed": " ",
                "dropCourtCode": "IND",
                "optPerBusInd": "PER",
                "txtLastName": last_name,
                "txtFirstName": first_name,
                "txtMiddleName": ""
            })
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {'error': str(e)}
        # parse html response and get the matched cases
        cases = self.parse_search_results(
            BeautifulSoup(r.text, features="html.parser"))

        for case in cases:
            url = '{}?CourtCode=C&RivInd=IND&CaseNumber={}&DefNbr=175830&DefSeq=1&otnmseq=0'.format(
                self.CASE_DETAIL_URL, case['case_number'])
            try:
                r = self.GLOBAL_SESSION.get(url)
            except requests.ConnectionError as e:
                print("Connection failure : " + str(e))
                print("Verification with InsightFinder credentials Failed")
                return {'error': str(e)}
            soup = BeautifulSoup(r.text, features="html.parser")
            case['case_detail'] = self.parse_case_detail(soup)

        return {'result': cases}


if __name__ == "__main__":
    print(json.dumps(ScraperCARiversideSuperior().scrape(search_parameters={
          'firstName': 'Joyce', 'lastName': 'Washington', 'dob': '1/23/1961'})['result'], indent=4, sort_keys=True))
    print('Done running', __file__, '.')
