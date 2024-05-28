import requests

# Remplacez 'YOUR_API_TOKEN' par votre jeton API
API_TOKEN = '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'
API_URL = "https://api-inference.huggingface.co/models/bigscience/bloom"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

data = query({"inputs": "tell me a storie"})
print(data)
