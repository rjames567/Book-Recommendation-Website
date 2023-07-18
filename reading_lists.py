# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
import configuration
import data_structures
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
# Instantiating import classes
# ------------------------------------------------------------------------------
_genre_required_match = config.get("books genre_match_threshold")

# ------------------------------------------------------------------------------
# List names
# ------------------------------------------------------------------------------
def get_names(user_id):
    res = connection.query(
        """
        SELECT list_name from reading_list_names
        WHERE user_id={};
        """.format(user_id)
    ) # List of single element tuples
    output_queue = data_structures.Queue()
    for i in res:
        output_queue.push(i[0]) # i is a single element tuple

    return output_queue

# ------------------------------------------------------------------------------
# List values
# ------------------------------------------------------------------------------
def get_values(name, user_id):
    res = connection.query(
        """
        SELECT books.cover_image,
        	books.title,
        	books.synopsis,
        	authors.first_name,
        	authors.surname,
        	authors.alias,
        	reading_lists.date_added,
        	reading_list_names.list_id,
        	(SELECT GROUP_CONCAT(genres.name)
                FROM book_genres
                inner join books on book_genres.book_id=books.book_id
                inner join genres on genres.genre_id=book_genres.genre_id
                WHERE book_genres.book_id=reading_lists.book_id
                    AND book_genres.match_strength>{match_strength}
                GROUP by books.title) as genres
        FROM reading_lists
        INNER JOIN books ON books.book_id=reading_lists.list_id
        INNER JOIN authors ON books.author_id=authors.author_id
        INNER JOIN reading_list_names ON reading_list_names.list_id=reading_lists.list_id
        WHERE reading_lists.user_id={user_id}
        	AND reading_list_names.list_name="{list_name}"
        ORDER BY reading_lists.date_added DESC, books.title ASC;
        """.format(
            match_strength=_genre_required_match,
            user_id=user_id,
            list_name=name
        )
    )