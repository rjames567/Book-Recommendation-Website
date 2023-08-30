# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import configuration
import data_structures
import mysql_handler


# -----------------------------------------------------------------------------
# Recommendations
# -----------------------------------------------------------------------------
class Recommendations:
    def __init__(self, connection):
        self._connection = connection
        self._available_genres = len(self._connection.query("""
            SELECT genre_id FROM genres        
        """))  # This is computed here as it is needed frequently.
        self._floating_error_threshold = 1E-15
        self._recommendation_number = 15  # Constant to specify number of
        # recommendations to generate each time

    def gen_book_vector(self, book_id=None, book_genres=None):
        if book_id is not None:
            book_genres = self._connection.query("""
                SELECT genre_id,
                    match_strength
                FROM book_genres
                WHERE book_id={}
            """.format(book_id))
        vector = data_structures.Vector(
            dimensions=self._available_genres,
            default_value=0
        )

        for i in book_genres:
            vector[i[0] - 1] = i[1]  # First index is 0 as there is only 1 
            # column - It is subtracted as MySQL IDs start at 1. Second index
            # is the book id. The value is the match strength.

        return vector

    def gen_user_vector(self, user_id):
        vector = data_structures.Vector(dimensions=self._available_genres)

        user_genres = self._connection.query("""
            SELECT genre_id,
                match_strength
            FROM user_genres
            WHERE user_id={}
        """.format(user_id))  # Avoiding storing all data for genres unless
        # needed does reduce generation speed, but reduces required storage,
        # and given that the speed is not essential, this is acceptable.

        vector = data_structures.Vector(
            dimensions=self._available_genres,
            default_value=0
        )

        for i in user_genres:
            vector[i[0] - 1] = i[1]  # First index is 0 as there is only 1 
            # column - It is subtracted as MySQL IDs start at 1. Second index
            # is the book id. The value is the match strength.

        return vector

    def update_user_data_add_review(self, user_id, book_id, rating):
        user_vector = self.gen_user_vector(user_id)

        num_reviews = self._connection.query("""
            SELECT COUNT(review_id)
            FROM reviews
            WHERE user_id={}
        """.format(user_id))[0][0]  # This will always give a result, select
        # only tuple, and its only value from the result.

        user_vector *= num_reviews - 1  # This must be called after adding the
        # review to the database - undoes the division, so it can be 
        # manipulated to change the values.

        book_vector = self.gen_book_vector(book_id)

        user_vector += book_vector * (rating / 5)

        user_vector /= num_reviews

        res_vector = self.remove_rounding_errors(user_vector)

        self.save_user_preference_vector(user_id, res_vector)
        return res_vector

    def update_user_data_remove_review(self, user_id, book_id, rating):
        user_vector = self.gen_user_vector(user_id)

        num_reviews = self._connection.query("""
            SELECT COUNT(review_id)
            FROM reviews
            WHERE user_id={}
        """.format(user_id))[0][0]  # This will always give a result, select
        # only tuple, and its only value from the result.

        user_vector *= num_reviews + 1  # This must be called after removing the
        # review to the database - undoes the division, so it can be 
        # manipulated to change the values.

        book_vector = self.gen_book_vector(book_id)

        user_vector -= book_vector * (rating / 5)

        user_vector /= num_reviews

        res_vector = self.remove_rounding_errors(user_vector)

        self.save_user_preference_vector(user_id, res_vector)
        return res_vector


    def remove_rounding_errors(self, vector):
        # Storage space is limited so 0s are not stored, but due to float errors, these can become small <1E-19, so are
        # removed to reduce storage needs
        for count, val in enumerate(vector):
            if val < self._floating_error_threshold:
                vector[count] = 0
        return vector

    def save_user_preference_vector(self, user_id, vector):
        self._connection.query("""
            DELETE FROM user_genres
            WHERE user_id={}
        """.format(user_id))
        values = ""
        for genre, match in enumerate(vector):
            if match == 0:
                continue  # Prevents matches with strength 0 being inserted - skips to next iteration
            if genre != 0:
                values += ","
            values += f"({user_id}, {genre + 1}, {match})"  # Genre id is incremented, as MySQL indexes from 1, python
            # from 0

        self._connection.query("INSERT INTO user_genres (user_id, genre_id, match_strength) VALUES " + values)

    def gen_all_user_data(self):
        # This is for initial setup only. Updating user data when it is needed is faster.
        users = self._connection.query("""
            SELECT user_id FROM users
        """)

        for user in users:
            user = user[0]  # The query gives an array of single element tuples – gets the integer value.
            items = self._connection.query("""
                SELECT (SELECT GROUP_CONCAT(book_genres.match_strength) as match_strengths
                        FROM book_genres
                        WHERE book_genres.book_id=reviews.book_id
                        ORDER BY book_genres.genre_id ASC) as genres,
                    (SELECT GROUP_CONCAT(book_genres.genre_id) as genre_ids
                        FROM book_genres
                        WHERE book_genres.book_id=reviews.book_id
                        ORDER BY book_genres.genre_id ASC) as genres,
                    reviews.overall_rating
                FROM book_genres
                INNER JOIN reviews ON book_genres.book_id=reviews.book_id
                WHERE user_id={}
                GROUP BY reviews.book_id;
            """.format(user))

            ratings = [i[2] / 5 for i in items]
            book_vectors = []
            for item in items:
                arr = [(int(genre), float(match)) for genre, match in zip(item[1].split(","), item[0].split(","))]
                book_vectors.append(self.gen_book_vector(book_genres=arr))

            user_vector = sum((vector * rating for vector, rating in zip(book_vectors, ratings)), data_structures.Vector(dimensions=self._available_genres, default_value=0)) / len(items)
            self.save_user_preference_vector(user, user_vector)

    def recommend_user_books(self, user_id):
        user_preferences = self.gen_user_vector(user_id)
        weightings = []
        for i in self._connection.query("SELECT book_id FROM books"):
            book = i[0]
            data = self.gen_book_vector(book_id=book)
            weightings.append({
                "id": book,
                "dot_product": user_preferences.dot_product(data)
            })

        return [i["id"] for i in sorted(weightings, key=lambda x: x["dot_product"], reverse=True)][:self._recommendation_number]


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

    recommendations = Recommendations(connection)  # Only runs if this file is
    # run directly so as a scheduled task to generate new recommendations, and
    # the connection will be closed at the end of the program execution so
    # shouldn't cause issues.
