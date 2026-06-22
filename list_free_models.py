import requests
import os

API_KEY = os.getenv("OPENROUTER_API_KEY")

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

response = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers=headers
)

response.raise_for_status()

models = response.json()["data"]

free_models = sorted(
    model["id"]
    for model in models
    if model["id"].endswith(":free")
)

print(f"\nFound {len(free_models)} free models:\n")

for model in free_models:
    print(model)