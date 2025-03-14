import os
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("TEST_USERNAME")
PASSWORD = os.getenv("TEST_PASSWORD")


@when("I log in with test credentials from a remote IP")
def login_from_remote():
    headers = {"X-Forwarded-For": "192.168.1.100"}
    response = requests.post(
        f"{API_URL}/login",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        headers=headers,
        cookies={}
    )
    pytest.remote_response = response

@then("I should be denied access")
def verify_remote_rejection():
    assert pytest.remote_response.status_code == 403
    assert pytest.remote_response.json()["detail"] == "Test credentials can only be used from localhost"
