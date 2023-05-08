import json


class ConfigLoader:
    def __init__(self, path: str):
        self.path = path
        self.data = None

    def load(self):
        with open(self.path) as f:
            self.data = json.load(f)
        return self.data

    def get_court_details(self, court_code):
        if self.data is None:
            self.data = self.load()
        for court in self.data["courts"]:
            if court["value"] == court_code:
                return court
        return {}
