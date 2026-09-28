import urllib.request
import urllib.error
import json

data = {
    "name": "Quality",
    "weight": 40
}

request = urllib.request.Request(
    "http://localhost:8080/api/events/evt_01/rubric",
    data=json.dumps(data).encode(),
    headers={
        "Content-Type": "application/json",
        "Cookie": "session=org_7f2a"
    },
    method="POST"
)

try:
    response = urllib.request.urlopen(request)
    print(response.status)
    print(response.read().decode())

except urllib.error.HTTPError as error:
    print(error.code)
    print(error.read().decode())