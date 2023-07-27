# -----------------------------------------------------------------------------
# Standard Python library imports
# -----------------------------------------------------------------------------
import json

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import configuration
import environ_manipulation
import logger
import login
import reading_lists

# -----------------------------------------------------------------------------
# Project constants
# -----------------------------------------------------------------------------
config = configuration.Configuration("project_config.conf")
debugging = config.get("debugging")  # Toggle whether logs are shown


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------
def write_log(msg, log):
    if log is not None:
        log.output_message(msg)


# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
# Note that this is not technically a middleware as it is not totally
# transparent, but it performs the same role.
class Middleware(object):
    def __init__(self, routes, log=None):
        self._routes = routes
        self._log = log
        write_log(f"Create Middleware object", self._log)

    def __call__(self, environ, start_response):
        target_name = environ_manipulation.application.get_target(environ)
        write_log(f"Attempting to redirect to {target_name} application", self._log)
        target_application = self._routes.get(target_name) or ErrorHandler("404 Not Found", log)
        return target_application(environ, start_response)


# -----------------------------------------------------------------------------
# Handler Base Class
# -----------------------------------------------------------------------------
class Handler(object):
    def __init__(self, log=None):
        self._routes = {}  # There are no routes for the base class - included so the __call__ should still work
        self._log = log
        write_log("Created " + __class__.__name__ + " instance", self._log)  # Cannot use
        # commas as it the method only takes 2 parameters, and these would
        # pass each element as a parameter

    def retrieve_post_parameters(self):
        try:
            body_size = int(self._environ["CONTENT_LENGTH"])
        except ValueError:
            body_size = 0

        return self._environ["wsgi.input"].read(body_size).decode("utf-8")

    def retrieve_get_parameters(self):
        query = self._environ.get("QUERY_STRING")
        if len(query) == 0:
            write_log("          Get parameters: #N/A", self._log)
            return None
        res = dict()
        for i in query.split("&"):
            pair = i.split("=")
            res[pair[0]] = pair[1].replace("%20", " ")  # Fix spaces in the result

        return res

    def __call__(self, environ, start_response):
        self._environ = environ  # Set so methods do not need to have it as a parameter.
        self.retrieve_get_parameters()
        write_log(self.__class__.__name__ + " object called", self._log)
        write_log(f"     Handling request. URI: {self._environ['REQUEST_URI']}", self._log)
        target_name = environ_manipulation.application.get_sub_target(self._environ)
        write_log(f"     Redirecting to {self.__class__.__name__}.{target_name}", self._log)
        target_function = self._routes.get(target_name) or ErrorHandler("404 Not Found", log).error_response
        response, status, response_headers = target_function()
        start_response(status, response_headers)
        write_log(f"     Response given.    status: {status}    headers: {response_headers}    response: {response}",
                  self._log)
        yield response.encode("utf-8")


# -----------------------------------------------------------------------------
# Account Handler
# -----------------------------------------------------------------------------
class AccountHandler(Handler):
    def __init__(self, log=None):
        super().__init__(log=log)
        self._routes = {
            "sign_in": self.sign_in,
            "sign_out": self.sign_out,
            "sign_up": self.sign_up
        }

    def sign_in(self):
        # Method is already specified for log - redirecting to object.method
        json_response = self.retrieve_post_parameters()
        response_dict = json.loads(json_response)
        username = response_dict["username"]
        try:
            user_id = login.account.check_credentials(
                username=username,
                password=response_dict["password"]
            )
            session_id = login.session.create_session(user_id)
            message = "Signed in successfully"
            write_log("          Signed into account     Username: " + username, self._log)
            write_log("          Session id: " + session_id, self._log)
        except login.InvalidUserCredentialsError:
            write_log("          Failed to sign into account     Username: " + username, self._log)
            message = "Invalid username or password"
            session_id = None
            write_log("          Session id: #N/A", self._log)

        response = json.dumps({
            "message": message,
            "session_id": session_id
        })

        status = "200 OK"

        response_headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def sign_out(self):
        session_id = self.retrieve_post_parameters()
        login.session.close(session_id)
        write_log("          Closed session     Session id: " + session_id, self._log)

        status = "200 OK"

        response = "true"  # Response is not needed – it is for completeness only. The client does not wait or respond.

        response_headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def sign_up(self):
        json_response = self.retrieve_post_parameters()
        response_dict = json.loads(json_response)
        username = response_dict["username"]
        try:
            user_id = login.account.create_user(
                first_name=response_dict["first_name"],
                surname=response_dict["surname"],
                username=username,
                password=response_dict["password"]
            )
            session_id = login.session.create_session(user_id)
            message = "Account created successfully"
            write_log("          Created account     Username: " + username, self._log)
        except login.UserExistsError:
            write_log("          Failed to create account - username is taken     Username: " + username, self._log)
            message = "Username is already taken."
            session_id = None  # json.dumps converts this to null automatically

        write_log("          Session id: " + session_id, self._log)

        response = json.dumps({
            "message": message,
            "session_id": session_id  # Success can be interpreted from the id
        })

        status = "200 OK"
        response_headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response)))
        ]
        return response, status, response_headers


