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
    def __init__(self, connection, required_genre_match, number_summaries_home):
        self._number_summaries_home = number_summaries_home
        self._required_genre_match = required_genre_match
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
            SELECT authors.first_name,
            authors.surname,
            authors.alias,
            authors.about,
            (SELECT count(author_followers.user_id) FROM author_followers
                WHERE author_followers.author_id=authors.author_id) AS followers 
            FROM authors
            WHERE authors.author_id={};
        """.format(author_id))

        if len(res) == 0:
            raise AuthorNotFoundError(
                author_id)  # Cannot safely assume that it is from a reputable source - it may not be
            # from a link, so it should be verified.
        else:
            res = res[0]

        first_name, surname, alias, about, followers = res  # res is a 4 element tuple, so this unpacks it
        author = names_to_display(first_name, surname, alias)
        output_dict = {
            "name": author,
            "about": "</p><p>".join(("<p>" + about + "</p>").split("\n")),
            "author_id": int(author_id),
            "num_followers": followers
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

        genres = self._connection.query("""
            SELECT genres.name
            FROM genres
            INNER JOIN book_genres ON book_genres.genre_id=genres.genre_id
            INNER JOIN books ON books.book_id=book_genres.book_id
            INNER JOIN authors ON authors.author_id=books.author_id
            WHERE authors.author_id={author_id}
                AND book_genres.match_strength>{match_strength}
        """.format(author_id=author_id, match_strength=self._required_genre_match))

        output_dict["genres"] = [i[0] for i in genres]

        avg_rating = self._connection.query("""
            SELECT ROUND(AVG(reviews.overall_rating), 2) AS average,
                   COUNT(reviews.overall_rating) AS number
            FROM reviews
            INNER JOIN books ON books.book_id=reviews.book_id
            INNER JOIN authors ON authors.author_id=books.author_id
            WHERE authors.author_id={}
        """.format(author_id))[0]  # Get first (only) tuple from result

        output_dict["average_rating"] = float(avg_rating[0])
        output_dict["num_ratings"] = avg_rating[1]

        return output_dict

    def id_to_name(self, author_id):
        res = self._connection.query("""
            SELECT first_name,
                surname,
                alias
            FROM authors
            WHERE author_id={}
        """.format(author_id))[0]

        return names_to_display(res[0], res[1], res[2])

    def get_author_id_list(self, names=False):
        if names:
            res = self._connection.query("""
                SELECT author_id,
                    first_name,
                    surname,
                    alias
                FROM authors
            """)
            output = []
            for count, item in enumerate(res):
                output.append({
                    "name": names_to_display(item[1], item[2], item[3]),
                    "id": item[0]
                })
            return output
        return [i[0] for i in self._connection.query("SELECT author_id FROM authors")]

    def get_author_favourite_data(self, user_id):
        res = self._connection.query("""
            SELECT books.title,
                books.book_id,
                books.cover_image,
                authors.first_name,
                authors.surname,
                authors.alias,
                AVG(reviews.overall_rating) AS average_rating
            FROM books
            INNER JOIN authors ON books.author_id=authors.author_id
            LEFT OUTER JOIN reviews ON reviews.book_id=books.book_id
            WHERE books.author_id IN (SELECT author_followers.author_id
                FROM author_followers
                WHERE author_followers.user_id={})
            GROUP BY books.book_id
            ORDER BY average_rating DESC;        
        """.format(user_id))[:self._number_summaries_home]

        if len(res) == 0:
            return None
        
        output_dict = dict()
        for i, k in enumerate(res):
            output_dict[i] = {
                "author": names_to_display(k[3], k[4], k[5]),
                "title": k[0],
                "book_id": k[1],
                "cover": k[2],
            }
        
        return output_dict


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