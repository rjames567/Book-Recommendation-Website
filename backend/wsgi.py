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
import authors as author_mod  # Can't use standard name, as it is the logical
# name for the class instance.
import books as book_mod
import configuration
import data_structures
import environ_manipulation
import logger
import ml_utilities
import mysql_handler
import recommendations

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
# Exceptions
# -----------------------------------------------------------------------------
class GenreNotFoundError(Exception):
    """
    Exception for when a genre is not found.
    """

    def __init__(self, genre_name):
        message = f"Genre '{genre_name}' was not found"
        super().__init__(message)


class SessionExpiredError(Exception):
    """
    Exception for when a client is using a session that has expired, and is no
    longer valid.
    """

    def __init__(self, session_id):
        message = f"Session id '{session_id}' has expired"
        super().__init__(message)


class UserExistsError(Exception):
    """
    Exception for when a user account already exists with a specific username,
    and it has been attempted to add a second.

    Usernames must be unique in the database.
    """

    def __init__(self, username):
        message = f"User already exists with the username {username}."
        super().__init__(message)


class InvalidUserCredentialsError(Exception):
    """
    Exception for where a user's provided username and password are not valid.
    """

    def __init__(self, username):
        message = f"Incorrect username or password entered for {username}"
        super().__init__(message)

class ListNotFoundError(Exception):
    """
    Exception for when a user's list is not found
    """
    def __init__(self, list_name, user_id):
        message = f"User with id '{user_id} does not have a list called {list_name}."
        super().__init__(message)


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
authors = author_mod.Authors(connection)
books = book_mod.Books(
    connection,
    genre_required_match,
    number_similarities_about,
    number_summaries_home,
    num_display_genres,
    authors
)

# -----------------------------------------------------------------------------
# Diaries
# -----------------------------------------------------------------------------
class diaries:
    def add_entry(user_id, book_id, overall_rating, character_rating, plot_rating, summary, thoughts, pages_read):
        params = locals()
        params = {i: "null" if k is None else k for i, k in zip(params.keys(), params.values())}
        if thoughts is not None:
            params["thoughts"] = '"' + re.sub("\n+", "\n", params["thoughts"]) + '"'
        if summary is not None:
            params["summary"] = '"' + params["summary"] + '"'
        connection.query("""
            INSERT INTO diary_entries (user_id, book_id, overall_rating, character_rating, plot_rating, summary, thoughts, pages_read)
            VALUES
            ({user_id}, {book_id}, {overall_rating}, {character_rating}, {plot_rating}, {summary}, {thoughts}, {pages_read});
        """.format(
            user_id=params["user_id"],
            book_id=params["book_id"],
            overall_rating=params["overall_rating"],
            character_rating=params["character_rating"],
            plot_rating=params["plot_rating"],
            summary=params["summary"],
            thoughts=params["thoughts"],
            pages_read=params["pages_read"]
        ))

    def delete_entry(user_id, entry_id):
        # The user id is just a way of helping preventing a random deletion of a list. The corresponding user_id must be
        # known.
        connection.query("""
            DELETE from diary_entries
            WHERE user_id={user_id}
                AND entry_id={entry_id};
        """.format(user_id=user_id, entry_id=entry_id))

    def get_entries(user_id):
        res = connection.query("""
            SELECT diary_entries.entry_id,
                diary_entries.book_id,
                diary_entries.overall_rating,
                diary_entries.character_rating,
                diary_entries.plot_rating,
                diary_entries.summary,
                diary_entries.thoughts,
                diary_entries.date_added,
                diary_entries.pages_read,
                books.cover_image,
                books.title,
                authors.author_id,
                authors.first_name,
                authors.surname,
                authors.alias,
                (SELECT IFNULL(ROUND(AVG(reviews.overall_rating), 2), 0)
                    FROM reviews
                    WHERE reviews.book_id=books.book_id) AS average_rating,
                (SELECT COUNT(reviews.overall_rating)
                    FROM reviews
                    WHERE reviews.book_id=books.book_id) AS num_rating
            FROM diary_entries
            INNER JOIN books ON books.book_id=diary_entries.book_id
            INNER JOIN authors ON books.author_id=authors.author_id
            WHERE diary_entries.user_id={}
            ORDER BY diary_entries.date_added DESC;
        """.format(user_id))  # Order by ensures that most recent is at the top.

        output_dict = dict()
        for i, k in enumerate(res):
            first_name = k[12]
            surname = k[13]
            alias = k[14]
            if (alias is not None and
                    (first_name is not None and surname is not None)):
                author = f"{alias} ({first_name} {surname})"
            elif (alias is not None and
                  (first_name is None and surname is None)):
                author = alias
            else:
                author = f"{first_name} {surname}"

            thoughts = k[6]
            if thoughts is not None:
                thoughts = "</p><p>".join(("<p>" + k[6] + "</p>").split("\n"))
            output_dict[i] = {
                "entry_id": k[0],
                "book_id": k[1],
                "overall_rating": k[2],
                "character_rating": k[3],
                "plot_rating": k[4],
                "summary": k[5],
                "thoughts": thoughts,
                "date_added": k[7].strftime("%d-%m-%Y"),
                "pages_read": k[8],
                "cover_image": k[9],
                "title": k[10],
                "author_id": k[11],
                "author_name": author,
                "average_rating": float(k[15]),
                "number_ratings": k[16]
            }

        return output_dict


