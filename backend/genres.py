# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import authors
import configuration
import mysql_handler


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------
class GenreNotFoundError(Exception):
    """
    Exception for when a genre is not found.
    """

    def __init__(self, genre_name):
        message = f"Genre '{genre_name}' was not found"
        super().__init__(message)


# -----------------------------------------------------------------------------
# Objects
# -----------------------------------------------------------------------------
class Genres:
    def __init__(self, connection):
        self._connection = connection

    def get_about_data(self, genre_name):
        res = self._connection.query("""
            SELECT genre_id, name, about FROM genres
            WHERE name="{genre_name}";
        """.format(
            genre_name=genre_name))  # There will only be one entry with that name, so take only tuple from result
        # list

        if len(res) == 0:  # Protect against a list out of range errors
            raise GenreNotFoundError(genre_name)
        else:
            res = res[0]

        db_books = self._connection.query("""
            SELECT books.book_id, books.title, books.cover_image, authors.first_name, authors.surname, authors.alias FROM books
            INNER JOIN authors ON books.author_id=authors.author_id
            INNER JOIN book_genres ON books.book_id=book_genres.book_id
            INNER JOIN genres ON genres.genre_id=book_genres.genre_id
            WHERE genres.genre_id={genre_id};
        """.format(genre_id=res[0]))

        book_dict = dict()
        for i, k in enumerate(db_books):
            book_id, title, cover, first_name, surname, alias = k
            author = authors.names_to_display(first_name, surname, alias)

            book_dict[i] = {
                "id": book_id,
                "title": title,
                "author": author,
                "cover": cover
            }

        output_dict = {
            "name": res[1],
            "about": "</p><p>".join(("<p>" + res[2] + "</p>").split("\n")),
            # Split each paragraph into <p></p> elements
            "books": book_dict
        }

        return output_dict

# -----------------------------------------------------------------------------
# File execution
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    config = configuration.Configuration("./project_config.conf")
    connection = mysql_handler.Connection(
        user=config.get("mysql username"),
        password=config.get("mysql password"),
        schema=config.get("mysql schema"),
        host=config.get("mysql host")
    )

    genres = Genres(connection)