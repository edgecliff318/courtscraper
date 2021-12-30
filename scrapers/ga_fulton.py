""" Scraper for Fulton Superior Court """
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir) +'/libraries')
import requests
import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from base import NameNormalizer, TextNormalizer, ScraperBase, InitializedSession, get_recaptcha_answer


class ScraperGAFultonSuperior(ScraperBase):
    """ AZ Maricopa Superior Court scraper """

    HEADERS = {}
    BASE_URL = "https://publicrecordsaccess.fultoncountyga.gov/Portal/"
    HOME_URL = "https://publicrecordsaccess.fultoncountyga.gov/Portal/Home/Dashboard/29"
    FINANCIAL_URL = "https://publicrecordsaccess.fultoncountyga.gov/Portal/Case/CaseDetail/LoadFinancialInformation"
    SEARCH_RESULT_URL = "https://publicrecordsaccess.fultoncountyga.gov/Portal/SmartSearch/SmartSearchResults"

    def scrape(self, search_parameters):
        """ Entry point for lambda.

        Query should look like this:

        {
            "lastName": "Baker",
            "firstName": "Stuart",
            "dob": ""
        }

        https://<endpoint>?queryStringParameters
        """

        last_name = search_parameters["lastName"]
        first_name = search_parameters["firstName"]
        dob = search_parameters["dob"]
        return self.search_in_fulton_ga(first_name, last_name, dob)

    # get cookie(including the cookie that contains search criteria) by using selenium
    def get_cookie(self, input_string):
        """ Get cookie from Search Result Page by using firstName and lastName.

        input_string(firstName+lastName) will be entered to Search Input in Search Page of the website automatically on Selenium chromedriver.
        To submit the Search Form with this input, we should pass the google recaptcha with sitekey.
        In this website, they don't send the input string like firstName and lastName with form_data or parameters.
        They get that information from cookie that is returned by server.(when we click submit button)

        This function returns an object.
        """
        driver = webdriver.Chrome('./chromedriver.exe')
        # driver = webdriver.Chrome(ChromeDriverManager().install())

        driver.get(self.HOME_URL)

        # fill up the search input with input_string
        search_form = driver.find_element_by_css_selector(
            '#SearchCriteriaContainer input.form-control')
        driver.execute_script(
            """arguments[0].value = '{}'""".format(input_string), search_form)

        # get site_key for google recaptcha
        site_key = driver.find_element_by_class_name(
            'g-recaptcha').get_attribute('data-sitekey')
        # get recaptcha_answer with 2captcha service
        recaptcha_answer = get_recaptcha_answer(site_key, self.HOME_URL)
        print(recaptcha_answer)

        # fill up the recaptcha_answer to recaptcha_response textarea to overcome the recaptcha
        recaptcha_response = driver.find_element_by_class_name(
            'g-recaptcha-response')
        driver.execute_script("""arguments[0].innerHTML = '{}'""".format(
            recaptcha_answer), recaptcha_response)

        # go to the search results page by clicking submit button
        submit_button = driver.find_element_by_css_selector('#btnSSSubmit')
        submit_button.click()

        # build the cookie list
        cookies_list = driver.get_cookies()
        cookies = {}
        for cookie in cookies_list:
            cookies[cookie['name']] = cookie['value']
        print(cookies)
        return cookies

    def get_case_information(self, soup):
        """ Parse initial case information using rendered HTML page.

        This function returns an object.
        """
        case_information_body = soup.find(
            'div', {'id': 'divCaseInformation_body'})
        if not case_information_body:
            return []
        case_information = {}
        items = case_information_body.findAll('div', class_='col-md-4')
        for item in items:
            label = item.find('span', class_='text-muted').text
            value = item.text.strip().replace(label, '').strip()
            case_information[label] = value
        return case_information

    def get_disposition_information(self, soup):
        """ Parse disposition information of case detail using rendered HTML page.

        This function returns an object array.
        """
        disposition_information_body = soup.find(
            'div', {'id': 'dispositionInformationDiv'})
        disposition_information = []
        if disposition_information_body:
            items = disposition_information_body.find('div', class_='row-buff')
            if not items:
                return []
            for item in items.findAll('div', class_='row-buff'):
                if not item.find('div', class_='tyler-toggle-container'):
                    continue
                position = ''
                name = ''
                if item.find('div', class_='tyler-toggle-container').find('p'):
                    if item.find('div', class_='tyler-toggle-container').find('p').find('span', class_='text-muted'):
                        position = item.find('div', class_='tyler-toggle-container').find(
                            'p').find('span', class_='text-muted').text.strip()
                    name = item.find(
                        'div', class_='tyler-toggle-container').find('p').text.strip().replace(position, '')
                dispositionItem = {
                    'date': item.find('div', class_='tyler-toggle-controller').text.replace('\n', '').replace('   ', ' ').strip(),
                    'position': position,
                    'name': name,
                    'details': []
                }

                items = item.find('div', class_='tyler-toggle-container')
                if not items or not items.find('div'):
                    return []
                for item in items.find('div').findAll('tr'):
                    cells = item.findAll('td')
                    if len(cells) > 2:
                        description = cells[0].text.strip()
                        disposition = cells[1].text.strip()
                        dispositionItem['details'].append({
                            'description': description,
                            'disposition': disposition,
                        })
                disposition_information.append(dispositionItem)
        return disposition_information

    def get_party_information(self, soup):
        """ Parse party information of case detail using rendered HTML page.

        This function returns an object array.
        """
        party_information_body = soup.find(
            'div', {'id': 'partyInformationDiv'})
        party_information = {}
        if party_information_body:
            items = party_information_body.find('div', class_='col-md-8')
            if not items:
                return []
            for item in items.findAll('p'):
                if item.find('span'):
                    label = item.find('span').text.replace('\n', '').replace(
                        '\r', '').replace('    ', '').strip()
                else:
                    label = 'Address'
                value = item.text.replace(label, '').replace(
                    '\n', '').replace('\r', '').replace('    ', '').strip()
                party_information[label] = value
        return party_information

    def get_charge_information(self, soup):
        """ Parse charge information of case detail using rendered HTML page.

        This function returns an object.
        """
        charge_information_body = soup.find(
            'div', {'id': 'chargeInformationDiv'})
        charge_information = {}
        if charge_information_body:
            charges = ''
            if len(charge_information_body.findAll('div', class_='col-md-12')) > 1:
                charges = charge_information_body.findAll(
                    'div', class_='col-md-12')[1].text.replace('Charges', '').strip()
            charge_information = {
                'name': charges,
                'charges': []
            }
            items = charge_information_body.findAll('tr')
            for item in items:
                cells = item.findAll('td')
                if len(cells) > 5:
                    description = cells[2].text.strip()
                    statute = cells[3].text.strip()
                    level = cells[4].text.strip()
                    date = cells[5].text.strip()
                    charge_information['charges'].append({
                        'Description': description,
                        'Statute': statute,
                        'Level': level,
                        'Date': date
                    })
        return charge_information

    def get_events_information(self, soup):
        """ Parse event information of case detail using rendered HTML page.

        This function returns an object array.
        """
        events_information_body = soup.find(
            'div', {'id': 'eventsInformationDiv'})
        events_information = []
        if events_information_body:
            items = events_information_body.find('ul', class_='list-group')
            if not items:
                return []
            for item in items.findAll('li', class_='list-group-item'):
                if item.find('div', class_='tyler-toggle-controller'):
                    event = {
                        'Event': item.find('div', class_='tyler-toggle-controller').text.replace('\n', '').replace('   ', ' ').strip()
                    }
                    options = item.find(
                        'div', class_='tyler-toggle-container').findAll('p')
                    for option in options:
                        label = option.find('span', class_='text-muted').text
                        value = option.text.strip().replace(label, '').replace('     ', '').strip()
                        event[label] = value
                else:
                    event = {
                        'Event': item.find('p', class_='text-primary').text.strip()
                    }
                events_information.append(event)
        return events_information

    def get_financial_information(self, financial_information_body):
        """ Parse financial information of case detail using rendered HTML page.

        This function returns an object.
        """
        financial_information = {}
        if financial_information_body:
            financial_information = {'financials': []}
            items = financial_information_body.findAll('div', class_='row')
            for item in items:
                if item.find('p', class_='text-primary'):
                    financial_information['name'] = item.find(
                        'p', class_='text-primary').text.strip()
                elif item.find('div', class_='text-left'):
                    label = item.find('div', class_='text-left').text.strip()
                    value = item.find('div', class_='text-right').text.strip()
                    financial_information[label] = value
                else:
                    rows = item.findAll('tr')
                    for row in rows:
                        cells = row.findAll('td')
                        if len(cells) > 4:
                            date = cells[0].text.strip()
                            financialType = cells[1].text.strip()
                            receipt = cells[2].text.strip()
                            name = cells[3].text.strip()
                            amounts = cells[4].text.strip()
                            financial_information['financials'].append({
                                'date': date,
                                'type': financialType,
                                'amounts': amounts,
                                'receipt': receipt,
                                'name': name
                            })
        return financial_information

    def get_case_detail(self, case_detail_url, case_id):
        """ Get every information of case detail by passing HTML page what we get with case_detail_url and case_id to parse functions

        This function returns an object.
        """

        try:
            ts = int(time.time())
            url = "{}?_={}".format(case_detail_url, ts)
            payload = {}
            response = requests.request(
                "GET", url, headers=self.HEADERS, data=payload)
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")

        soup = BeautifulSoup(response.text, features="html.parser")
        case_information = self.get_case_information(soup)
        case_information['party'] = self.get_party_information(soup)
        case_information['charges'] = self.get_charge_information(soup)
        case_information['events'] = self.get_events_information(soup)
        case_information['dispositions'] = self.get_disposition_information(
            soup)

        try:
            ts = int(time.time() * 1000)
            url = "{}?caseId={}&_={}".format(self.FINANCIAL_URL, case_id, ts)
            payload = {}
            response = requests.request(
                "GET", url, headers=self.HEADERS, data=payload)
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
        soup = BeautifulSoup(response.text, features="html.parser")

        case_information['financials'] = self.get_financial_information(soup)
        return case_information

    def get_search_result(self, html):
        """ Parse rendered HTML page for search result and get matched cases

        This function returns an array.
        """
        if len(html.split(',"data":')) > 1 and len(html.split(',"data":')[1].split("""},"detailTemplate":kendo.template($('#PartyCardTemplate')""")) > 0 and 'Data' in json.loads(html.split(',"data":')[1].split("""},"detailTemplate":kendo.template($('#PartyCardTemplate')""")[0]):
            return json.loads(html.split(',"data":')[1].split("""},"detailTemplate":kendo.template($('#PartyCardTemplate')""")[0])['Data']
        return []

    def search_in_fulton_ga(self, first_name, last_name, dob):
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

        input_string = last_name + ', ' + first_name
        cookies = self.get_cookie(input_string)
        # build the headers for request with built cookie list
        # BNES_SmartSearchCriteria will contain search criteria information

        self.HEADERS = {
            'Cookie': 'BNI_reco_cookie02684616={}; BNI_reco_cookie02684616={}; BNI_reco_cookie02684616={}; BNES_ASP.NET_SessionId={}; BNES_SameSite=0KCds494YizK+0ffxndFt9/4dsqCwi4btM9Ei3JM+NJDD2zFRISf/DsPxbfMdcjx5/JCk+o6Gg8=; BNES_SmartSearchCriteria={}'.format(cookies['BNI_reco_cookie02684616'], cookies['BNI_reco_cookie02684616'], cookies['BNI_reco_cookie02684616'], cookies['BNES_ASP.NET_SessionId'], cookies['BNES_SmartSearchCriteria'])
        }

        try:
            ts = int(time.time() * 1000)
            # get search results(maybe cases by person will be returned as a response)
            url = "{}?_={}".format(self.SEARCH_RESULT_URL, ts)
            payload = {}
            response = requests.request(
                "GET", url, headers=self.HEADERS, data=payload)
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")

        # cases by person will be returned as a response
        matches = self.get_search_result(response.text)

        for mInd, match in enumerate(matches):
            for cInd, case in enumerate(match['CaseResults']):
                case_detail_url = case['CaseLoadUrl']
                case_id = case['CaseId']
                # get case detail from detail page
                # case_id will be necessary to get financial information for the case
                matches[mInd]['CaseResults'][cInd]['CaseDetail'] = self.get_case_detail(
                    case_detail_url, case_id)
        return {'result': matches}


if __name__ == "__main__":
    # print(json.dumps(search_in_fulton('Stuart', 'Baker', ''), indent=4, sort_keys=True))
    # get_case_detail('https://publicrecordsaccess.fultoncountyga.gov/Portal/Case/CaseDetail?eid=SX3lDQI_7NOnUErm0POGSw2&tabIndex=3', 2988942)
    print(json.dumps(ScraperGAFultonSuperior().scrape(search_parameters={
          'firstName': 'Stuart', 'lastName': 'Baker', 'dob': ''})['result'], indent=4, sort_keys=True))
    print('Done running', __file__, '.')