# -----------------------------------------------------------------------------
# Genres
# -----------------------------------------------------------------------------
class genres:
    def get_about_data(genre_name):
        res = connection.query("""
            SELECT genre_id, name, about FROM genres
            WHERE name="{genre_name}";
        """.format(
            genre_name=genre_name))  # There will only be one entry with that name, so take only tuple from result
        # list

        if len(res) == 0:  # Protect against a list out of range errors
            raise GenreNotFoundError(genre_name)
        else:
            res = res[0]

        db_books = connection.query("""
            SELECT books.book_id, books.title, books.cover_image, authors.first_name, authors.surname, authors.alias FROM books
            INNER JOIN authors ON books.author_id=authors.author_id
            INNER JOIN book_genres ON books.book_id=book_genres.book_id
            INNER JOIN genres ON genres.genre_id=book_genres.genre_id
            WHERE genres.genre_id={genre_id};
        """.format(genre_id=res[0]))

        book_dict = dict()
        for i, k in enumerate(db_books):
            book_id, title, cover, first_name, surname, alias = k
            if (alias is not None and
                    (first_name is not None and surname is not None)):
                author = f"{alias} ({first_name} {surname})"
            elif (alias is not None and
                  (first_name is None and surname is None)):
                author = alias
            else:
                author = f"{first_name} {surname}"

            book_dict[i] = {
                "id": book_id,
                "title": title,
                "author": author,
                "cover": cover
            }

        output_dict = {
            "name": res[1],
            "about": "</p><p>".join(("<p>" + res[2] + "</p>").split("\n")),
            # Split each paragraph into <p></p> elements
            "books": book_dict
        }

        return output_dict


# -----------------------------------------------------------------------------
# Login
# -----------------------------------------------------------------------------
class login:
    def hash_password(password):
        """
        Method to hash the password, including a salt.

        password -> string
            The string that is to be hashed.

        Returns a string.
        """
        result = hashlib.pbkdf2_hmac(
            hashing_algorithm,
            password.encode("utf-8"),  # Needs to be in binary
            hashing_salt,  # Salt needs to be in binary - stored as binary in config
            number_hash_passes  # Recommended number of passes is 100,000
        )

        return result.hex()  # Hash is returned as a hex string, so converts back


class accounts:
    def check_credentials(username, password):
        """
        Method to check whether given user credentials are stored in the
        database.

        username -> string
            The username that is to be checked

        password -> string
            The password that is to checked

        Raises InvalidUserCredentialsError if the credentials are incorrect.

        Returns an integer value for the
        """
        entered_password = login.hash_password(password)
        query_result = connection.query(
            """
            SELECT password_hash FROM users
            WHERE username="{}";
            """.format(username)
        )

        if (len(query_result) == 0) or (query_result[0][0] != entered_password):
            raise InvalidUserCredentialsError(username)
        else:
            return accounts.get_user_id(username)

    def create_user(first_name, surname, username, password):
        """
        Method to create a new user in the database.

        first_name -> string
            The first name of the new user

        surname -> string
            The surname of the new user

        username -> string
            The unique identifier for the new user

        password -> string
            The password for the new user

        Raises UserExistsError, if the username provided already is in the
        database, as usernames must be unique.

        Returns an integer, which is the user id of the new user.
        """
        query_result = connection.query(
            """
            SELECT username FROM users
            WHERE username="{}"
            """.format(username)
        )

        if len(query_result):
            raise UserExistsError(username)
        else:
            connection.query(
                """
                INSERT INTO users (first_name, surname, username, password_hash)
                VALUES ("{first_name}", "{surname}", "{username}", "{password}");
                """.format(
                    first_name=first_name,
                    surname=surname,
                    username=username,
                    password=login.hash_password(password)  # Password must be hashed before
                    # storing in the database.
                )
            )

            user_id = connection.query(
                """
                SELECT user_id FROM users
                WHERE username="{}"
                """.format(username)
            )[0][0]

            reading_lists.create_list(user_id, "Want to Read")
            reading_lists.create_list(user_id, "Currently Reading")
            reading_lists.create_list(user_id, "Have Read")

            return user_id

    def get_user_id(username):
        """
        Method to get the corresponding id of the given username.

        username -> string
            The target username to get the id of

        Returns an integer.
        """
        query_result = connection.query(
            """
            SELECT user_id FROM users
            WHERE username="{}";
            """.format(username)
        )

        return query_result[0][0]


