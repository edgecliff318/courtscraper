""" Scraper for Orange Superior Court """
import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), os.pardir) + '/libraries')
from bs4 import BeautifulSoup
import json
from datetime import datetime
import requests
import re


sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), os.pardir))

from base import NameNormalizer, TextNormalizer, ScraperBase, InitializedSession, get_recaptcha_answer, SPLASH_USERNAME, SPLASH_PASSWORD, SPLASH_URL

sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), os.pardir) + '/libraries')


sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), os.pardir))


class ScraperFLOrangeSuperior(ScraperBase):
    """ FL Orange Superior Court scraper """

    HEADERS = {
        'Content-Type': 'application/json',
        'Cookie': 'ASP.NET_SessionId=mtipf4dilcyc1qtyyiri4fmi; __RequestVerificationToken=LWFE8f4cSaJEveboRdoR-ZtRhAOIAOhy1CX6EQNFEGOtX2F0vALssEcH2amxuB-SlzcN_u37GXgwSZqzYm6QPaoTKQwoMR3StxE8j6eLrjs1;  _ga=GA1.2.373529061.1592671700; _gid=GA1.2.1034634101.1592671700',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'
    }
    BASE_URL = 'https://myeclerk.myorangeclerk.com/'
    SEARCH_URL = 'https://myeclerk.myorangeclerk.com/Cases/Search'
    SITE_KEY = ''
    FIRST_NAME = ''
    LAST_NAME = ''
    DOB = ''
    RETRY_LIMIT = 5

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
        return self.search_in_orange_fl(first_name, last_name, dob)

    GLOBAL_SESSION = InitializedSession(headers=HEADERS)

    def parse_case_detail(self, soup):
        """ Get every information of case detail with rendered html

        This function returns an object.
        """
        case_detail = {}
        case_header_table = soup.find('div', {'id': 'headerCollapse'})
        if case_header_table:
            for row in case_header_table.findAll('div', class_='row'):
                key = row.find('div', class_='col-md-5').text.strip().replace(':', '')
                case_detail[key] = row.find('div', class_='col-md-7').text.strip()

        parties_table = soup.find('div', {'id': 'partiesCollapse'})
        if parties_table:
            case_detail['Parties'] = []
            for row in parties_table.find('tbody').findAll('tr'):
                cells = row.findAll('td')
                case_detail['Parties'].append({
                    'Name': cells[0].text.strip(),
                    'DOB': cells[1].text.strip(),
                    'Type': cells[2].text.strip(),
                    'Attorney': cells[3].text.strip(),
                    'Atty Phone': cells[4].text.strip()
                })
        
        charge_details_table = soup.find('div', {'id': 'chargeDetailsCollapse'})
        if charge_details_table:
            case_detail['Charge Details'] = []
            for row in charge_details_table.find('tbody').findAll('tr'):
                cells = row.findAll('td')
                case_detail['Charge Details'].append({
                    'Offense Date': cells[0].text.strip(),
                    'Charge': cells[1].text.strip(),
                    'Plea': cells[2].text.strip(),
                    'Arrest': cells[3].text.strip(),
                    'Disposition': cells[4].text.strip(),
                    'Sentence': cells[5].text.strip()
                })
        
        docket_events_table = soup.find('div', {'id': 'docketEventsCollapse'})
        if docket_events_table:
            case_detail['Docket Events'] = []
            for row in docket_events_table.find('tbody').findAll('tr'):
                cells = row.findAll('td')
                case_detail['Docket Events'].append({
                    'Date': cells[0].text.strip(),
                    'Description': cells[1].text.strip(),
                    'Pages': cells[2].text.strip(),
                    'Doc': cells[3].text.strip(),
                    'Request Doc': cells[4].text.strip(),
                })
        
        hearings_table = soup.find('div', {'id': 'hearingsCollapse'})
        if hearings_table:
            case_detail['Hearings'] = []
            for row in hearings_table.find('tbody').findAll('tr'):
                cells = row.findAll('td')
                case_detail['Hearings'].append({
                    'Date': cells[0].text.strip(),
                    'Hearing': cells[1].text.strip(),
                    'Time': cells[2].text.strip(),
                    'Location': cells[3].text.strip(),
                    'Pages': cells[4].text.strip(),
                    'Doc': cells[5].text.strip(),
                })
        
        financial_table = soup.find('div', {'id': 'financeCollapse'})
        if financial_table:
            case_detail['Financial'] = []
            for row in financial_table.find('tbody').findAll('tr'):
                cells = row.findAll('td')
                case_detail['Financial'].append({
                    'Date': cells[0].text.strip(),
                    'Description': cells[1].text.strip(),
                    'Player': cells[2].text.strip(),
                    'Amount': cells[3].text.strip(),
                })

        bonds_table = soup.find('div', {'id': 'bondsCollapse'})
        if bonds_table:
            case_detail['Bonds'] = []
            for row in bonds_table.find('tbody').findAll('tr'):
                cells = row.findAll('td')
                case_detail['Bonds'].append({
                    'Description': cells[0].text.strip(),
                    'Status Date': cells[1].text.strip(),
                    'Bond Status': cells[2].text.strip(),
                    'Image': cells[3].text.strip(),
                    'Amount': cells[4].text.strip(),
                })

        warrants_table = soup.find('div', {'id': 'warrantsCollapse'})
        if warrants_table:
            case_detail['Warrants'] = []
            for row in warrants_table.find('tbody').findAll('tr'):
                cells = row.findAll('td')
                case_detail['Warrants'].append({
                    'Number': cells[0].text.strip(),
                    'Status Description': cells[1].text.strip(),
                    'Issue Date': cells[2].text.strip(),
                    'Service Date': cells[3].text.strip(),
                    'Recall Date': cells[4].text.strip(),
                    'Expiration Date': cells[5].text.strip(),
                    'Warrant Type': cells[6].text.strip(),
                })   
        
        print(json.dumps(case_detail, indent=4, sort_keys=True))
        return case_detail

    def get_case_detail(self, case_number):
        """ Get every information of case detail with given case number

        This function returns an object.
        """
        try:
            captcha_response = get_recaptcha_answer(self.SITE_KEY, self.SEARCH_URL)
            LUA_SCRIPT = '''
                    function main(splash)
                        assert(splash:autoload("https://code.jquery.com/jquery-2.1.3.min.js"))
                        treat = require("treat")

                        assert(splash:go(splash.args.url))
                        assert(splash:wait(2))
                        assert(splash:runjs('$("input[name=FirstName]").val("'..splash.args.first_name..'")'))
                        assert(splash:runjs('$("input[name=LastName]").val("'..splash.args.last_name..'")'))
                        assert(splash:runjs('$("textarea[name=g-recaptcha-response]").val("'..splash.args.captcha_response..'")'))
                        assert(splash:wait(1))

                        local form = splash:select('.form-horizontal')
                        local values = assert(form:form_values())
                        assert(form:submit())
                        assert(splash:wait(5))
                        local search_input = splash:select('input[type=search]')
                        search_input:send_text(splash.args.dob)
                        assert(splash:wait(3))

                        local rows = splash:select_all('table#caseList tbody tr')
                        local case_number = ''
                        for j, row in ipairs(rows) do
                            local case_number_element = splash:select('table#caseList tbody tr:nth-child('..j..')  a.caseLink')
                            if case_number_element then
                                if case_number_element:text() == splash.args.case_number then
                                    case_number = case_number_element:text()
                                    local bounds = case_number_element:bounds()
                                    assert(case_number_element:mouse_click{x=bounds.width/3, y=bounds.height/3})
                                    assert(splash:wait(5))
                                end
                            end
                        end
                        return {
                            url = splash:url(),
                            html = splash:html(),
                            case_number = case_number
                        }
                    end
                '''

            r = self.GLOBAL_SESSION.post(SPLASH_URL, auth=(SPLASH_USERNAME, SPLASH_PASSWORD),
                                        json={'url': self.SEARCH_URL,
                                            'lua_source': LUA_SCRIPT,
                                            'first_name': self.FIRST_NAME,
                                            'last_name': self.LAST_NAME,
                                            'dob': self.DOB,
                                            'captcha_response': captcha_response,
                                            'case_number': case_number
                                            })
            print(case_number)
            
            if 'html' in json.loads(r.text):
                print(json.loads(r.text)['html'])
                print(json.loads(r.text)['case_number'])
                return self.parse_case_detail(BeautifulSoup(json.loads(r.text)['html'], features="html.parser"))
            else:
                print(r.text)
                return {}
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {}

    def parse_search_results(self, soup):
        """ Parse rendered HTML page for search result of specific page and get matched cases
        This function returns an array.
        """
        cases = []
        table = soup.find('table', {'id': 'caseList'})
        if not table:
            return cases
        for row in table.find('tbody').findAll('tr'):
            cells = row.findAll('td')
            cases.append({
                'case_number': cells[1].text.strip(),
                'detail_url': self.BASE_URL + cells[1].find('a').attrs['href'],
                'description': cells[2].text.strip(),
                'type': cells[3].text.strip(),
                'status': cells[4].text.strip(),
                'dob': cells[5].text.strip(),
                'judge_name': cells[6].text.strip(),
                'date': cells[7].text.strip()
            })
        print(json.dumps(cases, indent=4, sort_keys=True))
        return cases

    def search_in_orange_fl(self, first_name, last_name, dob):
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
        self.FIRST_NAME = first_name
        self.LAST_NAME = last_name
        self.DOB = dob

        try:
            r = self.GLOBAL_SESSION.get(self.SEARCH_URL)
            soup = BeautifulSoup(r.text, features="html.parser")
            if soup.find('form', class_='form-horizontal'):
                self.SITE_KEY = soup.find(
                    'div', class_='g-recaptcha').attrs['data-sitekey']
                captcha_response = get_recaptcha_answer(self.SITE_KEY, self.SEARCH_URL)
            else:
                return {'error': 'Server Error'}

            LUA_SCRIPT = '''
                function main(splash)
                    assert(splash:autoload("https://code.jquery.com/jquery-2.1.3.min.js"))
                    treat = require("treat")

                    assert(splash:go(splash.args.url))
                    assert(splash:wait(2))
                    assert(splash:runjs('$("input[name=FirstName]").val("'..splash.args.first_name..'")'))
                    assert(splash:runjs('$("input[name=LastName]").val("'..splash.args.last_name..'")'))
                    assert(splash:runjs('$("textarea[name=g-recaptcha-response]").val("'..splash.args.captcha_response..'")'))
                    assert(splash:wait(1))
                
                    local form = splash:select('.form-horizontal')
                    local values = assert(form:form_values())
                    assert(form:submit())
                    assert(splash:wait(5))
                    local search_input = splash:select('input[type=search]')
                    search_input:send_text(splash.args.dob)
                    assert(splash:wait(3))
                    return {
                        url = splash:url(),
                        html = splash:html(),
                        values = values
                    }
                end
            '''

            r = self.GLOBAL_SESSION.post(SPLASH_URL, auth=(SPLASH_USERNAME, SPLASH_PASSWORD),
                                         json={'url': self.SEARCH_URL,
                                               'lua_source': LUA_SCRIPT,
                                               'first_name': self.FIRST_NAME,
                                               'last_name': self.LAST_NAME,
                                               'dob': self.DOB,                                
                                               'captcha_response': captcha_response
                                               })
            print(r.text)
            if 'html' not in json.loads(r.text):
                return {'error': "Internal Server Error"}
            cases = self.parse_search_results(BeautifulSoup(json.loads(r.text)['html'], features="html.parser"))
            for case in cases:
                case['case_detail'] = self.get_case_detail(case['case_number'])

        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {'error': str(e)}
        return {'result': cases}


if __name__ == "__main__":
    # ScraperFLOrangeSuperior().parse_case_detail(BeautifulSoup(open('orange - Copy.html',
    #   'r+').read(), features="html.parser"))
    print(json.dumps(ScraperFLOrangeSuperior().scrape(search_parameters={
      'firstName': 'Adam', 'lastName': 'Smith', 'dob': '06/24/1991'})['result'], indent=4, sort_keys=True))

    print('Done running', __file__, '.')
