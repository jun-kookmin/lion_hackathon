import os
from api.services.llm_openai import explain

import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.devel")
django.setup()

features = {
    "business_type": "카페",
    "distance_km": 0.42,
    "daily_footfall_avg": 4790,
    "monthly_rent": 1565000,
    "deposit": 26600000,
    "floor": 1,
    "address": "서울 강남구 ..."
}

print("=== explain() 결과 ===")
print(explain(features))
