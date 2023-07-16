# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
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

        # Probability of getting duplicates is very low, and gets lower as the size
        # of the string increases. It would also need to be within 1 second, as
        # time.time() is added to the end which is the number of seconds since the
        # epoch.

        connection.query(
            """
            INSERT INTO sessions (client_id, user_id) VALUES ({token}, {user_id});
            """.format(token=token, user_id=user_id)
        )

        return token