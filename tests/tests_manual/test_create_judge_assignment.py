import urllib.request
import urllib.error
import json

data = {
    "judge_id": 1,
    "project_id": "prj_01"
}

request = urllib.request.Request(
    "http://localhost:8080/api/judge/assignments",
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