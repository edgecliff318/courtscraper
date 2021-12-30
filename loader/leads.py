import datetime
import os

import requests


class CaseNet:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password

    def login(self):
        self.session = requests.Session()
        url = os.path.join(self.url, "login")
        payload = f'username={self.username}&password=' \
                  f'{self.password}&logon=logon'
        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google '
                         'Chrome";v="96"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Upgrade-Insecure-Requests': '1',
            'Origin': 'https://www.courts.mo.gov',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,'
                      'application/xml;q=0.9,image/avif,image/webp,'
                      'image/apng,*/*;q=0.8,'
                      'application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Referer': 'https://www.courts.mo.gov/cnet/logon.do',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }

        self.session = self.session.request(
            "POST", url, headers=headers, data=payload
        )

    def get_leads(self, court_code, county_code, date, case_type="Infraction"):
        self.login()
        url = os.path.join(self.url, "searchResult.do")
        payload = "{\"draw\":1,\"columns\":[{\"data\":0,\"name\":\"\"," \
                  "\"searchable\":true,\"orderable\":true,\"search\":{" \
                  "\"value\":\"\",\"regex\":false}}," \
                  "{\"data\":\"initFiling\",\"name\":\"\"," \
                  "\"searchable\":true,\"orderable\":true,\"search\":{" \
                  "\"value\":\"\",\"regex\":false}}," \
                  "{\"data\":\"caseNumber\",\"name\":\"\"," \
                  "\"searchable\":true,\"orderable\":true,\"search\":{" \
                  "\"value\":\"\",\"regex\":false}},{\"data\":\"caseStyle\"," \
                  "\"name\":\"\",\"searchable\":true,\"orderable\":true," \
                  "\"search\":{\"value\":\"\",\"regex\":false}}," \
                  "{\"data\":\"caseType\",\"name\":\"\",\"searchable\":true," \
                  "\"orderable\":true,\"search\":{\"value\":\"\"," \
                  "\"regex\":false}},{\"data\":\"countyDesc\",\"name\":\"\"," \
                  "\"searchable\":true,\"orderable\":true,\"search\":{" \
                  "\"value\":\"\",\"regex\":false}}],\"order\":[{" \
                  "\"column\":0,\"dir\":\"asc\"}],\"start\":10," \
                  "\"length\":2000,\"search\":{\"value\":\"\"," \
                  "\"regex\":false}}"
        date = datetime.datetime.fromisoformat(date).strftime(
            "%m %d %Y").replace(" ", "%2F")
        url = f"https://www.courts.mo.gov/cnet/searchResult.do?" \
              f"countyCode={county_code}" \
              f"&courtCode={court_code}" \
              f"&startDate={date}" \
              f"&caseStatus=A" \
              f"&caseType={case_type}" \
              f"&locationCode="

        self.session.headers.update(
            {
                'Connection': 'keep-alive',
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", '
                             '"Google Chrome";v="96"',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/json;charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'sec-ch-ua-mobile': '?0',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X '
                              '10_15_7) AppleWebKit/537.36 (KHTML, '
                              'like Gecko) Chrome/96.0.4664.110 Safari/537.36',
                'sec-ch-ua-platform': '"macOS"',
                'Origin': 'https://www.courts.mo.gov',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8'
            }
        )
        response = self.session.request(
            "POST", url,
            data=payload,
        )



        return response.json()
