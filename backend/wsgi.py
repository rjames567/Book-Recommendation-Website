# -----------------------------------------------------------------------------
# Standard Python library imports
# -----------------------------------------------------------------------------
import json
import urllib.parse

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import authors
import books
import configuration
import environ_manipulation
import genres
import logger
import login
import reading_lists

# -----------------------------------------------------------------------------
# Project constants
# -----------------------------------------------------------------------------
config = configuration.Configuration("./project_config.conf")
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
        arr_dict = urllib.parse.parse_qs(query)  # Returns dictionary of arrays {str: list}
        res = {i: arr_dict[i][0] for i in arr_dict.keys()}  # Convert to dictionary {str: str}
        #  Use urllib as it handles the non-printable characters – %xx
        return res

    def __call__(self, environ, start_response):
        self._environ = environ  # Set so methods do not need to have it as a parameter.
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
            ("Content-Type", "text/plain"),
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
            "remove_list_entry": self.remove_list_entry,
            "add_list_entry": self.add_list_entry,
            "move_list_entry": self.move_list_entry,
            "remove_list": self.remove_list,
            "create_list": self.create_list,
            "get_lists_book_target": self.get_list_names_include_book
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
        write_log("          Session id: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User id: " + str(user_id), self._log)

        list_id = response_dict["list_id"]
        write_log("          List ID: " + str(list_id), self._log)

        result = dict()

        entries, result["button"], result["move_target_id"] = reading_lists.get_values(list_id, user_id)

        result["books"] = [entries.pop() for i in range(entries.size)]

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
        list_id = response_dict["list_id"]
        book_id = response_dict["book_id"]  # Replace ampersand code with character

        write_log("          Session id: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User id: " + str(user_id), self._log)

        write_log("          List ID: " + str(list_id), self._log)
        write_log("          Book ID: " + str(book_id), self._log)

        reading_lists.remove_entry(user_id, list_id, book_id)
        response = "true"  # A response is needed to use this result, but does not impact the client at all.

        status = "200 OK"

        response_headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def move_list_entry(self):
        json_response = self.retrieve_post_parameters()
        response_dict = json.loads(json_response)
        session_id = response_dict["session_id"]
        list_id = response_dict["list_id"]
        book_id = response_dict["book_id"]

        write_log("          Session id: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User id: " + str(user_id), self._log)

        write_log("          List ID: " + str(list_id), self._log)
        write_log("          Book ID: " + str(book_id), self._log)

        target_list_id = response_dict["target_list_id"]
        write_log("          Target list ID: " + str(target_list_id), self._log)

        reading_lists.move_entry(user_id, list_id, target_list_id, book_id)

        response = "true"  # A response is needed to use this result, but does not impact the client at all.

        status = "200 OK"

        response_headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def remove_list(self):
        json_response = self.retrieve_post_parameters()
        response_dict = json.loads(json_response)
        session_id = response_dict["session_id"]
        list_id = response_dict["list_id"]

        write_log("          Session id: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User id: " + str(user_id), self._log)
        write_log("          List ID: " + str(list_id), self._log)

        reading_lists.remove_list(user_id, list_id)

        response = "true"  # A response is needed to use this result, but does not impact the client at all.

        status = "200 OK"

        response_headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def create_list(self):
        json_response = self.retrieve_post_parameters()
        response_dict = json.loads(json_response)
        session_id = response_dict["session_id"]
        list_name = response_dict["list_name"]

        write_log("          Session id: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User id: " + str(user_id), self._log)
        write_log("          List name: " + list_name, self._log)

        reading_lists.create_list(user_id, list_name)

        response = "true"  # A response is needed to use this result, but does not impact the client at all.

        status = "200 OK"

        response_headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def get_list_names_include_book(self):
        params = self.retrieve_get_parameters()
        session_id = params["session_id"]
        write_log("          Session id: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User id: " + str(user_id), self._log)
        book_id = params["book_id"]
        write_log("          Book id: " + str(book_id), self._log)

        result = reading_lists.get_names_check_book_in(user_id, book_id)

        response = json.dumps(result)

        status = "200 OK"

        response_headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def add_list_entry(self):
        params = self.retrieve_post_parameters()
        params = json.loads(params)
        session_id = params["session_id"]
        write_log("          Session id: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User id: " + str(user_id), self._log)
        book_id = params["book_id"]
        write_log("          Book id: " + str(book_id), self._log)
        list_id = params["list_id"]
        write_log("          List id: " + str(list_id), self._log)

        reading_lists.add_entry(user_id, list_id, book_id)

        response = "true"  # Response does not matter to the client

        status = "200 OK"

        response_headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers


