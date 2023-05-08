""" Scraper for Santa Clara Superior Court """
import json
import os.path
import sys

import requests

from src.scrapers.base import (
    InitializedSession,
    NameNormalizer,
    ScraperBase,
    get_recaptcha_answer,
)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    + "/libraries"
)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
)


class ScraperCASantaClaraSuperior(ScraperBase):
    """CA Santa Clara Superior Court scraper"""

    SITE_KEY_URL = "https://portal.scscourt.org/api/siteverify/key"
    SEARCH_URL = "https://portal.scscourt.org/search"
    TOKEN_URL = "https://portal.scscourt.org/api/case/token"
    CASE_URL = "https://portal.scscourt.org/api/case/"
    SEARCH_RESULT_URL = "https://portal.scscourt.org/api/cases/byparty"

    case_token = ""  # case_token for case detail api

    def scrape(self, search_parameters):
        """Entry point for lambda.

        Query should look like this:

        {
            "lastName": "Stuart",
            "firstName": "Baker",
            "dob": "10/27/1963"
        }
        https://<endpoint>?queryStringParameters
        """
        last_name = search_parameters["lastName"]
        first_name = search_parameters["firstName"]
        dob = search_parameters["dob"]
        return self.search_in_santa_clara_ca(first_name, last_name, dob)

    GLOBAL_SESSION = InitializedSession()

    def get_token(self):
        """Generate the token that will be used for case detail api

        This function returns an object.
        """
        # get site_key for google recaptcha

        try:
            site_key = (
                self.GLOBAL_SESSION.get(self.SITE_KEY_URL)
                .text.replace('"', "")
                .strip()
            )
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {"error": str(e)}
        print(site_key)

        # get captcha_id with captcha_key, site_key and page_url on the website that has CAPTCHAs
        recaptcha_answer = get_recaptcha_answer(site_key, self.SEARCH_URL)
        print(recaptcha_answer)

        # get case_token with recaptcha_answer

        self.GLOBAL_SESSION = InitializedSession(
            headers={"recaptcha": recaptcha_answer}
        )
        try:
            r = self.GLOBAL_SESSION.get(self.TOKEN_URL)
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {"error": str(e)}

        if "token" in json.loads(r.text):
            return {"token": json.loads(r.text)["token"]}
        else:
            return {"token": ""}

    def request_case(self, case_id):
        """Get the response from case detail API with case_id

        This function returns an object.
        """
        print("token:", self.case_token)
        url = "{}{}".format(self.CASE_URL, case_id)

        payload = {}
        headers = {
            "case-token": self.case_token,
            "cookie": "_ga=GA1.2.380791490.1588790476; _gid=GA1.2.1932016851.1588790476",
        }
        try:
            response = requests.request(
                "GET", url, headers=headers, data=payload
            )
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {"error": str(e)}

        print(response.text)

        return {"case": response.text}

    def get_case_detail(self, case_id):
        """Get case detail with case_id

        This function returns an object.
        """

        # for the first run, generate the token and set the value to GLOBAL case_token
        if self.case_token == "":
            self.case_token = self.get_token()
            if "error" in self.case_token:
                return {"error": self.case_token["error"]}
            else:
                self.case_token = self.case_token["token"]

        # get case detail
        case_detail = self.request_case(case_id)
        if "error" in case_detail:
            return {"error": case_detail["error"]}
        else:
            case_detail = case_detail["case"]

        # until case_token works
        while "Case Search Session Expired." in case_detail:
            case_detail = self.request_case(case_id)
            if "error" in case_detail:
                return {"error": case_detail["error"]}
            else:
                case_detail = case_detail["case"]
            # generate the new case_token
            self.case_token = self.get_token()
            if "error" in self.case_token:
                return {"error": self.case_token["error"]}
            else:
                self.case_token = self.case_token["token"]

            print("new_token:", self.case_token)

        if "data" in json.loads(case_detail):
            return {"case_detail": json.loads(case_detail)["data"]}
        else:
            return {"case_detail": {}}

    # get parsed search result with input data
    def get_search_result(self, first_name, last_name, dob, test=False):
        """Get matched cases using given firstName, lastName and dob

        If test is set to parsed HTML, like what BeautifulSoup provides,
        the code will not attempt a lookup on the web site,
        but will instead use that HTML.

        This function returns an array
        """

        try:
            r = self.GLOBAL_SESSION.post(
                self.SEARCH_RESULT_URL,
                {
                    "dateOfBirth": dob,
                    "firstName": first_name,
                    "lastName": last_name,
                },
            )
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")

        if test:
            if "data" in json.loads(test):
                return json.loads(test)["data"]
            else:
                return []
        else:
            if "data" in json.loads(r.text):
                return json.loads(r.text)["data"]
            else:
                return []

    def search_in_santa_clara_ca(self, first_name, last_name, dob):
        """Scrape the web site using the given search criteria.

        This function either returns an object with
        a field called "result" which is an array of cases, or
        an object with a field called "error" with a error string
        e.g. { "result": [...] } or { "error": "..." }
        """

        first_name = NameNormalizer(first_name).normalized()
        last_name = NameNormalizer(last_name).normalized()
        if dob:
            dob = dob.strip()

        matched_cases = self.get_search_result(first_name, last_name, dob)
        cases = []
        for case in matched_cases:
            detailed_case = case
            print(case["caseId"])
            # add case_detail information to mathced_case object
            result = self.get_case_detail(case["caseId"])
            if "error" in result:
                return {"error": result["error"]}
            else:
                detailed_case["case_detail"] = result["case_detail"]
            cases.append(detailed_case)
        return {"result": cases}


if __name__ == "__main__":
    # print(search_in_santa_clara_ca('Stuart','Baker', '10/27/1963'))
    # print(get_token())
    print(
        json.dumps(
            ScraperCASantaClaraSuperior().scrape(
                search_parameters={
                    "firstName": "Stuart",
                    "lastName": "Baker",
                    "dob": "10/27/1963",
                }
            )["result"],
            indent=4,
            sort_keys=True,
        )
    )
    print("Done running", __file__, ".")
