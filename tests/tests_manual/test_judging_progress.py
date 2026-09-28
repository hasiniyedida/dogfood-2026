from urllib.request import Request, urlopen

BASE_URL = "http://localhost:8080"

request = Request(
    f"{BASE_URL}/api/organizer/judging-progress",
    headers={
        "Cookie": "session=org_7f2a"
    }
)

with urlopen(request) as response:
    print(response.status)
    print(response.read().decode())