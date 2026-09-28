import urllib.request
import urllib.error

request = urllib.request.Request(
    "http://localhost:8080/api/judge/scores",
    headers={
        "Cookie": "session=prt_2e88"
    },
    method="GET"
)

try:
    response = urllib.request.urlopen(request)
    print(response.status)
    print(response.read().decode())

except urllib.error.HTTPError as error:
    print(error.code)
    print(error.read().decode())