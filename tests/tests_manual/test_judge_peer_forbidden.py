import urllib.request
import urllib.error

request = urllib.request.Request(
    "http://localhost:8080/api/judge/scores?judge=judge_a",
    headers={
        "Cookie": "session=jdg_b_44de"
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