import requests
import json


def authenticate_user()->str:
    
    username = "yassine@tickettakedown.com"
    password = "humjEPhmkRh642Pe"
    url = "https://api.openpeoplesearch.com/api/v1/User/authenticate"

    headers = {
        "accept": "*/*",
        "Content-Type": "application/json"
    }

    data = {
        "username": username,
        "password": password
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    token = response.json()["token"]

    return token





def search_person(firstName, lastName, token, middleName="", city=None, state=None):
    url = "https://api.openpeoplesearch.com/api/v1/consumer/NameSearch"

    headers = {
        "accept": "text/plain",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "firstName": firstName,
        "middleName": middleName,
        "lastName": lastName,
        "city": city,
        "state": state
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    return response.text


token = authenticate_user()
print(search_person("Samama", "Mahmud", token))
