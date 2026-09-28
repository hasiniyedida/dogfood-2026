import urllib.request
import urllib.error
import urllib.parse

data = urllib.parse.urlencode({
    "title": "Edited",
    "summary": "Edited summary",
    "repo_url": "https://example.org/edited"
}).encode()

request = urllib.request.Request(
    "http://localhost:8080/projects/prj_01",
    data=data,
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "session=prt_2e88"
    },
    method="PUT"
)

try:
    response = urllib.request.urlopen(request)
    print(response.status)
    print(response.read().decode())
except urllib.error.HTTPError as error:
    print(error.code)
    print(error.read().decode())