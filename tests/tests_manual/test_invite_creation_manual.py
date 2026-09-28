import urllib.request
import urllib.error
import json

team_id = "54638549-28e7-46c7-af08-772ce0a215f3"

data = {
    "email": "participant@example.org"
}

request = urllib.request.Request(
    f"http://localhost:8080/api/teams/{team_id}/invites",
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