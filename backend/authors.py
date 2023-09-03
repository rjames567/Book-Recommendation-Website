# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import configuration
import mysql_handler


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------
class AuthorNotFoundError(Exception):
    """
    Exception for when an author is not found.
    """

    def __init__(self, author_id):
        message = f"Author with ID '{author_id}' was not found."
        super().__init__(message)


# -----------------------------------------------------------------------------
# Objects
# -----------------------------------------------------------------------------
class Authors:
    def __init__(self, connection):
        self._connection = connection

    def follow(self, user_id, author_id):
        self._connection.query("""
            INSERT INTO author_followers (user_id, author_id)
            VALUES ({user_id}, {author_id});
        """.format(user_id=user_id, author_id=author_id))

    def unfollow(self, user_id, author_id):
        self._connection.query("""
            DELETE FROM author_followers
            WHERE user_id={user_id}
                AND author_id={author_id};
        """.format(user_id=user_id, author_id=author_id))

    def get_number_followers(self, author_id):
        return self._connection.query("""
        SELECT COUNT(author_id) FROM author_followers
            WHERE author_id={};
        """.format(author_id))[0][
            0]  # If the author ID is known, can safely assume that an author is in the DB with that
        # name.

    def get_about_data(self, author_id):
        res = self._connection.query("""
            SELECT first_name, surname, alias, about FROM authors
            WHERE author_id={};
        """.format(author_id))

        if len(res) == 0:
            raise AuthorNotFoundError(
                author_id)  # Cannot safely assume that it is from a reputable source - it may not be
            # from a link, so it should be verified.
        else:
            res = res[0]

        first_name, surname, alias, about = res  # res is a 4 element tuple, so this unpacks it
        author = names_to_display(first_name, surname, alias)
        output_dict = {
            "name": author,
            "about": "</p><p>".join(("<p>" + about + "</p>").split("\n")),
        }

        books = self._connection.query("""
            SELECT book_id, title, cover_image FROM books
            WHERE author_id={};
        """.format(author_id))

        book_arr = []
        for i in books:
            book_arr.append({
                "id": i[0],
                "title": i[1],
                "cover": i[2]
            })  # Author name can be done implicitly from other sent data - reduce amount of data sent for speed

        output_dict["books"] = book_arr

        return output_dict

    def id_to_name(self, author_id):
        res = self._connection.query("""
            SELECT first_name,
                surname,
                alias
            FROM authors
            WHERE author_id={}
        """.format(author_id))

        return names_to_display(res[0], res[1], res[2])


# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------
def names_to_display(first_name, surname, alias):
    if (alias is not None and
            (first_name is not None and surname is not None)):
        author = f"{alias} ({first_name} {surname})"
    elif (alias is not None and
            (first_name is None and surname is None)):
        author = alias
    else:
        author = f"{first_name} {surname}"
    return author


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

    authors = Authors(connection)