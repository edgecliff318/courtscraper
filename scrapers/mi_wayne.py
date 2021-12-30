""" Scraper for Wayne Superior Court """
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



class ScraperMIWayneSuperior(ScraperBase):
    """ MI Wayne Superior Court scraper """

    HEADERS = {
        'Content-Type': 'application/json'
    }
    LOGIN_URL = 'https://dapps.36thdistrictcourt.org/ROAWEBINQ/login.aspx?ReturnUrl=%2fROAWEBINQ%2fDefault.aspx'
    SEARCH_URL = 'https://dapps.36thdistrictcourt.org/ROAWEBINQ/Default.aspx'
    SEARCH_RESULT_URL = 'https://dapps.36thdistrictcourt.org/ROAWEBINQ/ROASched.aspx'
    CASE_DETAIL_URL = 'https://dapps.36thdistrictcourt.org/ROAWEBINQ/ROACase.aspx'
    SITE_KEY = '6LcNZWsUAAAAAHtZgMbFMLZeT-Mx0LiY-OszpUDq'
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
        return self.search_in_wayne_mi(first_name, last_name, dob)

    GLOBAL_SESSION = InitializedSession(headers=HEADERS)

    def get_case_detail(self, case_number, page_number, last_name, first_name):
        """ Get every information of case detail with given case number and page number

        This function returns an object.
        """
        recaptcha_answer = get_recaptcha_answer(
            self.SITE_KEY, self.CASE_DETAIL_URL)
        print(recaptcha_answer)
        LUA_SCRIPT = '''
            function main(splash)
                assert(splash:autoload("https://code.jquery.com/jquery-2.1.3.min.js"))
                treat = require("treat")
                local url = splash.args.url
                local case_number = splash.args.case_number
                local page = splash.args.page
                local captcha_response = splash.args.captcha_response

                assert(splash:go(url))
                assert(splash:wait(5))
                local form = splash:select('#frmDefault')
                local values = assert(form:form_values())
                values.txtDKTNAME = splash.args.name
                assert(form:fill(values))
                local element = splash:select('#btnGO')
                local bounds = element:bounds()
                assert(element:mouse_click{x=bounds.width/3, y=bounds.height/3})
                assert(splash:wait(1))
                local page_links = splash:select_all('tr.mypager:nth-child(1) td')
                local cases = {}
                local case_count = 0

                if page > 1 then
                    local element = splash:select('tr.mypager:nth-child(1) td:nth-child('..page..') a')
                    if element then
                        local bounds = element:bounds()
                        assert(element:mouse_click{x=bounds.width/3, y=bounds.height/3})
                        assert(splash:wait(1))
                    end
                end
                local rows = splash:select_all('table#gvDocket > tbody > tr')
                for j, row in ipairs(rows) do
                    local case_number_element = splash:select('table#gvDocket > tbody > tr:nth-child('..j..')  > td:nth-child(2) span')
                    if case_number_element then
                        if case_number_element:text() == case_number then
                            local view_button = splash:select('table#gvDocket > tbody > tr:nth-child('..j..')  > td:nth-child(1) input')
                            local bounds = view_button:bounds()
                            assert(view_button:mouse_click{x=bounds.width/3, y=bounds.height/3})
                            assert(splash:wait(1))
                        end
                    end
                end
                local sitekey = splash:select('div.g-recaptcha'):getAttribute('data-sitekey')
                assert(splash:wait(1))
                local form1 = splash:select('#Form1')
                local values1 = form1:form_values()
                values1['g-recaptcha-response'] = captcha_response
                assert(form1:fill(values1))
                assert(form1:submit())
                assert(splash:wait(1))
                return {
                    url = splash:url(),
                    html = splash:html(),
                    sitekey=sitekey,
                    values=values1
                }
            end
            '''
        try:
            r = self.GLOBAL_SESSION.post(SPLASH_URL, auth=(SPLASH_USERNAME, SPLASH_PASSWORD),
                                         json={'url': self.SEARCH_URL,
                                               'lua_source': LUA_SCRIPT,
                                               'case_number': case_number,
                                               'page': page_number + 1,
                                               'captcha_response': recaptcha_answer,
                                               'name': last_name + '/' + first_name
                                               })
            if 'html' in json.loads(r.text):
                return self.parse_case_detail(BeautifulSoup(json.loads(r.text)['html'], features="html.parser"))
            else:
                return {}
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {'error': str(e)}

    def parse_case_detail(self, soup):
        table = soup.find('table', {'id': 'dlROA'})
        if not table:
            return {}
        case_detail = {'Offenses': []}
        keys = [['PIN:'], ['STATUS:'], ['JUDGE\xa0OF\xa0RECORD:'], ['JUDGE:'], ['TCN:'], ['CTN:'], ['SID:'], ['ENTRY\xa0DATE:'], ['OFFENSE\xa0DATE:'], ['ARREST\xa0DATE:'], [
            'DOB:', 'SEX:', 'RACE:', 'CDL:'], ['VEHICLE\xa0TYPE:', 'VPN:'], ['VEH\xa0YR:', 'VEH\xa0MAKE:', 'PAPER\xa0PLATE:'], ['OFFICER:', 'DEPT:'], ['PROSECUTOR:']]
        offenseKeys = [['CNT:', 'C/M/F:'], ['ARRAIGNMENT\xa0DATE:', 'PLEA:',
                                            'PLEA\xa0DATE:'], ['FINDINGS:', 'DISPOSITION\xa0DATE:'], ['SENTENCING\xa0DATE:']]
        status = ''
        count = 0
        for row in table.findAll('tr'):
            row_content = row.text
            for key in keys:
                if key[0] in row_content:
                    if len(key) == 1:
                        case_detail[key[0].replace(':', '').replace('\xa0', ' ')] = row_content.split(
                            key[0])[1].replace('|', '').replace('\xa0\xa0', ' ').replace('\xa0', ' ').strip()
                    else:
                        for i in range(0, len(key)):
                            if i == len(key) - 1:
                                case_detail[key[i].replace(':', '').replace('\xa0', ' ')] = row_content.split(
                                    key[i])[1].replace('|', '').replace('\xa0\xa0', ' ').replace('\xa0', ' ').strip()
                            else:
                                case_detail[key[i].replace(':', '').replace('\xa0', ' ')] = row_content.split(key[i])[1].split(
                                    key[i + 1])[0].replace('\xa0\xa0', ' ').replace('\xa0', '').replace('|', '').strip()
                    break
            for key in offenseKeys:
                if key[0] in row_content:
                    if key[0] == 'CNT:':
                        case_detail['Offenses'].append({})
                        status = 'Offense'
                        count = 0
                    if len(key) == 1:
                        case_detail['Offenses'][len(case_detail['Offenses']) - 1][key[0].replace(':', '').replace(
                            '\xa0', ' ')] = row_content.split(key[0])[1].replace('|', '').replace('\xa0\xa0', ' ').replace('\xa0', '').strip()
                    else:
                        for i in range(0, len(key)):
                            if i == len(key) - 1:
                                if key[i] == 'C/M/F:':
                                    array = re.split(
                                        '\s+', row_content.split(key[i])[1].replace('|', '').replace('\xa0', ' ').strip())
                                    case_detail['Offenses'][len(
                                        case_detail['Offenses']) - 1]['Offense Level'] = array[0]
                                    case_detail['Offenses'][len(
                                        case_detail['Offenses']) - 1]['Statue ID'] = array[1]
                                    case_detail['Offenses'][len(
                                        case_detail['Offenses']) - 1]['Statue'] = array[2]

                                    case_detail['Offenses'][len(case_detail['Offenses']) - 1][key[i].replace(':', '').replace(
                                        '\xa0', ' ')] = row_content.split(key[i])[1].replace('|', '').replace('\xa0\xa0', ' ').replace('\xa0', ' ').strip()
                                else:
                                    case_detail['Offenses'][len(case_detail['Offenses']) - 1][key[i].replace(':', '').replace(
                                        '\xa0', ' ')] = row_content.split(key[i])[1].replace('|', '').replace('\xa0', ' ').strip()

                            else:
                                case_detail['Offenses'][len(case_detail['Offenses']) - 1][key[i].replace(':', '').replace('\xa0', ' ')] = row_content.split(
                                    key[i])[1].split(key[i + 1])[0].replace('\xa0\xa0', ' ').replace('\xa0', ' ').replace('|', '').strip()
            if status == 'Offense' and count == 1:
                case_detail['Offenses'][len(case_detail['Offenses']) - 1]['Offense'] = row_content.replace(
                    '\xa0\xa0', ' ').replace('\xa0', ' ').replace('|', '').strip()
            if 'DEFENSE\xa0ATTORNEY\xa0ADDRESS' in row_content:
                status = 'DEFENSE ATTORNEY ADDRESS'
                print(status)
                count = 0
            if status == 'DEFENSE ATTORNEY ADDRESS':
                if count == 1:
                    start = row_content.find('\xa0\xa0')
                    case_detail['DEFENSE ATTORNEY ADDRESS'] = row_content[0:start].strip(
                    )
                    case_detail['BAR NO.'] = row_content[start:len(
                        row_content) - 1].replace('\xa0\xa0', ' ').replace('\xa0', '').strip()
                    print(case_detail['BAR NO.'])
                elif count == 2:
                    start = row_content.find('\xa0\xa0')
                    case_detail['DEFENSE ATTORNEY ADDRESS'] = case_detail['DEFENSE ATTORNEY ADDRESS'] + \
                        ' ' + \
                        row_content[0:start].replace(
                            '\xa0\xa0', ' ').replace('\xa0', '').strip()
                elif count == 3:
                    start = row_content.find('\xa0\xa0')
                    case_detail['DEFENSE ATTORNEY ADDRESS'] = case_detail['DEFENSE ATTORNEY ADDRESS'] + \
                        ' ' + \
                        row_content[0:start].replace(
                            '\xa0\xa0', ' ').replace('\xa0', '').strip()
                elif count == 4:
                    start = row_content.find(
                        '\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0')
                    case_detail['DEFENSE ATTORNEY ADDRESS'] = case_detail['DEFENSE ATTORNEY ADDRESS'] + \
                        ' ' + \
                        row_content[0:start].replace(
                            '\xa0\xa0', ' ').replace('\xa0', '').strip()
                    case_detail['Telephone No.'] = row_content[start:len(
                        row_content) - 1].replace('\xa0\xa0', ' ').replace('\xa0', '').strip()
            count = count + 1

        print(json.dumps(case_detail, indent=4, sort_keys=True))
        # print(case_detail)
        return case_detail

    def parse_search_results_page(self, soup, dob):
        """ Parse rendered HTML page for search result of specific page and get matched cases using given dob
        This function returns an array.
        """
        cases = []
        case_table = soup.find('table', {'id': 'gvDocket'})
        if not case_table:
            return cases
        count = 0
        for row in case_table.findAll('tr'):
            count = count + 1
            if count < 3:
                continue
            cells = row.findAll('td')
            if row.find('input'):
                birth_date = cells[5].text.strip()
                if birth_date == dob:
                    case_number = cells[1].text.strip()
                    case_type = cells[2].text.strip()
                    case_pty = cells[3].text.strip()
                    name = cells[4].text.strip()
                    balance_date = cells[6].text.strip()
                    cases.append({
                        'case_number': case_number,
                        'case_type': case_type,
                        'case_pty': case_pty,
                        'name': name,
                        'balance_date': balance_date,
                        'birth_date': birth_date,
                    })
        return cases

    def convertDobToStr(self, dob):
        """ Convert given dob to expected dob string
        expected dob for api is M/DD/YYYY

        This function returns string.
        """
        dobString = datetime.strptime(dob, '%m/%d/%Y')
        return str(int(datetime.strftime(dobString, '%m'))) + datetime.strftime(dobString, '/%d/%Y')

    def search_in_wayne_mi(self, first_name, last_name, dob):
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
        dob = self.convertDobToStr(dob)

        LUA_SCRIPT = '''
            function main(splash)
                treat = require("treat")

                local url = splash.args.url
                assert(splash:go(url))
                assert(splash:wait(5))
                local form = splash:select('#frmDefault')
                local values = assert(form:form_values())
                values.txtDKTNAME = splash.args.name
                assert(form:fill(values))
                local element = splash:select('#btnGO')
                local bounds = element:bounds()
                assert(element:mouse_click{x=bounds.width/3, y=bounds.height/3})
                assert(splash:wait(1))
                local page_links = splash:select_all('tr.mypager:nth-child(1) td')
                local html_array = {}
                local cases = {}
                local case_count = 0
                html_array[1] = splash:html()
                for i, elem in ipairs(page_links) do
                    if i > 0 then
                        local element = splash:select('tr.mypager:nth-child(1) td:nth-child('..(i + 1)..') a')
                        if element then
                            local bounds = element:bounds()
                            assert(element:mouse_click{x=bounds.width/3, y=bounds.height/3})
                            assert(splash:wait(1))
                            html_array[i + 1] = splash:html()
                        end
                    end
                end
                return {
                    url = splash:url(),
                    html = splash:html(),
                    html_array = treat.as_array(html_array),
                    cases = cases
                }
            end
        '''
        retry = 0
        cases = []
        while retry < self.RETRY_LIMIT and len(cases) == 0:
            retry = retry + 1
            try:
                r = self.GLOBAL_SESSION.post(SPLASH_URL, auth=(SPLASH_USERNAME, SPLASH_PASSWORD),
                                            json={'url': self.SEARCH_URL,
                                                'lua_source': LUA_SCRIPT,
                                                'name': last_name + '/' + first_name
                                                })
            except requests.ConnectionError as e:
                print("Connection failure : " + str(e))
                print("Verification with InsightFinder credentials Failed")
                return {'error': str(e)}
            if 'html_array' not in json.loads(r.text):
                print(r.text)
                return {'error': "Internal Server Error"}
            print(len(json.loads(r.text)['html_array']))
            html_pages = json.loads(r.text)['html_array']
            # print(html_pages)
            for i in range(0, len(html_pages)):
                soup = BeautifulSoup(html_pages[i], features="html.parser")
                page_cases = self.parse_search_results_page(soup, dob)
                for case in page_cases:
                    case['case_detail'] = self.get_case_detail(
                        case['case_number'], i, last_name, first_name)
                cases = cases + page_cases
        return {'result': cases}


if __name__ == "__main__":
    print(json.dumps(ScraperMIWayneSuperior().scrape(search_parameters={
          'firstName': 'Adam', 'lastName': 'Smith', 'dob': '09/20/1984'})['result'], indent=4, sort_keys=True))
    print('Done running', __file__, '.')
