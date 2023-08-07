# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
import configuration
import mysql_handler

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
# Follow Author
# ------------------------------------------------------------------------------
def follow_author(user_id, author_id):
    connection.query("""
        INSERT INTO author_followers (user_id, author_id)
        VALUES ({user_id}, {author_id});
    """.format(user_id=user_id, author_id=author_id))