# -----------------------------------------------------------------------------
# Genres Handler
# -----------------------------------------------------------------------------
class GenreHandler(Handler):
    def __init__(self, log=None):
        super().__init__(log=log)
        self._routes = {
            "about_data": self.get_genre_data
        }

    def get_genre_data(self):
        genre_name = self.retrieve_get_parameters()["genre_name"]
        write_log("          Genre name: " + genre_name, self._log)
        try:
            result = genres.get_about_data(genre_name)
            status = "200 OK"
            write_log("          Success", self._log)

            response = json.dumps(result)
            write_log("          Response: " + response, self._log)
            write_log("          Status: " + status, self._log)

            response_headers = [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(response)))
            ]

            return response, status, response_headers

        except genres.GenreNotFoundError:
            status = "404 Not Found"
            write_log("          Status: " + status, self._log)
            return ErrorHandler("404 Not Found").error_response()  # Return the content for a 404 error


# -----------------------------------------------------------------------------
# Book Handler
# -----------------------------------------------------------------------------
class BookHandler(Handler):
    def __init__(self, log=None):
        super().__init__(log)
        self._routes = {
            "about_data": self.get_book_data,
            "delete_review": self.delete_review,
            "add_review": self.leave_review
        }

    def get_book_data(self):
        get_params = self.retrieve_get_parameters()
        session_id = get_params["session_id"]
        book_id = get_params["book_id"]
        write_log("          Book ID: " + book_id, self._log)
        write_log("          Session ID: " + session_id, self._log)
        if session_id != "null":
            user_id = login.session.get_user_id(session_id)
        else:
            user_id = None
        write_log("          User ID: " + str(user_id), self._log)
        try:
            result = books.get_about_data(book_id, user_id)
            status = "200 OK"
            write_log("          Success", self._log)

            response = json.dumps(result)
            write_log("          Response: " + response, self._log)
            write_log("          Status: " + status, self._log)

            response_headers = [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(response)))
            ]

            return response, status, response_headers

        except books.BookNotFoundError:
            status = "404 Not Found"
            write_log("          Status: " + status, self._log)
            return ErrorHandler("404 Not Found").error_response()  # Return the content for a 404 error

    def delete_review(self):
        json_response = self.retrieve_post_parameters()
        params = json.loads(json_response)
        session_id = params["session_id"]
        review_id = params["review_id"]
        write_log("          Review ID: " + str(review_id), self._log)
        write_log("          Session ID: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User ID: " + str(user_id), self._log)

        books.delete_review(review_id, user_id)

        response = "true"  # A response is needed to use this result, but does not impact the client at all.

        status = "200 OK"

        response_headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def leave_review(self):
        json_response = self.retrieve_post_parameters()
        params = json.loads(json_response)
        write_log(params, self._log)
        session_id = params["session_id"]
        write_log("          Session ID: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User ID: " + str(user_id), self._log)
        book_id = params["book_id"]
        write_log("          Book ID: " + str(book_id), self._log)


        books.leave_review(
            user_id,
            book_id,
            params["overall_rating"],
            params["plot_rating"],
            params["character_rating"],
            params["summary"],
            params["thoughts"]
        )

        response = "true"  # A response is needed to use this result, but does not impact the client at all.

        status = "200 OK"

        response_headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers


# -----------------------------------------------------------------------------
# Book Handler
# -----------------------------------------------------------------------------
class AuthorHandler(Handler):
    def __init__(self, log=None):
        super().__init__(log)
        self._routes = {
            "follow_author": self.follow_author,
            "unfollow_author": self.unfollow_author
        }

    def follow_author(self):
        json_response = self.retrieve_post_parameters()
        params = json.loads(json_response)
        session_id = params["session_id"]
        author_id = params["author_id"]
        write_log("          Author ID: " + str(author_id), self._log)
        write_log("          Session ID: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User ID: " + str(user_id), self._log)

        authors.follow_author(user_id, author_id)

        response = str(authors.get_number_followers(author_id))  # Sends the new number of followers as the response.
        # Cast the integer result to string so it can be sent as text.

        status = "200 OK"

        response_headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def unfollow_author(self):
        json_response = self.retrieve_post_parameters()
        params = json.loads(json_response)
        session_id = params["session_id"]
        author_id = params["author_id"]
        write_log("          Author ID: " + str(author_id), self._log)
        write_log("          Session ID: " + session_id, self._log)
        user_id = login.session.get_user_id(session_id)
        write_log("          User ID: " + str(user_id), self._log)

        authors.unfollow_author(user_id, author_id)

        response = str(authors.get_number_followers(author_id)) # Sends the new amount followers as the response.
        # Cast the integer result to string, so it can be sent as text.

        status = "200 OK"

        response_headers = [
            ("Content-Type", "text/plain"),
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
        # necessary processing – it is known an error has occurred, it does not need to be checked for.
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

# https://www.sitepoint.com/python-web-applications-the-basics-of-wsgi/
routes = {
    "account": AccountHandler(log),
    "my_books": MyBooksHandler(log),
    "genres": GenreHandler(log),
    "books": BookHandler(log),
    "authors": AuthorHandler(log)
    # Objects are persistent, so will the response should be faster and more memory efficient.
}

app = Middleware(routes, log)

# FIXME Fix errors with sessionIDs of null.