from urllib.request import Request, urlopen

request = Request(
    "http://localhost:8080/organizer/judging-progress",
    headers={
        "Cookie": "session=org_7f2a"
    }
)

with urlopen(request) as response:
    print(response.status)
    html = response.read().decode()
    print("Judging Progress" in html)
    print("total-projects" in html)
    print("progress-percent" in html)