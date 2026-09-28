import urllib.request
import urllib.error

invite_id = "52d4aadc-7008-4c2a-bac5-4ccf4399fccd"

request = urllib.request.Request(
    f"http://localhost:8080/api/judge-invites/{invite_id}/accept",
    headers={
        "Cookie": "session=jdg_a_91bc"
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