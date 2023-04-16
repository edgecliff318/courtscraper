import json


class ConfigLoader(object):
    def __init__(self, path: str):
        self.path = path
        self.data = None

    def load(self):
        with open(self.path, "r") as f:
            self.data = json.load(f)
        return self.data

    def get_court_details(self, court_code):
        if self.data is None:
            self.data = self.load()
        for court in self.data["courts"]:
            if court["value"] == court_code:
                return court
        return {}
