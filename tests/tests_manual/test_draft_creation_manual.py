import urllib.request
import urllib.error
import urllib.parse

data = urllib.parse.urlencode({
    "team_id": "54638549-28e7-46c7-af08-772ce0a215f3",
    "track_id": "6c214a5f-8380-4b8d-bfe2-84553db90688",
    "title": "Open Event Test Project",
    "summary": "Testing draft creation during an open submission window.",
    "repo_url": "https://example.org/repo"
}).encode()

request = urllib.request.Request(
    "http://localhost:8080/projects/new",
    data=data,
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "session=prt_2e88"
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