#!/usr/bin/env python3.10

# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import json

# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
import environ_manipulation
import logger
import login
import reading_lists

# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
log = logger.Logging(clear=False,filepath="/tmp/logging/")

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
            case "my_books":
                application = MyBooksApplication(self.environ, self.start)
                yield application()
            case _:
                response_headers = [("Content-Type", "text/plain")]
                self.start("200 OK", response_headers)
                yield "Page Not Found".encode("utf-8")

# ------------------------------------------------------------------------------
# Application base class
# ------------------------------------------------------------------------------
class Application:
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response

    def get_post_data(self):
        try:
            body_size = int(self.environ["CONTENT_LENGTH"])
        except ValueError:
            body_size = 0

        return self.environ["wsgi.input"].read(body_size).decode("utf-8")

# ------------------------------------------------------------------------------
# Account application
# ------------------------------------------------------------------------------
class AccountApplication (Application):
    def __init__(self, environ, start_response):
        super().__init__(environ, start_response)

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

    def sign_out(self, session_id):
        login.session.close(session_id)
        return "true" # Response does not matter - client does not wait for one.

    def __call__(self):
        environ_manipulation.application.add_sub_target(self.environ)
        match self.environ["APPLICATION_PROCESS"]:
            case "sign_up":
                post_content = self.get_post_data()
                response = self.create_account(post_content)
                response_headers = [
                    ("Content-Type", "application/json"),
                    ("Content-Length", str(len(response)))
                ]
                self.start("200 OK", response_headers)

            case "sign_in":
                post_content = self.get_post_data()
                response = self.sign_in(post_content)
                response_headers = [
                    ("Content-Type", "application/json"),
                    ("Content-Length", str(len(response)))
                ]
                self.start("200 OK", response_headers)
            case "sign_out":
                post_content = self.get_post_data()
                response = self.sign_out(post_content) # Response is for
                    # completeness
                response_headers = [
                    ("Content-Type", "test/plain"),
                    ("Content-Length", str(len(response)))
                ]
                self.start("200 OK", response_headers)
            case _:
                response_headers = [("Content-Type", "text/plain")]
                self.start("200 OK", response_headers)
                response = "Page Not Found"
        return response.encode("utf-8")

# ------------------------------------------------------------------------------
# Account application
# ------------------------------------------------------------------------------
class MyBooksApplication (Application):
    def __init__(self, environ, start_response):
        super().__init__(environ, start_response)

    def get_list_names(self, session_id):
        user_id = login.session.get_user_id(session_id)

        names = reading_lists.get_names(user_id)
        result = {i: names.pop() for i in range(names.size)}

        return json.dumps(result)

    def get_list_content(self, response_json):
        response_dict = json.loads(response_json)
        user_id = login.session.get_user_id(response_dict["session_id"])

        entries = reading_lists.get_values(response_dict["list_name"], user_id)

        result = {}

        result["books"] = [entries.pop() for i in range(entries.size)]
        if not entries.size:
            result["meta"] = "You have no books in this list"
        else:
            result["meta"] = None

        return json.dumps(result)


    def __call__(self):
        environ_manipulation.application.add_sub_target(self.environ)
        match self.environ["APPLICATION_PROCESS"]:
            case "get_lists":
                post_content = self.get_post_data()
                response = self.get_list_names(post_content)
                response_headers = [
                    ("Content-Type", "application/json"),
                    ("Content-Length", str(len(response)))
                ]
                self.start("200 OK", response_headers)
            case "get_list_entries":
                post_content = self.get_post_data()
                response = self.get_list_content(post_content)
                response_headers = [
                    ("Content-Type", "application/json"),
                    ("Content-Length", str(len(response)))
                ]
                self.start("200 OK", response_headers)
            case _:
                response_headers = [("Content-Type", "text/plain")]
                self.start("404 Page Not Found", response_headers)
                response = "Page Not Found"
        return response.encode("utf-8")
