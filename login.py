# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import hashlib

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