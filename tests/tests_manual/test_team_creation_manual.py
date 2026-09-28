import urllib.request
import urllib.error
import json

event_id = "5feb1fba-aec9-4473-bdf4-0a347b450878"

data = {
    "name": "Open Test Team"
}

request = urllib.request.Request(
    f"http://localhost:8080/api/events/{event_id}/teams",
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