# -----------------------------------------------------------------------------
# My Books Handler
# -----------------------------------------------------------------------------
class MyBooksHandler(Handler):
    def __init__(self, log=None):
        super().__init__(log=log)
        self._routes = {
            "get_lists": self.get_list_names,
            "get_list_entries": self.get_list_entries,
            "remove_list_entry": self.remove_list_entry
        }

    def get_list_names(self):
        session_id = self.retrieve_get_parameters()["session_id"]
        write_log("          Session id: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User id: " + str(user_id), self._log)

        names = reading_lists.get_names(user_id)
        response = json.dumps({i: names.pop() for i in range(names.size)})

        status = "200 OK"

        response_headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def get_list_entries(self):
        response_dict = self.retrieve_get_parameters()

        session_id = response_dict["session_id"]
        user_id = login.session.get_user_id(session_id)
        write_log("          Session id: " + session_id, self._log)

        list_name = response_dict["list_name"]
        write_log("          List name: " + list_name, self._log)

        entries = reading_lists.get_values(list_name, user_id)

        result = dict()

        result["books"] = [entries.pop() for i in range(entries.size)]
        if list_name == "Currently Reading":
            result["button"] = "Mark as read"
        elif list_name == "Want to Read":
            result["button"] = "Start Reading"
        else:
            result["button"] = None

        if not entries.size:
            result["meta"] = "You have no books in this list"
        else:
            result["meta"] = None

        response = json.dumps(result)  # Logging this will be slow – remove debug for production from config.

        status = "200 OK"

        response_headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def remove_list_entry(self):
        json_response = self.retrieve_post_parameters()
        response_dict = json.loads(json_response)
        session_id = response_dict["session_id"]
        list_name = response_dict["list_name"]
        book_title = response_dict["book_title"].replace("&amp;", "&")  # Replace ampersand code with character

        write_log("          Session id: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User id: " + str(user_id), self._log)

        write_log("          List name: " + list_name, self._log)
        write_log("          Book title: " + book_title, self._log)

        reading_lists.remove_entry(user_id, list_name, book_title)
        response = "true"  # A response is needed to use this result, but does not impact the client at all.

        status = "200 OK"

        response_headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers


# -----------------------------------------------------------------------------
# Error Handler
# -----------------------------------------------------------------------------
class ErrorHandler(Handler):
    def __init__(self, status, log=None):
        super().__init__(log=log)
        self._status = status

    def error_response(self):
        write_log(f"     Handling error: {self._status}", self._log)
        response = f"<h1>{self._status}</h1>"
        if self._status[0] == "4":  # Other messages are successful, so do not need to be created.
            response += "<p>The page you were looking for does not exist.</p>"
        elif self._status[0] == "5":
            response += "<p>An server error has occurred. Please try again later.</p>"

        response_headers = [
            ("Content-Type", "text/html")
        ]

        return response, self._status, response_headers  # Status is needed as this format is needed elsewhere

    def __call__(self, environ, start_response):
        write_log(self.__class__.__name__ + " object called", self._log)
        write_log(f"     Handling request. URI: {environ['REQUEST_URI']}", self._log)
        response, status, response_headers = self.error_response()  # Overwrite standard method. Different to reduce
        # necessary processing - it is known an error has occurred, it does not need to be checked for.
        start_response(status, response_headers)
        write_log(
            f"     Response given.    status: {self._status}    headers: {response_headers}    response: {response}",
            self._log)
        yield response.encode("utf-8")


# -----------------------------------------------------------------------------
# Object initialisation
# -----------------------------------------------------------------------------
if debugging:
    log = logger.Logging()
else:
    log = None

routes = {
    "account": AccountHandler(log),
    "my_books": MyBooksHandler(log)
    # Objects are persistent, so will the response should be faster and more memory efficient
}

app = Middleware(routes, log)
