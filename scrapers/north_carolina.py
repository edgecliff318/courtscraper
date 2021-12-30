""" Scraper for North Carolina Superior Court """
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir) +'/libraries')
import requests
import json
from bs4 import BeautifulSoup 

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from base import NameNormalizer, TextNormalizer, ScraperBase, InitializedSession

class ScraperNCSuperior(ScraperBase):
    """ NC Superior Court scraper """

    HEADERS = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    BASE_URL = 'https://webapps.doc.state.nc.us/opi/'
    SEARCH_RESULT_URL = 'https://webapps.doc.state.nc.us/opi/offendersearch.do?method=list'
    SEARCH_URL = 'https://webapps.doc.state.nc.us/opi/offendersearch.do?method=view'

    def scrape(self, search_parameters):
        """ Entry point for lambda.

        Query should look like this:

        {
            "lastName": "Smith",
            "firstName": "Adam",
            "dob": "12/19/1967"
        }
        https://<endpoint>?queryStringParameters
        """
        last_name = search_parameters["lastName"]
        first_name = search_parameters["firstName"]
        dob = search_parameters["dob"]
        return self.search_in_nc(first_name, last_name, dob)

    GLOBAL_SESSION = InitializedSession(headers = HEADERS)

    def parse_offender_information(self, soup):
        """ Get offender information by parsing rendered HTML page

        This function returns an object.
        """
        offender_information = {}
        offender_informaion_table = soup.find('table', class_='displaydatatable')
        if not offender_informaion_table: return {}
        for row in offender_informaion_table.findAll('tr'):
            cells = row.findAll('td')
            print(cells)
            if len(cells) == 1 and 'Printable Version' not in row.text.strip():
                offender_information['Full Name'] = row.text.strip()
            elif len(cells) == 2 and cells[0].text.strip() != '':
                offender_information[cells[0].text.strip()] = cells[1].text.strip()

        return offender_information

    def parse_names_of_record(self, soup):
        """ Get names of record by parsing rendered HTML page

        This function returns an array.
        """
        offender_names = []
        offender_names_table = soup.find('table', class_='datainput')
        if not offender_names_table: return {}
        for row in offender_names_table.findAll('tr'):
            cells = row.findAll('td')
            if row.has_key('class') and row['class'][0] != 'tableRowHeader':
                last_name = cells[0].text.strip()
                suffix = cells[1].text.strip()
                first_name = cells[2].text.strip()
                middle_name = cells[3].text.strip()
                name_type = cells[4].text.strip()
                offender_names.append({
                    "last_name": last_name,
                    "suffix": suffix,
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "name_type": name_type
                })

        return offender_names

    def parse_sentence_table(self, table):
        """ Get sentence information by parsing rendered table element

        This function returns an object.
        """
        sentence_information = {}
        sentence_information_table = table.find('table', class_='innerdisplaytable')
        if not sentence_information_table: return {}
        key = ''
        for row in sentence_information_table.findAll('tr'):
            if 'align' in row.attrs and row.attrs['align'] == 'center':
                for cell in row.findAll('td'):
                    if 'align' in cell.attrs:
                        if cell.attrs['align'] == 'right':
                            key = cell.text.strip()
                        elif cell.attrs['align'] == 'left' and key != '':
                            sentence_information[key] = cell.text.strip()
            elif row.find('td', class_='sentencepanel'):
                data_table = row.find('table', class_='datainput')
                sentence_information['commitments'] = []
                for data_row in data_table.findAll('tr'):
                    cells = data_row.findAll('td')
                    if data_row.has_key('class') and (data_row['class'][0] == 'tableRowOdd' or data_row['class'][0] == 'tableRowEven'):
                        commitment = cells[0].text.strip()
                        docket = cells[1].text.strip()
                        offense = cells[2].text.strip()
                        offense_date = cells[3].text.strip()
                        commitment_type = cells[4].text.strip()
                        class_code = cells[5].text.strip()
                        sentence_information['commitments'].append({
                            'Commitment': commitment, 
                            'Docket#': docket,
                            'Offense (Qualifier)': offense,
                            'Offense Date': offense_date, 
                            'Type': commitment_type,
                            'Sentencing Penalty Class Code': class_code
                        })
        return sentence_information

    def parse_sentence_history(self, soup):
        """ Get sentence history by parsing rendered HTML page

        This function returns an array.
        """
        offender_sentences = []

        for sentence_table in soup.findAll('table', class_='sentencedisplaytable'):
            offender_sentences.append(self.parse_sentence_table(sentence_table))

        return offender_sentences

    def get_offender_detail(self, soup):
        """ Get every information of offender detail by parsing rendered HTML page

        This function returns an object.
        """
        return {
            "offender_information": self.parse_offender_information(soup),
            "names_of_record": self.parse_names_of_record(soup),
            "sentence_history": self.parse_sentence_history(soup)
        }
    def parse_search_results(self, soup):
        """ Parse rendered HTML page for search result and get de-duped offenders
        
        This function returns an array.
        """
        offenders = []
        offender_keys = []
        offender_table = soup.find('table', class_='resultstable')
        if not offender_table: return []
        offender_rows = offender_table.findAll('tr')
        for offender_row in offender_rows:
            cells = offender_row.findAll('td')
            if offender_row.has_key('class') and (offender_row['class'][0] == 'tableRowOdd' or offender_row['class'][0] == 'tableRowEven'):
                offender_number = cells[0].text.strip()
                if offender_number in offender_keys: continue
                offender_keys.append(offender_number)
                last_name = cells[1].text.strip()
                name_suffix = cells[2].text.strip()
                first_name = cells[3].text.strip()
                middle_name = cells[4].text.strip()
                gender = cells[5].text.strip()
                race = cells[6].text.strip()
                birth_date = cells[7].text.strip()
                age = cells[8].text.strip()
                offender_url = ''
                if cells[0].find('a'):
                    offender_url = self.BASE_URL + cells[0].find('a').attrs['href']
                offenders.append({
                    "offender_number": offender_number,
                    "last_name": last_name,
                    "name_suffix": name_suffix,
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "gender": gender,
                    "race": race,
                    "birth_date": birth_date,
                    "age": age,
                    "offender_url": offender_url
                })
        return offenders

    def search_in_nc(self, first_name, last_name, dob):
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
                "heightTotalInchesMinimum": "0",
                "heightTotalInchesMaximum": "0",
                "activeFilter": "1",
                "searchLastName": "Smith",
                "searchFirstName": "Adam",
                "searchMiddleName": "",
                "searchOffenderId": "",
                "searchGender": "",
                "searchRace": "",
                "ethnicity": "",
                "searchDOB": "12/19/1967",
                "searchDOBRange": "0",
                "ageMinimum": "",
                "ageMaximum": "",
            })
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {'error': str(e)}
        soup = BeautifulSoup(r.text, features="html.parser")
        
        # parse html response and get the matched cases
        offenders = self.parse_search_results(soup)
        result = []
        for offender in offenders:
            try:
                r = self.GLOBAL_SESSION.get(offender['offender_url'])
                soup = BeautifulSoup(r.text, features="html.parser")
                offender['detail'] = self.get_offender_detail(soup)
            except requests.ConnectionError as e:
                print("Connection failure : " + str(e))
                print("Verification with InsightFinder credentials Failed")
            result.append(offender)
        return {'result': result}
        # print(json.dumps(result, indent=4, sort_keys=True))
        # if 'error' in result:
        #     return {'error': result['error']}
        # else:
        #     return {'result': result['cases']}  

if __name__ == "__main__":
    print(json.dumps(ScraperNCSuperior().scrape(search_parameters={
          'firstName': 'Adam', 'lastName': 'Smith', 'dob': '12/19/1967'})['result'], indent=4, sort_keys=True))
    print('Done running', __file__, '.')
