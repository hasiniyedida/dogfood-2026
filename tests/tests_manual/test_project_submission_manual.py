import urllib.request
import urllib.error

project_id = "c8b6f821-d027-45f4-b8e1-8cb95ebee2cc"

request = urllib.request.Request(
    f"http://localhost:8080/projects/{project_id}/submit",
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