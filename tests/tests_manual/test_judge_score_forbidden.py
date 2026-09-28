import urllib.request
import urllib.error
import json

data = {
    "project_id": "prj_02",
    "functionality": 5,
    "quality": 5,
    "comment": "This should not be accepted."
}

request = urllib.request.Request(
    "http://localhost:8080/api/judge/scores",
    data=json.dumps(data).encode(),
    headers={
        "Content-Type": "application/json",
        "Cookie": "session=jdg_a_91bc"
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