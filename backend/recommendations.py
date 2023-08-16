# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import configuration
import ml_utilities
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
    
    def gen_book_matrix(self, book_id):
        book_genres = self._connection.query("""
            SELECT genre_id,
                match_strength
            FROM book_genres
            WHERE book_id={}
        """.format(book_id))

        print(book_genres)

        print(self._available_genres)

        matrix = ml_utilities.Matrix(n=1, m=self._available_genres)

        for i in range(self._available_genres):
            matrix[i][0] = 0  # Set all genres to having match strenth of 0.

        # matrix.print()

        for i in book_genres:
            matrix[i[0] - 1][0] = i[1]  # First index is 0 as there is only 1 
            # column - It is subtracted as MySQL IDs start at 1. Second index
            # is the book id. The value is the match strength.
        
        return matrix


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

    recommendations = Recommendations(connection)