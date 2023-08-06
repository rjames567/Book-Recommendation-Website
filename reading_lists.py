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
# Exceptions
# ------------------------------------------------------------------------------
class ProtectedListDeletionError(Exception):
    """
    Exception for when a reading list is tried to be deleted, which is protected, and should not be deleted.
    """

    def __init__(self, list_name):
        message = f"'{list_name}' list is protected and cannot be deleted."
        super().__init__(message)


# ------------------------------------------------------------------------------
# List names
# ------------------------------------------------------------------------------
def get_names(user_id):
    res = connection.query(
        """
        SELECT list_name from reading_list_names
        WHERE user_id={};
        """.format(user_id)
    )  # List of single element tuples
    output_queue = data_structures.Queue()
    for i in res:
        output_queue.push(i[0])  # i is a single element tuple

    return output_queue


# ------------------------------------------------------------------------------
# List values
# ------------------------------------------------------------------------------
def get_values(name, user_id):
    res = connection.query(
        """
        SELECT books.book_id,
            books.cover_image,
            books.title,
            books.synopsis,
            authors.first_name,
            authors.surname,
            authors.alias,
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
            WHERE reading_lists.user_id={user_id}
            AND reading_list_names.list_name="{list_name}"
            ORDER BY reading_lists.date_added DESC, books.title ASC;
        """.format(
            match_strength=_genre_required_match,
            user_id=user_id,
            list_name=name
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
                "date_added": i[7].strftime("%d/%m/%Y"),
                "genres": i[8].split(","),
                "average_rating": i[9],
                "num_reviews": i[10],
            }
        )

    return output_queue


def remove_entry(user_id, list_name, book_title):
    list_id = connection.query("""
    SELECT list_id FROM reading_list_names
    WHERE user_id={user_id}
        AND list_name="{list_name}";
    """.format(
        user_id=user_id,
        list_name=list_name
    ))[0][0]  # Will only be one iteem, so first element of only tuple is selected.

    book_id = connection.query("""
    SELECT book_id FROM books
    WHERE title="{book_title}";
    """.format(book_title=book_title))[0][0]

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


def add_entry(user_id, list_name, book_title):
    book_id = connection.query("""
        SELECT book_id FROM books
        WHERE title="{book_title}";
        """.format(book_title=book_title))[0][0]

    list_id = connection.query("""
        SELECT list_id FROM reading_list_names
        WHERE user_id={user_id}
            AND list_name="{list_name}";
        """.format(
        user_id=user_id,
        list_name=list_name
    ))[0][0]

    connection.query("""
    INSERT INTO reading_lists (user_id, book_id, list_id) VALUES 
    ({user_id}, {book_id}, {list_id})
    """.format(
        user_id=user_id,
        book_id=book_id,
        list_id=list_id
    ))


def move_entry(user_id, start_list_name, end_list_name, book_title):
    remove_entry(user_id, start_list_name, book_title)
    add_entry(user_id, end_list_name, book_title)  # This changes the date added, but this is not an issue as
    # as once moved, it would be a new addition to the list, so the date should change.


# ------------------------------------------------------------------------------
# List management
# ------------------------------------------------------------------------------
def remove_list(user_id, list_name):
    if list_name in ["Currently Reading", "Want to Read", "Have Read"]:
        raise ProtectedListDeletionError(list_name)

    list_name_id = connection.query("""
        SELECT list_id FROM reading_list_names
        WHERE user_id={user_id}
            AND list_name="{list_name}";
    """.format(
        user_id=user_id,
        list_name=list_name
    ))[0][0]

    connection.query("""
        DELETE FROM reading_lists
        WHERE list_id={};
    """.format(list_name_id))
    # Only the specific users list will be deleted, as it targets the single list
    # Delete the entries

    connection.query("""
        DELETE FROM reading_list_names
        WHERE list_id={}
    """.format(list_name_id))
    # Delete the list name


def create_list(user_id, list_name):
    connection.query("""
        INSERT INTO reading_list_names (user_id, list_name) VALUES
        ({user_id}, "{list_name}")
    """.format(user_id=user_id, list_name=list_name))