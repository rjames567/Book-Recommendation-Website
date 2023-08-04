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
# Exceptions
# ------------------------------------------------------------------------------
class BookNotFoundError(Exception):
    """
    Exception for when a genre is not found.
    """
    def __init__(self, book_title):
        message = f"Book '{book_title}' was not found"
        super().__init__(message)


# ------------------------------------------------------------------------------
# About data
# ------------------------------------------------------------------------------
def get_about_data(book_title, user_id):
    res = connection.query("""
    SELECT books.book_id,
        books.title,
        books.cover_image,
        books.synopsis,
        books.purchase_link,
        books.release_date,
        books.isbn,
        authors.first_name,
        authors.surname,
        authors.alias,
        authors.about,
        (SELECT COUNT(author_followers.author_id) FROM author_followers
                WHERE author_followers.author_id=books.author_id) as author_num_followers
    FROM books
    INNER JOIN authors ON authors.author_id=books.book_id
    WHERE books.title="{book_title}";
    """.format(book_title=book_title))

    if len(res) == 0:
        raise BookNotFoundError(book_title)  # If the query result has 0 entries, no book was found with the target name

    book_id = res[0]  # Avoids joins for subsequent queries
    first_name = res[7]
    surname = res[8]
    alias = res[9]
    if (alias is not None and
            (first_name is not None and surname is not None)):
        author = f"{alias} ({first_name} {surname})"
    elif (alias is not None and
          (first_name is None and surname is None)):
        author = alias
    else:
        author = f"{first_name} {surname}"

    output_dict = {
        "title": res[1],
        "cover_image": res[2],
        "synopsis": res[3],
        "purchase_link": res[4],
        "release_date": res[5],
        "isbn": res[6],
        "author": author
    }

    return output_dict