# -----------------------------------------------------------------------------
# Sessions
# -----------------------------------------------------------------------------
class sessions:
    def create_session(user_id):
        """
        Method to create new session. Adds the new session token to the
        database, which can the be queries using it, to get the corresponding
        user id.

        user_id -> integer
            The user id for the new session

        Return a string, which is the session token, to be sent to the client
        after login.
        """
        token = secrets.token_bytes(token_size).hex() + str(time.time()).replace(".", "")  # Remove the fullstops from
        # the time to make it shorter
        # Generates a random string, and adds time to reduce required size of
        # the randomly generated string for speed.
        # https://docs.python.org/3/library/secrets.html#:~:text=it%20is%20believed%20that%2032%20bytes%20(256%20bits)%20of%20randomness%20is%20sufficient%20for%20the%20typical%20use%2Dcase%20expected%20for%20the%20secrets%20module

        # Probability of getting duplicates is very low, and gets lower as the
        # size of the string increases. It would also need to be within 1
        # second, as time.time() is added to the end which is the number of
        # seconds since the epoch.

        connection.query(
            """
            INSERT INTO sessions (client_id, user_id) VALUES ("{token}", {user_id});
            """.format(token=token, user_id=user_id)
        )

        return token

    def update_time(session_id):
        """
        Method to update the stored session time to the current time, so that
        the timeout for the session is reset.

        session_id -> string
            The session id for which the creation time needs to be updated for

        Does not have a return value
        """
        connection.query(
            """
            UPDATE sessions
            SET
                date_added=NOW()
            WHERE client_id="{}";
            """.format(session_id)
        )

    def get_user_id(session_id):
        """
        Method to get the corresponding user_id to the session id passed in. It
        checks whether the session has expired, and if it has expired, it raises
        a SessionExpiredError. If it has not, it returns the user id.

        When the session has expired, it removes the entry from the database.

        session_id -> string
            The session id to get corresponding user id of

        Returns an integer of the user id.
        """
        res = connection.query(
            """
            SELECT user_id, date_added FROM sessions
            WHERE client_id="{}";
            """.format(session_id)
        )
        if len(res) == 0:
            raise SessionExpiredError(session_id)  # If there is no entries
            # it must have been deleted by a maintenance script, as it had
            # expired.
        else:
            res = res[0]  # Gets first element result from list - should only be
            # one result
        expiry_datetime = res[1] + datetime.timedelta(days=1)
        # Set expiry date to one day after it has been last used

        if datetime.datetime.now() > expiry_datetime:
            sessions.close(session_id)
            raise SessionExpiredError(session_id)
        else:
            return res[0]

        # Does not update the session time - Excluded from this as any request
        # from the client indicates that is still active, regardless of whether
        # the user id is needed to carry out the required process.

    def close(session_id):
        """
        Method to close an open session using the session id, which is has been sent
        to the client. It should be called when the browser/tab is closed.

        session_id -> string
            The session id which should be closed

        Does not have a return value.
        """
        connection.query(
            """
            DELETE FROM sessions
            WHERE client_id="{}";
            """.format(session_id)
        )


