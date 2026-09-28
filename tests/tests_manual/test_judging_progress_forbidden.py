from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_URL = "http://localhost:8080"

sessions = {
    "judge": "jdg_a_91bc",
    "participant": "prt_2e88"
}

for role, session in sessions.items():
    request = Request(
        f"{BASE_URL}/api/organizer/judging-progress",
        headers={
            "Cookie": f"session={session}"
        }
    )

    try:
        with urlopen(request) as response:
            print(role, response.status)
    except HTTPError as error:
        print(role, error.code)