import requests

response = requests.get("http://127.0.0.1:8000/search/keyword?query=regt")
print(response.status_code)
print(response.json())