""" Scraper for Maricopa Superior Court """
import os.path
import sys

import requests
from bs4 import BeautifulSoup

from src.scrapers.base import (
    InitializedSession,
    NameNormalizer,
    ScraperBase,
    TextNormalizer,
)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    + "/libraries"
)
# from json import dumps

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
)


class ScraperAZMaricopaSuperior(ScraperBase):
    """AZ Maricopa Superior Court scraper"""

    BASE_URL = "http://www.superiorcourt.maricopa.gov"
    SEARCH_BY_DOB_URL = (
        BASE_URL + "/docket/CriminalCourtCases/dobSearchResults.asp"
    )
    CASE_DETAIL_URL = BASE_URL + "/docket/CriminalCourtCases/caseInfo.asp"

    def scrape(self, search_parameters):
        """Entry point for lambda.

        Query should look like this:

        {
            "lastName": "Banks",
            "firstName": "Christina",
            "dob": "10/22/1978"
        }

        https://<endpoint>?queryStringParameters
        """
        print("Maricopa:", search_parameters)
        last_name = search_parameters["lastName"]
        first_name = search_parameters["firstName"]
        dob = search_parameters["dob"]
        return self.search_in_maricopa_az(first_name, last_name, dob)

    # This should be the only session used in this module.
    GLOBAL_SESSION = InitializedSession()

    def get_case_detail(self, case_number, test=False):
        """Scrape detail of case using a case_number.

        If test is set to parsed HTML, like what BeautifulSoup provides,
        the code will not attempt a lookup on the web site,
        but will instead use that HTML.

        This function either returns an object with a field called "case_detail"
        or a field called "error" with a error string
        e.g. { "cases": [...] } or { "error": "..." }
        """

        if test:
            url = ""
            soup = test
        else:
            url = "{}?caseNumber={}".format(self.CASE_DETAIL_URL, case_number)
            try:
                response = self.GLOBAL_SESSION.get(url)
            except requests.ConnectionError as exception:
                print("Connection failure : " + str(exception))
                return {"error": str(exception)}
            soup = BeautifulSoup(response.text, features="html.parser")

        # case information
        case_type = ""
        location = ""

        case_information = soup.find("table", {"id": "tblForms"})
        if case_information:
            cells = case_information.findAll("td")
            if len(cells) > 3:
                case_type = cells[1].text.strip()
                location = cells[3].text.strip()

        # parties
        parties = []

        party_information = soup.find("table", {"id": "tblDocket2"})
        if party_information:
            count = 0
            for row in party_information.findAll("tr"):
                cells = row.findAll("td")
                count = count + 1
                if count > 2 and len(cells) >= 5:
                    partyname = cells[0].text.strip()
                    relationship = cells[1].text.strip()
                    sex = cells[2].text.strip()
                    attorney = cells[3].text.strip()
                    judge = cells[4].text.strip()
                    parties.append(
                        {
                            "partyname": partyname,
                            "relationship": relationship,
                            "sex": sex,
                            "attorney": attorney,
                            "judge": judge,
                        }
                    )

        # dispositions
        # TODO: not all dispositions are for the party being searched.
        # We probably want to filter out those for other parties.
        # I am not sure if that code belongs in here, or in a post-filter.
        dispositions = []

        disposition_information = soup.find("table", {"id": "tblDocket12"})
        if disposition_information:
            count = 0
            for row in disposition_information.findAll("tr"):
                cells = row.findAll("td")
                count = count + 1
                if count > 2 and len(cells) > 6:
                    partyname = cells[0].text.strip()
                    arscode = cells[1].text.strip()
                    description = cells[2].text.strip()
                    crimedate = cells[3].text.strip()
                    dispositioncode = cells[4].text.strip()
                    disposition = cells[5].text.strip()
                    date = cells[6].text.strip()
                    dispositions.append(
                        {
                            "partyname": partyname,
                            "arscode": arscode,
                            "description": description,
                            "crimedate": crimedate,
                            "dispositioncode": dispositioncode,
                            "disposition": disposition,
                            "date": date,
                        }
                    )

        # case documents
        casedocuments = []

        document_information = soup.find("table", {"id": "tblDocket3"})
        if document_information:
            new_case = {}
            count = 0
            for row in document_information.findAll("tr"):
                cells = row.findAll("td")
                count = count + 1
                if count > 2 and len(cells) > 0:  # skip table headers
                    if len(cells) == 1:  # check if this row is for note or not
                        new_case["note"] = TextNormalizer(
                            cells[0].text
                        ).normalized()
                        casedocuments.append(new_case)
                        new_case = {}
                    else:
                        if new_case:
                            casedocuments.append(new_case)
                        filingdate = cells[0].text.strip()
                        description = TextNormalizer(
                            cells[1].text
                        ).normalized()
                        docketdate = cells[2].text.strip()
                        filingparty = cells[3].text.strip()
                        new_case = {
                            "filingdate": filingdate,
                            "description": description,
                            "docketdate": docketdate,
                            "filingparty": filingparty,
                        }
            if new_case:  # add last row if it's not for note
                casedocuments.append(new_case)

        # case calendar
        casecalendarevents = []

        case_calendar = soup.find("table", {"id": "tblDocket4"})
        if case_calendar:
            count = 0
            for row in case_calendar.findAll("tr"):
                cells = row.findAll("td")
                count = count + 1
                if count > 2 and len(cells) > 0:
                    date = cells[0].text.strip()
                    time = cells[1].text.strip()
                    event = cells[2].text.strip()
                    casecalendarevents.append(
                        {
                            "date": date,
                            "time": time,
                            "event": event,
                        }
                    )

        case_detail = {
            "url": url,
            "case_type": case_type,
            "location": location,
            "parties": parties,
            "dispositions": dispositions,
            "casedocuments": casedocuments,
            "casecalendarevents": casecalendarevents,
        }

        return {"case_detail": case_detail}

    def search_by_dob(self, last_name, first_name, dob, test=False):
        """Scrape list of cases by using the first name initial and last name initial and DOB.

        If test is set to parsed HTML, like what BeautifulSoup provides,
        the code will not attempt a lookup on the web site,
        but will instead use that HTML.

        This function either returns an object with
        a field called "cases" which is an array of cases, or
        an object with a field called "error" with a error string
        e.g. { "cases": [...] } or { "error": "..." }
        """

        if test:
            soup = test
        else:
            first_name = NameNormalizer(first_name).normalized()
            last_name = NameNormalizer(last_name).normalized()
            if len(first_name) < 1 or len(last_name) < 1:
                return {"error": "first and last initial must be provided"}

            form_data = {
                "lastName2": last_name[0].upper(),
                "FirstName2": first_name[0].upper(),
                "dob": dob,
            }
            try:
                response = self.GLOBAL_SESSION.post(
                    self.SEARCH_BY_DOB_URL, data=form_data
                )
            except requests.ConnectionError as exception:
                print("Connection failure : " + str(exception))
                return {"error": str(exception)}

            soup = BeautifulSoup(response.text, features="html.parser")

        results = []

        case_table = soup.find("table", class_="zebraRowTable")
        if case_table:
            rows = case_table.findAll("tr")
            is_first = True
            for row in rows:
                cells = row.findAll("td")
                # to skip table header
                if not is_first and cells and len(cells) >= 4:
                    case_number = cells[0].find("a").text.strip()
                    case_url = cells[0].find("a").attrs["href"]
                    party_name = cells[1].text.strip()
                    aka = cells[2].text.strip()
                    dob = cells[3].text.strip()

                    case = {
                        "case_number": case_number,
                        "case_url": self.BASE_URL + case_url,
                        "party_name": party_name,
                        "aka": aka,
                        "dob": dob,
                    }

                    if not test:
                        result = self.get_case_detail(case_number)

                        if "error" in result:
                            return {"error": result["error"]}

                        case["case_detail"] = result["case_detail"]

                    results.append(case)

                if is_first:
                    is_first = False

        return {"cases": results}

    def search_in_maricopa_az(self, first_name, last_name, dob, test=False):
        """Scrape the web site using the given search criteria.

        If test is set to parsed HTML, like what BeautifulSoup provides,
        the code will not attempt a lookup on the web site,
        but will instead use that HTML.

        This function either returns an object with
        a field called "result" which is an array of cases, or
        an object with a field called "error" with a error string
        e.g. { "result": [...] } or { "error": "..." }
        """

        first_name = NameNormalizer(first_name).normalized()
        last_name = NameNormalizer(last_name).normalized()
        if dob:
            dob = dob.strip()

        # get all cases with initials of input name and dob
        result = self.search_by_dob(last_name, first_name, dob, test)

        if "error" in result:
            return {"error": result["error"]}

        # Since the search is by initials and DOB, we need to make sure
        # that the resulting name is for the person we asked for.
        # For example, if we search for "John Smith, 1/1/1980" and
        # we do a search using "J S 1/1/1980" we do not
        # want to return a record for "Jimmy Smits, 1/1/1980".
        matched_cases = []
        for case in result["cases"]:
            # find the exact cases with same name as input name among cases from second search type
            if test or self.party_matches(
                last_name + "," + first_name, case["party_name"]
            ):
                matched_cases.append(case)

        return {"result": matched_cases}

    def party_matches(self, party_name1, party_name2):
        """Returns true if the given last name and first name match the given party name."""
        party1 = NameNormalizer(party_name1).normalized()
        party2 = NameNormalizer(party_name2).normalized()
        return party1.startswith(party2) or party2.startswith(party1)


if __name__ == "__main__":
    # print(dumps(search_by_dob('B', 'C', '10/22/1978'), indent=4, sort_keys=True))
    # print(dumps(get_case_detail('CR2015-030647'), indent=4, sort_keys=True))
    # print(dumps(search_in_maricopa_az('Christina', 'Banks', '10/22/1978'), indent=4, sort_keys=True))
    # print(dumps(search_in_maricopa_az('Baker', 'Stuart', ''), indent=4, sort_keys=True))
    # print(dumps(search_in_maricopa_az('Laurie', 'Wheeler', '10/07/1968'), indent=4, sort_keys=True))

    print("Done running", __file__, ".")
