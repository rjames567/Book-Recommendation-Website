# -----------------------------------------------------------------------------
# Standard Python library imports
# -----------------------------------------------------------------------------
import datetime
import hashlib
import json
import re
import secrets
import time
import urllib.parse

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import accounts as accounts_mod  # Can't use standard name, as it is the logical
# name for the class instance.
import authors as author_mod
import books as book_mod
import diaries as diaries_mod
import genres as genres_mod
import reading_lists as reading_lists_mod
import recommendations

import configuration
import data_structures
import environ_manipulation
import logger
import ml_utilities
import mysql_handler

# -----------------------------------------------------------------------------
# Project constants
# -----------------------------------------------------------------------------
config = configuration.Configuration("./project_config.conf")
debugging = config.get("debugging")  # Toggle whether logs are shown
number_hash_passes = config.get("passwords number_hash_passes")
hashing_salt = config.get("passwords salt")  # Stored in the config as binary
hashing_algorithm = config.get("passwords hashing_algorithm")
token_size = config.get("session_id_length")
genre_required_match = config.get("books genre_match_threshold")
number_summaries_home = 8
number_similarities_about = 10
num_display_genres = 10

# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------
def write_log(msg, log):
    if log is not None:
        log.output_message(msg)

# -----------------------------------------------------------------------------
# Database connection
# -----------------------------------------------------------------------------
connection = mysql_handler.Connection(
    user=config.get("mysql username"),
    password=config.get("mysql password"),
    schema=config.get("mysql schema"),
    host=config.get("mysql host")
)

# -----------------------------------------------------------------------------
# Class instantiation
# -----------------------------------------------------------------------------
diaries = diaries_mod.Diaries(connection)
genres = genres_mod.Genres(connection)
sessions = accounts_mod.Sessions(connection, token_size)
authors = author_mod.Authors(connection)
reading_lists = reading_lists_mod.ReadingLists(
    connection,
    number_summaries_home,
    genre_required_match,
    num_display_genres
)
books = book_mod.Books(
    connection,
    genre_required_match,
    number_similarities_about,
    number_summaries_home,
    num_display_genres
)
accounts = accounts_mod.Accounts(
    connection,
    hashing_algorithm,
    hashing_salt,
    number_hash_passes,
    reading_lists
)


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
        # write_log(f"     Response given.    status: {status}    headers: {response_headers}    response: {response}",
                #   self._log)
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
            user_id = accounts.check_credentials(
                username=username,
                password=response_dict["password"]
            )
            session_id = sessions.create_session(user_id)
            message = "Signed in successfully"
            write_log("          Signed into account     Username: " + username, self._log)
            write_log("          Session id: " + session_id, self._log)
        except accounts_mod.InvalidUserCredentialsError:
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
        sessions.close(session_id)
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
            user_id = accounts.create_user(
                first_name=response_dict["first_name"],
                surname=response_dict["surname"],
                username=username,
                password=response_dict["password"]
            )
            session_id = sessions.create_session(user_id)
            message = "Account created successfully"
            write_log("          Created account     Username: " + username, self._log)
        except accounts_mod.UserExistsError:
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
        user_id = sessions.get_user_id(session_id)
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
        user_id = sessions.get_user_id(session_id)
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
        user_id = sessions.get_user_id(session_id)
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
        user_id = sessions.get_user_id(session_id)
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
        user_id = sessions.get_user_id(session_id)
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
        user_id = sessions.get_user_id(session_id)
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
        user_id = sessions.get_user_id(session_id)
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
        user_id = sessions.get_user_id(session_id)
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

        except genres_mod.GenreNotFoundError:
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
            user_id = sessions.get_user_id(session_id)
        else:
            user_id = None
        write_log("          User ID: " + str(user_id), self._log)
        try:
            result = books.get_about_data(book_id, user_id)

            result["similar_books"] = books.get_similar_items(int(book_id))
            status = "200 OK"
            write_log("          Success", self._log)

            response = json.dumps(result)
            # write_log("          Response: " + response, self._log)
            write_log("          Status: " + status, self._log)

            response_headers = [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(response)))
            ]

            return response, status, response_headers

        except book_mod.BookNotFoundError:
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
        user_id = sessions.get_user_id(session_id)
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
        user_id = sessions.get_user_id(session_id)
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
# Author Handler
# -----------------------------------------------------------------------------
class AuthorHandler(Handler):
    def __init__(self, log=None):
        super().__init__(log)
        self._routes = {
            "follow_author": self.follow_author,
            "unfollow_author": self.unfollow_author,
            "about_data": self.get_author_data
        }

    def follow_author(self):
        json_response = self.retrieve_post_parameters()
        params = json.loads(json_response)
        session_id = params["session_id"]
        author_id = params["author_id"]
        write_log("          Author ID: " + str(author_id), self._log)
        write_log("          Session ID: " + session_id, self._log)
        user_id = sessions.get_user_id(session_id)
        write_log("          User ID: " + str(user_id), self._log)

        authors.follow(user_id, author_id)

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
        user_id = sessions.get_user_id(session_id)
        write_log("          User ID: " + str(user_id), self._log)

        authors.unfollow(user_id, author_id)

        response = str(authors.get_number_followers(author_id))  # Sends the new amount followers as the response.
        # Cast the integer result to string, so it can be sent as text.

        status = "200 OK"

        response_headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def get_author_data(self):
        get_params = self.retrieve_get_parameters()
        author_id = get_params["author_id"]
        write_log("          Author ID: " + str(author_id), self._log)
        try:
            result = authors.get_about_data(author_id)
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

        except author_mod.AuthorNotFoundError:
            status = "404 Not Found"
            write_log("          Status: " + status, self._log)
            return ErrorHandler("404 Not Found").error_response()  # Return the content for a 404 error


