import asyncio
import json
import os
from email import header

import aiohttp
from rich.console import Console
from rich.progress import track

console = Console()


async def fetch_with_retry(
    url, session, retry_intervals, request_type="get", **kwargs
):
    #  curl -x dc.pr.oxylabs.io:10000 -U "customer-samatix:mi2YWzNb8dMrnBS" https://ip.oxylabs.io
    proxy = "http://dc.pr.oxylabs.io:10000"
    proxy_auth = aiohttp.BasicAuth("customer-samatix", "mi2YWzNb8dMrnBS")
    # curl 'https://ip.oxylabs.io' -U 'customer-samatixr-cc-US:JLN5CF8YwPUpeGw' -x 'pr.oxylabs.io:7777'
    # proxy = "http://pr.oxylabs.io:7777"
    # proxy_auth = aiohttp.BasicAuth("customer-samatixr", "JLN5CF8YwPUpeGw")
    for i, delay in enumerate(retry_intervals):
        try:
            async with session.request(
                request_type, url, **kwargs, proxy=proxy, proxy_auth=proxy_auth
            ) as response:
                # Check for a successful response and return the result
                if response.status == 204:
                    return {}
                elif response.status == 201:
                    return await response.json()
                elif response.status == 200:
                    return await response.json()
                elif response.status == 202:
                    return await response.json()
                elif response.status == 400:
                    content = await response.json()
                    return content
                else:
                    content = await response.json()
                    raise Exception(f"Error {response.status}")
                # Handle other HTTP statuses as needed
        except Exception as e:
            # Log or handle the exception as needed
            console.log(f"Retrying {i + 1}")
            # Wait for the specified delay before the next retry
            if (
                i < len(retry_intervals) - 1
            ):  # Avoid sleeping after the last attempt
                await asyncio.sleep(delay)

    # Optionally, raise an exception or return a default value after all retries fail
    raise Exception("All retries failed")


