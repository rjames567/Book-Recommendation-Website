# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import json

# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
import environ_manipulation
import login

# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------
def get_post_content(environ):
    try:
        body_size = int(environ["CONTENT_LENGTH"])
    except ValueError:
        body_size = 0

    return environ["wsgi.input"].read(body_size).decode("utf-8")

# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------
class Middleware:
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response

    def __iter__(self):
        environ_manipulation.application.add_target(self.environ)
        match self.environ["TARGET_APPLICATION"]:
            case "account":
                application = AccountApplication(self.environ, self.start)
                yield application()
            case _:
                response_headers = [("Content-Type", "text/plain")]
                self.start("200 OK", response_headers)
                yield "Page Not Found".encode("utf-8")

# ------------------------------------------------------------------------------
# Sub-Applications
# ------------------------------------------------------------------------------
class AccountApplication:
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response

    def create_account(self, json_response):
        response_dict = json.loads(json_response)
        try:
            user_id = login.account.create_user(
                first_name=response_dict["first_name"],
                surname=response_dict["surname"],
                username=response_dict["username"],
                password=response_dict["password"]
            )
            session_id = login.session.create_session(user_id)
            message = "Account created successfully"
        except login.UserExistsError:
            message = "Username is already taken."
            session_id = None # json.dumps converts this to null automatically

        result_dict = {
            "message": message,
            "session_id": session_id # Success can be interpreted from the id
        }

        return json.dumps(result_dict) # Convert dictionary to json.

    def sign_in(self, json_response):
        response_dict = json.loads(json_response)
        try:
            user_id = login.account.check_credentials(
                username=response_dict["username"],
                password=response_dict["password"]
            )
            session_id = login.session.create_session(user_id)
            message = "Signed in successfully"
        except login.InvalidUserCredentialsError:
            message = "Invalid username or password"
            session_id = None

        result_dict = {
            "message": message,
            "session_id": session_id
        }

        return json.dumps(result_dict)

    def __call__(self):
        environ_manipulation.application.add_sub_target(self.environ)
        match self.environ["APPLICATION_PROCESS"]:
            case "sign_up":
                post_content = get_post_content(self.environ)
                response = self.create_account(post_content)
                response_headers = [
                    ("Content-Type", "application/json"),
                    ("Content-Length", str(len(response)))
                ]
                self.start("200 OK", response_headers)

            case "sign_in":
                post_content = get_post_content(self.environ)
                response = self.sign_in(post_content)
                response_headers = [
                    ("Content-Type", "application/json"),
                    ("Content-Length", str(len(response)))
                ]
                self.start("200 OK", response_headers)
        return response.encode("utf-8")