# -----------------------------------------------------------------------------
# Author Handler
# -----------------------------------------------------------------------------
class DiaryHandler(Handler):
    def __init__(self, log=None):
        super().__init__(log)
        self._routes = {
            "get_entries": self.get_entries,
            "delete_entry": self.delete_entry,
            "add_entry": self.add_entry
        }

    def get_entries(self):
        session_id = self.retrieve_get_parameters()["session_id"]  # Only has one parameter, so this is fine.
        write_log("          Session ID: " + session_id, self._log)
        user_id = sessions.get_user_id(session_id)
        write_log("          User ID: " + str(user_id), self._log)

        result = dict()
        result["entries"] = diaries.get_entries(user_id)
        result["books"] = reading_lists.get_currently_reading(user_id)

        response = json.dumps(result)

        status = "200 OK"

        write_log("          Response: " + response, self._log)
        write_log("          Status: " + status, self._log)

        response_headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def delete_entry(self):
        json_response = self.retrieve_post_parameters()
        params = json.loads(json_response)
        session_id = params["session_id"]
        entry_id = params["entry_id"]
        write_log("          Entry ID: " + str(entry_id), self._log)
        write_log("          Session ID: " + session_id, self._log)
        user_id = sessions.get_user_id(session_id)
        write_log("          User ID: " + str(user_id), self._log)

        diaries.delete_entry(user_id, entry_id)

        response = "true"  # The client does not need the response. This is just for completeness, and a value is
        # required for the return statement.

        status = "200 OK"

        write_log("          Response: " + response, self._log)
        write_log("          Status: " + status, self._log)

        response_headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers

    def add_entry(self):
        json_response = self.retrieve_post_parameters()
        params = json.loads(json_response)
        session_id = params["session_id"]
        book_id = params["book_id"]
        write_log("          Session ID: " + session_id, self._log)
        user_id = sessions.get_user_id(session_id)
        write_log("          User ID: " + str(user_id), self._log)
        write_log("          Book ID: " + str(book_id), self._log)

        diaries.add_entry(
            user_id,
            book_id,
            params["overall_rating"],
            params["character_rating"],
            params["plot_rating"],
            params["summary"],
            params["thoughts"],
            params["pages_read"]
        )

        response = "true" # The response does not matter - here for completeness only

        status = "200 OK"

        write_log("          Response: " + response, self._log)
        write_log("          Status: " + status, self._log)

        response_headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(response)))
        ]

        return response, status, response_headers


# -----------------------------------------------------------------------------
# Home Handler
# -----------------------------------------------------------------------------
class HomeHandler(Handler):
    def __init__(self, log=None):
        super().__init__(log)
        self._routes = {
            "get_data": self.get_data
        }
    
    def get_data(self):
        session_id = self.retrieve_get_parameters()["session_id"]  # Only has one parameter, so this is fine.
        result = dict()
        if session_id != "null": # retrieve_get_parameters does not convert "null" to None.
            write_log("          Session ID: " + session_id, self._log)
            user_id = sessions.get_user_id(session_id)
            write_log("          User ID: " + str(user_id), self._log)

            result["recommended"] = {}  # TODO update this once recommendation methods are made
            result["currently_reading"] = reading_lists.get_currently_reading(user_id)
            result["want_read"] = reading_lists.get_want_read(user_id)
        else:
            write_log("          Session ID: None", self._log)
            result["recommended"] = None
            result["currently_reading"] = None
            result["want_read"] = None
        
        result["trending"] = reading_lists.get_popular()
        result["newest_additions"] = books.get_newest()

        response = json.dumps(result)

        status = "200 OK"

        write_log("          Response: " + response, self._log)
        write_log("          Status: " + status, self._log)

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
    "authors": AuthorHandler(log),
    "diary": DiaryHandler(log),
    "home": HomeHandler(log)
    # Objects are persistent, so will the response should be faster and more memory efficient.
}

app = Middleware(routes, log)

# FIXME Fix errors with sessionIDs of null.
