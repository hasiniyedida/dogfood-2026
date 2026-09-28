import urllib.request
import urllib.error

invite_id = "d41045ba-8039-4442-b9a4-fe252c4a3d3a"

request = urllib.request.Request(
    f"http://localhost:8080/api/team-invites/{invite_id}/accept",
    headers={
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