# -----------------------------------------------------------------------------
# Reading lists
# -----------------------------------------------------------------------------
class reading_lists:
    def get_popular():
        res = connection.query("""
            SELECT books.book_id,
                books.title,
                books.cover_image,
                authors.first_name,
                authors.surname,
                authors.alias,
                COUNT(books.book_id) as num
            FROM books
            INNER JOIN authors ON books.author_id=authors.author_id
            INNER JOIN reading_lists ON reading_lists.book_id=books.book_id
            INNER JOIN reading_list_names ON reading_list_names.list_id=reading_lists.list_id
            WHERE reading_list_names.list_name="Currently Reading"
            GROUP BY books.book_id
            ORDER BY num DESC;
        """)[:number_summaries_home]

        output_dict = dict()
        for i, k in enumerate(res):
            output_dict[i] = {
                "author": authors.names_to_display(k[5], k[3], k[4]),
                "title": k[1],
                "book_id": k[0],
                "cover": k[2],
            }
        
        return output_dict
    
    def get_list_id(list_name, user_id):
        res = connection.query("""
            SELECT list_id
            FROM reading_list_names
            WHERE user_id={user_id}
                AND list_name={list_name};
        """.format(user_id=user_id, list_name=list_name))

        if len(res) == 0:
            raise ListNotFoundError(list_name, user_id)
        
        return res[0][0]

    def get_names(user_id):
        res = connection.query(
            """
            SELECT list_id, list_name FROM reading_list_names
            WHERE user_id={};
            """.format(user_id)
        )  # List of single element tuples
        output_queue = data_structures.Queue()
        for i in res:
            output_queue.push({
                "id": i[0],
                "name": i[1]
            })

        return output_queue

    def get_currently_reading(user_id):
        res = connection.query("""
            SELECT books.book_id,
                books.title,
                books.cover_image,
                authors.first_name,
                authors.surname,
                authors.alias
            FROM reading_lists
            INNER JOIN books ON reading_lists.book_id=books.book_id
            INNER JOIN authors ON books.author_id=authors.author_id
            INNER JOIN reading_list_names ON reading_list_names.list_id=reading_lists.list_id
            WHERE reading_list_names.list_name="Currently Reading"
                AND reading_list_names.user_id={};
        """.format(user_id))
        return [{
                "author": authors.names_to_display(i[5], i[3], i[4]),
                "title": i[1],
                "book_id": i[0],
                "cover": i[2],
            } for i in res]

    def get_want_read(user_id):
        res = connection.query("""
            SELECT books.book_id,
                books.title,
                books.cover_image,
                authors.first_name,
                authors.surname,
                authors.alias
            FROM reading_lists
            INNER JOIN books ON reading_lists.book_id=books.book_id
            INNER JOIN authors ON books.author_id=authors.author_id
            INNER JOIN reading_list_names ON reading_list_names.list_id=reading_lists.list_id
            WHERE reading_list_names.list_name="Want to Read"
                AND reading_list_names.user_id={};
        """.format(user_id))
        return [{
                "author": authors.names_to_display(i[5], i[3], i[4]),
                "title": i[1],
                "book_id": i[0],
                "cover": i[2],
            } for i in res]

    def get_names_check_book_in(user_id, book_id):
        res = connection.query(
            """
            SELECT list_id, list_name FROM reading_list_names
            WHERE user_id={};
            """.format(user_id)
        )

        lists = dict()
        for i, k in enumerate(res):
            list_id, list_name = k
            in_list = bool(len(connection.query("""
                SELECT book_id FROM reading_lists
                WHERE list_id={list_id}
                    AND book_id={book_id};
            """.format(list_id=list_id, book_id=book_id))))
            lists[i] = {
                "id": list_id,
                "list_name": list_name,
                "has_book": in_list
            }

        return lists

    def get_values(list_id, user_id):
        res = connection.query("""
            SELECT books.book_id,
                books.cover_image,
                books.title,
                books.synopsis,
                authors.first_name,
                authors.surname,
                authors.alias,
                authors.author_id,
                reading_lists.date_added,
                (SELECT GROUP_CONCAT(genres.name)
                    FROM book_genres
                    inner join books on book_genres.book_id=books.book_id
                    inner join genres on genres.genre_id=book_genres.genre_id
                    WHERE book_genres.book_id=reading_lists.book_id
                        AND book_genres.match_strength>{match_strength}
                    GROUP by books.title) AS genres,
                (SELECT CAST(IFNULL(AVG(reviews.overall_rating), 0) as FLOAT)  # Prevent any null values - replace with 0s.
                    FROM reviews
                    WHERE reviews.book_id=books.book_id) AS average_rating,
                (SELECT COUNT(reviews.overall_rating)
                    FROM reviews
                    WHERE reviews.book_id=books.book_id) AS num_ratings
                FROM reading_lists
                INNER JOIN books
                ON books.book_id=reading_lists.book_id
                INNER JOIN authors
                ON books.author_id=authors.author_id
                INNER JOIN reading_list_names
                ON reading_list_names.list_id=reading_lists.list_id
                WHERE reading_lists.list_id={list_id}
                    AND reading_lists.user_id={user_id}
                ORDER BY reading_lists.date_added DESC, books.title ASC;
            """.format(
            match_strength=genre_required_match,
            list_id=list_id,
            user_id=user_id  # This is not strictly necessary, but helps protect against people being able to view other
            # people's list contents by guessing the list id.
        )
        )

        output_queue = data_structures.Queue()
        for i in res:
            first_name = i[4]
            surname = i[5]
            alias = i[6]
            if (alias is not None and
                    (first_name is not None and surname is not None)):
                author = f"{alias} ({first_name} {surname})"
            elif (alias is not None and
                  (first_name is None and surname is None)):
                author = alias
            else:
                author = f"{first_name} {surname}"

            synopsis = "</p><p>".join(("<p>" + i[3] + "</p>").split("\n"))
            # Change new lines to new paragraphs

            output_queue.push(
                {
                    "id": i[0],
                    "cover": i[1],
                    "title": i[2],
                    "synopsis": synopsis,
                    "author": author,
                    "author_id": i[7],
                    "date_added": i[8].strftime("%d-%m-%Y"),
                    "genres": i[9].split(",")[:num_display_genres],
                    "average_rating": i[10],
                    "num_reviews": i[11]
                }
            )

        list_name = connection.query("""
            SELECT list_name FROM reading_list_names
            WHERE list_id={};
        """.format(list_id))[0][0]  # See which list the button would move too.

        if list_name == "Currently Reading":
            button = "Mark as Read"
            move_target = connection.query("""
                SELECT list_id FROM reading_list_names
                WHERE list_name="Have Read"
                    AND user_id={};
            """.format(user_id))[0][0]
        elif list_name == "Want to Read":
            button = "Start Reading"
            move_target = connection.query("""
                SELECT list_id FROM reading_list_names
                WHERE list_name="Currently Reading"
                    AND user_id={};
            """.format(user_id))[0][0]
        else:
            button = None
            move_target = None

        return output_queue, button, move_target

    def remove_entry(user_id, list_id, book_id):
        connection.query("""
        DELETE FROM reading_lists
        WHERE user_id={user_id}
            AND book_id={book_id}
            AND list_id={list_id};
        """.format(
            book_id=book_id,
            user_id=user_id,
            list_id=list_id
        ))

    def add_entry(user_id, list_id, book_id):
        connection.query("""
            INSERT INTO reading_lists (user_id, book_id, list_id) VALUES 
            ({user_id}, {book_id}, {list_id});
        """.format(
            user_id=user_id,
            book_id=book_id,
            list_id=list_id
        ))

    def move_entry(user_id, start_list_id, end_list_id, book_id):
        reading_lists.add_entry(user_id, end_list_id, book_id)  # This changes the date added, but this is not an issue as
        reading_lists.remove_entry(user_id, start_list_id, book_id)
        # as once moved, it would be a new addition to the list, so the date should change.

    def remove_list(user_id, list_id):
        # Do not need to check whether the list is protected, the delete button is hidden by the JS. To delete it would
        # still require session id, so cannot be done accidentally.
        connection.query("""
            DELETE FROM reading_lists
            WHERE list_id={list_id}
                AND user_id={user_id};
        """.format(list_id=list_id, user_id=user_id))
        # Only the specific users list will be deleted, as it targets the single list
        # Delete the entries

        connection.query("""
            DELETE FROM reading_list_names
            WHERE list_id={list_id}
                AND user_id={user_id}
        """.format(list_id=list_id, user_id=user_id))
        # Delete the list name

    def create_list(user_id, list_name):
        connection.query("""
            INSERT INTO reading_list_names (user_id, list_name) VALUES
            ({user_id}, "{list_name}")
        """.format(user_id=user_id, list_name=list_name))


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
        except InvalidUserCredentialsError:
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
        except UserExistsError:
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

        except GenreNotFoundError:
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
    log = None # logger.Logging()
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
