# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
import configuration
import mysql_handler

# ------------------------------------------------------------------------------
# Instantiating import classes
# ------------------------------------------------------------------------------
config = configuration.Configuration("./project_config.conf")
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


def unfollow_author(user_id, author_id):
    connection.query("""
        DELETE FROM author_followers
        WHERE user_id={user_id}
            AND author_id={author_id};
    """.format(user_id=user_id, author_id=author_id))


# ------------------------------------------------------------------------------
# Author Statistics
# ------------------------------------------------------------------------------
def get_number_followers(author_id):
    return connection.query("""
    SELECT COUNT(author_id) FROM author_followers
        WHERE author_id={};
    """.format(author_id))[0][0]  # If the author ID is known, can safely assume that an author is in the DB with that
    # name.
