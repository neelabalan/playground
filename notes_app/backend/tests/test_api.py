import unittest
import typing
import http
import http.client
import urllib3.exceptions
import http
import json
import collections
import subprocess
import time
import sqlite3
import logging
import pathlib

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(console_handler)


class Response:
    def __init__(self, status: http.HTTPStatus, body: list[dict] | dict | None = None):
        self.status = status
        self.body = body


class BaseRequest:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.conn = http.client.HTTPConnection(self.base_url)

    def __del__(self):
        if self.conn:
            self.conn.close()

    def make_request(self, method: str, path: str, body: dict | None = None, headers: dict | None = None) -> Response:
        if body is not None:
            body = json.dumps(body).encode("utf-8")
        if headers is None:
            headers = {"Content-Type": "application/json"}
        logger.info(f"{method=} -- {path=} -- {headers=} -- {body=}")
        data = None
        self.conn.request(method, path, body, headers)
        response = self.conn.getresponse()

        try:
            response_body = response.read().decode()
            if response_body:
                data = json.loads(response_body)
        except json.JSONDecodeError as ex:
            logger.error(f"Error decoding JSON string - {ex}")

        # except http.client.ResponseNotReady as ex:
        logger.info(f"Received response: {response.status} {response.reason}")
        return Response(status=response.status, body=data)


def tearDownModule():
    pathlib.Path("app").unlink()


class TestBase(unittest.TestCase):
    def build_app(self):
        app_path = pathlib.Path("app")
        if not app_path.exists():
            logger.info("Building the Go application...")
            subprocess.run(["go", "build", "-o", "app"])
        else:
            logger.info("Go application already exists, skipping build...")

    def setUp(self):
        self.request = BaseRequest("localhost:8080")
        # subprocess.run(["go", "build", "-o", "app"], cwd="../")
        self.build_app()

        # Start the executable
        self.process = subprocess.Popen(["./app"])
        logger.info("starting app...")

        # Wait for the server to start
        time.sleep(3)

    def clear_database(self, sql_file_path: str, db_path: str):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        with open(sql_file_path, "r") as sql_file:
            sql_script = sql_file.read()

        cursor.executescript(sql_script)
        conn.commit()
        conn.close()

    def tearDown(self):
        self.request.conn.close()
        self.process.terminate()
        self.process.wait()

        # Clear the database
        self.clear_database("sql/clear.sql", "dbstore/notes.db")

        self.request.conn.close()
        logger.info("Resource tear down completed")

    def assert_response(self, response: Response, expected_response: Response):
        self.assertEqual(response.status, expected_response.status)
        if expected_response.body:
            self.assertEqual(response.body, expected_response.body)


class TestHealthCheck(TestBase):
    def test_healthcheck(self):
        response = self.request.make_request("GET", "/health")
        self.assert_response(response, Response(status=http.HTTPStatus.OK, body={"message": "OK"}))


User = collections.namedtuple("User", ["username", "email", "password"])


class UserBase:
    user1 = User(username="testuser", email="testuser@example.com", password="password123")
    user2 = User(username="somerandomuser", email="somerandomuser@example.com", password="somerandomuserpassword")
    user1_duplicate = User(username="testuser_duplicate", email="testuser@example.com", password="password")


class Step:
    def __init__(self, method: str, endpoint: str, body: list[dict] | dict | None = None, headers: dict = {}):
        self.method = method
        self.endpoint = endpoint
        self.body = body
        self.headers = headers

        # some issue with test framework which causes incorrect instantiation 
        if body is None:
            self.body = None 
        
        if not headers:
            self.headers = {} 


FlowResponse = list[tuple[Step, Response]]


class FlowExecutor(TestBase):
    steps_and_expectations = []
    continue_on_error = False

    def setUp(self):
        super().setUp()
        self.request = BaseRequest("localhost:8080")
        self.responses: FlowResponse = []
        self._access_token = ""

    def execute_flow(self, steps: list[Step], continue_on_error: bool = False) -> FlowResponse:
        self._access_token = ""
        self.responses = []
        for step in steps:
            # Make the HTTP request
            if self._access_token:
                step.headers.update({"Authorization": f"Bearer {self._access_token}"})
            response = self.request.make_request(step.method, step.endpoint, body=step.body, headers=step.headers)

            if not self.continue_on_error:
                # adapted from https://github.com/psf/requests
                #
                http_error_msg = None
                if 400 <= response.status < 500:
                    http_error_msg = f"{response.status} Client Error for url: {step.endpoint}"

                elif 500 <= response.status < 600:
                    http_error_msg = f"{response.status} Server Error for url: {step.endpoint}"

                if http_error_msg:
                    raise urllib3.exceptions.HTTPError(http_error_msg)
                ###
            # get access token for future requests
            if step.method == "POST" and "signin" in step.endpoint:
                try:
                    self._access_token = response.body.get("access_token")
                    logger.info(f"Access token obtained for further request - {self._access_token}")
                except Exception as ex:
                    logger.error(f"Error decoding JSON response at /signin stage for - {ex}")

            self.responses.append((step, response))

        return self.responses

    def test_flow(self):
        responses = self.execute_flow([se[0] for se in self.steps_and_expectations])
        for idx, response in enumerate(responses):
            self.assert_response(response[1], self.steps_and_expectations[idx][1])


class TestAuthHappyFlow(FlowExecutor):
    steps_and_expectations: list[tuple[Step, Response]] = [
        (Step("POST", "/signup", body=UserBase.user1._asdict()), Response(status=http.HTTPStatus.CREATED, body={"message": "User created successfully"})),
        (Step("POST", "/signin", body={"email": UserBase.user1.email, "password": UserBase.user1.password}), Response(status=http.HTTPStatus.OK)),
        (Step("POST", "/create_note", body={}), Response(status=http.HTTPStatus.CREATED)),
    ]


class TestAuthNotSoHappyFlow(FlowExecutor):
    continue_on_error = True
    steps_and_expectations: list[tuple[Step, Response]] = [
        # Signup with user1 email
        (Step("POST", "/signup", body=UserBase.user1._asdict()), Response(status=http.HTTPStatus.CREATED, body={"message": "User created successfully"})),
        # Signup with duplicate user1 again
        (Step("POST", "/signup", body=UserBase.user1_duplicate._asdict()), Response(status=http.HTTPStatus.BAD_REQUEST)),
        # Sign-in with incorrect password
        (Step("POST", "/signin", body={"email": UserBase.user1.email, "password": "wrongpassword"}), Response(status=http.HTTPStatus.UNAUTHORIZED)),
        # Access protected endpoint without token
        (Step("POST", "/create_note", body={}), Response(status=http.HTTPStatus.FORBIDDEN)),
        # Access protected endpoint with invalid token
        (
            Step(
                "POST",
                "/create_note",
                body={},
                headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3R1c2VyQGV4YW1wbGUuY29tIiwiaWF0IjoxNTE2MjM5MDIyfQ.LLmhcQ8FWPWg-A4vodheqXyJ2ktsUkwV2iW_cMszp8I"},
            ),
            Response(status=http.HTTPStatus.FORBIDDEN),
        ),
    ]

if __name__ == "__main__":
    unittest.main()
