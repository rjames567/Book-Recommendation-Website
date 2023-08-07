# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
import mysql_handler
import configuration

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
# Exceptions
# ------------------------------------------------------------------------------
class GenreNotFoundError(Exception):
    """
    Exception for when a genre is not found.
    """
    def __init__(self, genre_name):
        message = f"Genre '{genre_name}' was not found"
        super().__init__(message)

# ------------------------------------------------------------------------------
# About data
# ------------------------------------------------------------------------------
def get_about_data(genre_name):
    res = connection.query("""
        SELECT genre_id, name, about FROM genres
        WHERE name="{genre_name}";
    """.format(genre_name=genre_name))  # There will only be one entry with that name, so take only tuple from result
    # list

    if len(res) == 0: # Protect against a list out of range errors
        raise GenreNotFoundError(genre_name)
    else:
        res = res[0]

    books = connection.query("""
        SELECT books.book_id, books.title, books.cover_image, authors.first_name, authors.surname, authors.alias FROM books
        INNER JOIN authors ON books.author_id=authors.author_id
        INNER JOIN book_genres ON books.book_id=book_genres.book_id
        INNER JOIN genres ON genres.genre_id=book_genres.genre_id
        WHERE genres.genre_id={genre_id};
    """.format(genre_id=res[0]))

    book_dict = dict()
    for i, k in enumerate(books):
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
        "about": "</p><p>".join(("<p>" + res[2] + "</p>").split("\n")), # Split each paragraph into <p></p> elements
        "books": book_dict
    }

    return output_dict