class OffTheRecord:
    def __init__(
        self,
        headers,
        states=None,
        cdl="NO_CDL",
        accident=False,
    ):
        self.headers = headers
        self.base_url = "https://offtherecord.com"

        if states is None:
            self.states = [
                "AL",
                "AK",
                "AZ",
                "AR",
                "CA",
                "CO",
                "CT",
                "DE",
                "FL",
                "GA",
                "HI",
                "ID",
                "IL",
                "IN",
                "IA",
                "KS",
                "KY",
                "LA",
                "ME",
                "MD",
                "MA",
                "MI",
                "MN",
                "MS",
                "MO",
                "MT",
                "NE",
                "NV",
                "NH",
                "NJ",
                "NM",
                "NY",
                "NC",
                "ND",
                "OH",
                "OK",
                "OR",
                "PA",
                "RI",
                "SC",
                "SD",
                "TN",
                "TX",
                "UT",
                "VT",
                "VA",
                "WA",
                "WV",
                "WI",
                "WY",
            ]
        else:
            self.states = states
        if not isinstance(self.states, list):
            self.states = [self.states]

        self.cdl = cdl
        self.accident = accident
        self.retry_strategy = [1, 2, 5, 10, 30, 60, 120, 300, 600]

    def load_temp_file(self, temp_file):
        if os.path.exists(temp_file):
            with open(temp_file) as f:
                results_temp = json.load(f)

            results = [
                r
                for r in results_temp
                if r.get("quote_request", {})
                .get("error", {})
                .get("uiErrorMsg")
                is None
                or r.get("quote_request", {}).get("error", {}).get("errorCode")
                == 501
            ]
            return results
        else:
            return []

    async def create_citation(self, session: aiohttp.ClientSession, state):
        console.log(f"Creating citation for {state}")
        url = "https://otr-backend-service-us-prod.offtherecord.com/api/v1/citations"
        payload = {
            "rawImageData": None,
            "clientType": "OTR_WEBSITE",
            "imageContentType": "bypassed",
            "citationState": state,
        }
        headers = self.headers.copy()
        headers["content-type"] = "application/json;charset=UTF-8"

        payload = json.dumps(payload)
        citation = await fetch_with_retry(
            url,
            session,
            self.retry_strategy,
            request_type="post",
            headers=headers,
            data=payload,
        )
        citation_code = citation.get("citation", {}).get("citationId")
        console.log(f"Created citation {citation_code} for {state}")
        return citation_code

    async def update_citation(
        self,
        session: aiohttp.ClientSession,
        citation_code,
        court_id,
        violations,
        accident=False,
        issue_date=None,
        cdl_status="NO_CDL",
    ):
        url = f"https://otr-backend-service-us-prod.offtherecord.com/api/v1/citations/{citation_code}"
        payload_dict = {
            "citation": {
                "violationCount": len(violations),
                "court": {"courtId": court_id},
                "clientType": "OTR_WIDGET",
                "violations": [{"violationId": v} for v in violations],
                "involvesAccident": accident,
                "cdlStatus": cdl_status,
            }
        }

        headers = self.headers.copy()
        # set 'content-type': 'application/json;charset=UTF-8',
        headers["content-type"] = "application/json;charset=UTF-8"
        payload = json.dumps(payload_dict)
        # response = requests.request("PUT", url, headers=headers, data=payload)
        # async with session.put(url, headers=headers, data=payload) as response:
        await fetch_with_retry(
            url,
            session,
            self.retry_strategy,
            request_type="put",
            headers=headers,
            data=payload,
        )
        console.log(f"Updated citation {citation_code} successfully")

    async def get_quote(self, session: aiohttp.ClientSession, citation_code):
        url = f"https://otr-backend-service-us-prod.offtherecord.com/api/v1/citations/{citation_code}/case"
        payload = '{"setQuoteExpirationOn":true,"courtDate":null}'
        headers = self.headers.copy()
        headers["content-type"] = "application/json;charset=UTF-8"
        case_details = await fetch_with_retry(
            url,
            session,
            self.retry_strategy,
            request_type="post",
            headers=headers,
            data=payload,
        )
        return case_details

    async def get_quote_cost(self, session: aiohttp.ClientSession, case_code):
        url = f"https://otr-backend-service-us-prod.offtherecord.com/api/v1/cases/{case_code}/customer/cost?version=wjd6plzfdnf"
        payload = {}
        quote_cost = await fetch_with_retry(
            url,
            session,
            self.retry_strategy,
            data=payload,
            headers=self.headers,
        )
        return quote_cost

    async def get_quote_eligibility(
        self, session: aiohttp.ClientSession, case_code
    ):
        url = f"https://otr-backend-service-us-prod.offtherecord.com/api/v1/cases/{case_code}/refund/eligibility?version=2bkl60ywyh8"
        payload = {}
        quote_eligibility = await fetch_with_retry(
            url,
            session,
            self.retry_strategy,
            data=payload,
            headers=self.headers,
        )
        return quote_eligibility

    async def get_violations(self, session: aiohttp.ClientSession, state):
        console.log(f"Getting violations for {state}")
        url = f"https://otr-backend-service-us-prod.offtherecord.com/api/v1/violations?audience=client&state={state}"
        # async with session.get(url, headers=self.headers) as response:
        raw_violations = await fetch_with_retry(
            url, session, self.retry_strategy, headers=self.headers
        )
        violation_types = raw_violations["violationTypes"]
        console.log(f"Got {len(violation_types)} violations for {state}")
        return violation_types

    async def get_courts(self, session: aiohttp.ClientSession, state):
        console.log(f"Getting courts for {state}")
        url = f"https://otr-backend-service-us-prod.offtherecord.com/api/v2/courts/traffic?state={state}"
        payload = {}
        courts_list = await fetch_with_retry(
            url,
            session,
            self.retry_strategy,
            data=payload,
            headers=self.headers,
        )
        courts_list = courts_list.get("courts", [])

        console.log(f"Got {len(courts_list)} courts for {state}")
        return courts_list

    async def run_single(
        self, session, citation_code, state, court_id, violation_id
    ):
        # Citation Update
        await self.update_citation(
            session,
            citation_code,
            court_id,
            [
                violation_id,
            ],
            accident=self.accident,
            issue_date=None,
            cdl_status=self.cdl,
        )
        # Quote Request
        quote_request = await self.get_quote(session, citation_code)
        law_firm = (
            quote_request.get("theCase", {})
            .get("lawfirmCaseDecision", {})
            .get("lawfirmName")
        )
        error_code = quote_request.get("error", {}).get("errorCode")

        if error_code == 102:
            # Recreate citation
            citation_code = await self.create_citation(session, state)

            # Citation Update
            await self.update_citation(
                session,
                citation_code,
                court_id,
                [
                    violation_id,
                ],
                accident=self.accident,
                issue_date=None,
                cdl_status=self.cdl,
            )

            # Quote Request
            quote_request = await self.get_quote(session, citation_code)

        error_msg = quote_request.get("error", {}).get("uiErrorMsg")

        quote_eligibility = None
        quote_cost = None
        message = None

        if error_msg is not None:
            message = error_msg

        # Quote Cost
        case_code = quote_request.get("theCase", {}).get("caseId")

        if error_msg is None:
            message = law_firm
            quote_cost = await self.get_quote_cost(session, case_code)

            # Quote eligibility
            quote_eligibility = await self.get_quote_eligibility(
                session, case_code
            )
            fees = quote_cost.get("lineItems", [])
            for fee in fees:
                message += f" {fee.get('feeDescription')} {fee.get('feeAmount')/100} $"

        console.log(
            f"Got quote for {state} : {court_id} : {violation_id} => {message}"
        )

        return {
            "state": state,
            "court_id": court_id,
            "violation_id": violation_id,
            "quote_request": quote_request,
            "quote_cost": quote_cost,
            "quote_eligibility": quote_eligibility,
        }

    async def run(self):
        async with aiohttp.ClientSession() as session:
            results = []
            for state in self.states:
                output_file = f"otr/{state}_{self.cdl}_{self.accident}.json"
                output_file_temp = (
                    f"{state}_{self.cdl}_{self.accident}_temp.json"
                )
                results = self.load_temp_file(output_file)
                results_temp = self.load_temp_file(output_file_temp)
                results_temp_filtered = [
                    r
                    for r in results_temp
                    if f'{r.get("state")}_{r.get("court_id")}_{r.get("violation_id")}'
                    not in [
                        f'{e.get("state")}_{e.get("court_id")}_{e.get("violation_id")}'
                        for e in results
                    ]
                ]
                results += results_temp_filtered

                excluded_parse = [
                    f'{r.get("state")}_{r.get("court_id")}_{r.get("violation_id")}'
                    for r in results
                ]

                console.log(f"Excluded {len(excluded_parse)}")

                violation_types = await self.get_violations(session, state)
                courts_list = await self.get_courts(session, state)

                console.log(
                    f"Got {len(violation_types) * len(courts_list)} to parse"
                )

                # Get the run plan
                parameters = [
                    (
                        state,
                        court["courtId"],
                        violation["trafficViolationTypeId"],
                    )
                    for court in courts_list
                    for violation in violation_types
                    if (
                        (
                            f"{state}_{court['courtId']}"
                            f"_{violation['trafficViolationTypeId']}"
                        )
                        not in excluded_parse
                    )
                    and (violation.get("enabledForCustomers", False))
                ]

                console.log(
                    f"After excluding {len(excluded_parse)} : {len(parameters)}"
                )

                parallelism = 40

                # Generate citation codes for the 40 concurrent requests
                citation_codes = [
                    await self.create_citation(session, state)
                    for i in range(parallelism)
                ]

                # Split the parameters into 40 chunks for the 40 concurrent requests
                chunks = [
                    parameters[i : i + parallelism]
                    for i in range(0, len(parameters), parallelism)
                ]
                counter = 0
                # Run the requests
                for chunk in track(chunks, description=f"Running {state}"):
                    counter += 1
                    tasks = [
                        self.run_single(
                            session,
                            citation_codes[i],
                            state,
                            court_id,
                            violation_id,
                        )
                        for i, (state, court_id, violation_id) in enumerate(
                            chunk
                        )
                    ]
                    results += await asyncio.gather(*tasks)

                    if counter % 100 == 0:
                        # Save every 100 requests
                        output_file = (
                            f"{state}_{self.cdl}_{self.accident}_temp.json"
                        )
                        await self.save(results, output_file)

                output_file = f"{state}_{self.cdl}_{self.accident}_temp.json"
                await self.save(results, output_file)
        return results

    async def save(self, results, output_file):
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        console.log(f"Saved results to {output_file}")


# samatix : mi2YWzNb8dMrnBS
# python main.py retrieve-quotes --headers-file=headers/1374833.json --states=PA,FL,MO,OH,NJ,LA,GA,NY,TX
