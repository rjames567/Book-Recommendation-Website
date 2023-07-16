# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import datetime
import hashlib
import secrets
import time

# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
import mysql_handler
import configuration

# ------------------------------------------------------------------------------
# Instantiating import classes
# ------------------------------------------------------------------------------
config = configuration.Configuration("project_config.conf")
connection = mysql_handler.Connection(
    user=config.get("mysql username"),
    password=config.get("mysql password"),
    schema=config.get("mysql schema"),
    host=config.get("mysql host")
)

# ------------------------------------------------------------------------------
# Variables
# ------------------------------------------------------------------------------
_number_hash_passes = config.get("passwords number_hash_passes")
_hashing_salt = config.get("passwords salt") # Stored in the config as binary
_hashing_algorithm = config.get("passwords hashing_algorithm")
_token_size = config.get("session_id_length")

# ------------------------------------------------------------------------------
# Custom exceptions
# ------------------------------------------------------------------------------
class SessionExpiredError (Exception):
    """
    Exception for when a client is using a session that has expired, and is no
    longer valid
    """
    def __init__(self, session_id):
        message = f"Session id '{session_id}' has expired"
        super().__init__(message)

class UserExistsError (Exception):
    """
    Exception for when a user account already exists with a specific username,
    and it has been attempted to add a second.

    Usernames must be unique in the database.
    """
    def __init__(self, username):
        message = f"User already exists with the username {username}."
        super().__init__(message)

# ------------------------------------------------------------------------------
# Password hashing
# ------------------------------------------------------------------------------
def hash(password):
    """
    Method to hash the password, including a salt.

    password -> string
        The string that is to be hashed.

    Returns a string.
    """
    result = hashlib.pbkdf2_hmac(
        _hashing_algorithm,
        password.encode("utf-8"), # Needs to be in binary
        _hashing_salt, # Salt needs to be in binary - stored as binary in config
        _number_hash_passes # Recommended number of passes is 100,000
    )

    return result.hex() # Hash is returned as a hex string, so converts back

# ------------------------------------------------------------------------------
# Account Class
# ------------------------------------------------------------------------------
class account:
    def check_credentials(username, password):
        """
        Method to check whether given user credentials are stored in the
        database.

        username -> string
            The username that is to be checked

        password -> string
            The password that is to checked

        Returns a boolean value, True, if it is a valid username in the
        database, False if it is not.
        """
        entered_password = hash(password)
        query_result = connection.query(
            """
            SELECT password_hash FROM users
            WHERE username="{}";
            """.format(username)
        )

        return not((len(query_result) == 0)
            or (query_result[0][0] != entered_password))

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
                    password=hash(password) # Password must be hashed before
                        # storing in the database.
                )
            )

            user_id = connection.query(
                """
                SELECT user_id FROM users
                WHERE username="{}"
                """.format(username)
            )[0][0]

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

# ------------------------------------------------------------------------------
# Session Class
# ------------------------------------------------------------------------------
class session:
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
        token = secrets.token_bytes(_token_size).hex() + str(time.time())
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
            The session id for which the creation time needs to be ipdated for

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
            raise SessionExpiredError(session_id) # If there is no entries
                # it must have been deleted by a maintenance script, as it had
                # expired.
        else:
            res = res[0] # Gets first element result from list - should only be
                # one result
        expiry_datetime = res[1] + datetime.timedelta(days=1)
            # Set expiry date to one day after it has been last used

        if datetime.datetime.now() > expiry_datetime:
            session.close(session_id)
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