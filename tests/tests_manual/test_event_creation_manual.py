import urllib.request
import urllib.error
import json

data = {
    "name": "Open Test Event",
    "submissions_open": "2026-09-01T00:00:00Z",
    "submissions_close": "2026-10-05T18:00:00Z",
    "tracks": [
        {"name": "Developer tools"}
    ],
    "prizes": [
        {
            "name": "Best Overall",
            "description": "Best project"
        }
    ]
}

request = urllib.request.Request(
    "http://localhost:8080/api/events",
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