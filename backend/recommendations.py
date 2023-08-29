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
    
    def gen_book_vector(self, book_id):
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

        user_vector *= num_reviews - 1 # This must be called after adding the
        # review to the database - undoes the division, so it can be 
        # manipulated to change the values.

        book_vector = self.gen_book_vector(book_id)

        user_vector += book_vector * (rating/5)

        user_vector /= num_reviews

        return user_vector


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
