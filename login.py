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
        query_result = connection.query(
            """
            SELECT username FROM users
            WHERE username="{}"
            """.format(username)
        )
        if len(query_result):
            return False
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
            return True

    def get_user_id(username):
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
    def create(user_id):
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
        connection.query(
            """
            UPDATE sessions
            SET
                date_added=NOW()
            WHERE client_id="{}";
            """.format(session_id)
        )

    def get_user_id(session_id):
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
            raise SessionExpiredError(session_id)
        else:
            return res[0]

        # Does not update the session time - Excluded from this as any request
        # from the client indicates that is still active, regardless of whether
        # the user id is needed to carry out the required process.

    def close(session_id):
        connection.query(
            """
            DELETE FROM sessions
            WHERE client_id="{}";
            """.format(session_id)
        )