import json

from src.core.config import get_settings
from src.services.cases import get_cases, get_single_case

from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


settings = get_settings()


case_id = "220210358"

case  = get_single_case(case_id)
case_data = case.model_dump()

with open("case_data.json", "w") as f:
    json.dump(case_data, f, indent=4, cls=DateTimeEncoder)

print(case_data)