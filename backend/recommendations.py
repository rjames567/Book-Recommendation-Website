# -----------------------------------------------------------------------------
# Standard Python library imports
# -----------------------------------------------------------------------------
import math

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import accounts
import authors
import configuration
import data_structures
import mysql_handler


# -----------------------------------------------------------------------------
# Recommendations
# -----------------------------------------------------------------------------
class Recommendations:
    def __init__(self, connection, genre_match_threshold, num_display_genres, authors):
        self._authors = authors
        self._connection = connection
        self._num_display_genres = num_display_genres
        self._genre_match_threshold = genre_match_threshold
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

    def update_user_data_increment(self, user_id, book_id, rating, significant=False):
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

        user_vector += book_vector * self.calc_scale_factor(rating)
        # Significant increase is not required so is left out

        user_vector /= num_reviews

        res_vector = self.remove_rounding_errors(user_vector)

        self.save_user_preference_vector(user_id, res_vector)
        return res_vector

    def calc_scale_factor(self, rating):
        # https://www.desmos.com/calculator/1rloljemzz
        x = rating - 3
        return ((1/100) * x**3) - ((1/40) * x ** 2) + ((1/3) * x)
    
        # Almost linear between 2 and 4.
        # 3 is neurtral and has no effect
        # 1 has a more significant impact than 5

    def update_user_data_decrement(self, user_id, book_id, rating, delete_recommendation=False):
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
        
        if delete_recommendation:
            scale_factor = math.log(self.calc_scale_factor(rating + 3))
            # Math/log is ln not log. Rating+3 undoes the subtraction in calc_scale_factor
            # Increases the impact of the change, for when a user has deleted a recommendation.
        else:
            scale_factor = self.calc_scale_factor(rating)
        user_vector -= book_vector * scale_factor

        user_vector /= num_reviews

        res_vector = self.remove_rounding_errors(user_vector)  # This will prevent negative values

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

            if len(items) > 0:
                user_vector = sum((vector * rating for vector, rating in zip(book_vectors, ratings)), data_structures.Vector(dimensions=self._available_genres, default_value=0)) / len(items)
                 # If the user has left no reviews, this would break, but this is fine as it will not run if the length of the items is 0 (ie no reviews)
                self.save_user_preference_vector(user, user_vector)

    def recommend_user_books(self, user_id):
        self._connection.query("""
            DELETE FROM recommendations
            WHERE user_id={}
                AND date_added<=DATE_SUB(NOW(), INTERVAL 2 DAY)
        """.format(user_id))

        existing_recommendations = self._connection.query("SELECT book_id FROM recommendations WHERE user_id={}".format(user_id))
        existing_recommendations = {i[0] for i in existing_recommendations}  # Sets are faster for 'in' operations

        reading_list_items = self._connection.query("""
            SELECT reading_lists.book_id
            FROM reading_lists
            INNER JOIN reading_list_names ON reading_lists.list_id=reading_list_names.list_id
            WHERE reading_lists.user_id={}
        """.format(user_id))
        reading_list_items = {i[0] for i in reading_list_items}

        user_preferences = self.gen_user_vector(user_id)
        weightings = []
        for i in self._connection.query("SELECT book_id FROM books"):
            book = i[0]
            if (book not in existing_recommendations and  # Prevent duplicate recommendations, which is likely
                book not in reading_list_items):  # Prevent recommendation of items that are in any of the users lists.
                data = self.gen_book_vector(book_id=book)
                if abs(data) and abs(user_preferences):  # Prevent issues with calculating dot product with 0 values (ZeroDivisionError)
                    cos_sim = user_preferences.cosine_sim(data)
                else:
                    cos_sim = 0
                weightings.append({
                        "id": book,
                        "cos_sim": cos_sim
                    })

        new_recommendations = sorted(weightings, key=lambda x: x["cos_sim"], reverse=True)[:self._recommendation_number]
        # Note that this could raise an error, but should not do so, as the amount available books should be greater
        # than 3x the amount recommendations made, and they are removed every two days.

        values = ""
        for count, recommendation in enumerate(new_recommendations):
            if count != 0:
                values += ","
            values += f"({user_id}, {recommendation['id']}, {recommendation['cos_sim']})"

        # Cosine sim can be multiplied by 100, to give percentage match for the user.

        self._connection.query("INSERT INTO recommendations (user_id, book_id, certainty) VALUES " + values)
        # Certainty is to allow for it to be done by order on a query, as they may become out of order when the entries
        # are deleted after the specified period.

    def get_user_recommendations(self, user_id):
        items = self._connection.query("""
            SELECT recommendations.book_id,
                ROUND(recommendations.certainty * 100, 1) as certainty,
                recommendations.date_added,
                books.cover_image,
                books.synopsis,
                books.title,
                authors.first_name,
                authors.surname,
                authors.alias,
                authors.author_id,
                (SELECT GROUP_CONCAT(genres.name) FROM book_genres
                    INNER JOIN genres ON book_genres.genre_id=genres.genre_id
                    WHERE book_genres.book_id=recommendations.book_id
                    GROUP BY books.book_id) AS genres,
                (SELECT ROUND(CAST(IFNULL(AVG(reviews.overall_rating), 0) as FLOAT), 2)
                    FROM reviews
                    WHERE reviews.book_id=books.book_id) AS average_rating,
                (SELECT COUNT(reviews.overall_rating)
                    FROM reviews
                    WHERE reviews.book_id=books.book_id) AS num_ratings
            FROM recommendations
            INNER JOIN books ON recommendations.book_id=books.book_id
            INNER JOIN authors ON books.author_id=authors.author_id
            WHERE recommendations.user_id={}
            ORDER BY recommendations.certainty DESC;
        """.format(user_id))  # ORDER BY does not use calculated certainty for higher accuracy, and avoiding collisions
        # IFNULL prevents any null values - replace with 0s.

        output_dict = dict()
        for i, k in enumerate(items):
            author = authors.names_to_display(k[6], k[7], k[8])

            output_dict[i] = {
                "book_id": k[0],
                "certainty": k[1],
                "date_added": k[2].strftime("%d/%m/%Y"),
                "cover_image": k[3],
                "synopsis": "</p><p>".join(("<p>" + k[4] + "</p>").split("\n")),
                "title": k[5],
                "author_name": author,
                "author_id": k[9],
                "genres": k[10].split(",")[:self._num_display_genres],
                "average_rating": round(k[11], 2),
                "number_ratings": k[12]
            }

        return output_dict
    
    def remove_stored_recommendation(self, user_id, book_id):
        self._connection.query("""
            DELETE FROM recommendations
            WHERE user_id={user_id}
                AND book_id={book_id};
        """.format(user_id=user_id, book_id=book_id))
    
    def get_user_recommendation_summaries(self, user_id):
        res = self._connection.query("""
            SELECT books.book_id,
                books.title,
                books.cover_image,
                authors.first_name,
                authors.surname,
                authors.alias
            FROM recommendations
            INNER JOIN books ON recommendations.book_id=books.book_id
            INNER JOIN authors ON books.author_id=authors.author_id
            WHERE recommendations.user_id={}
            ORDER BY recommendations.certainty DESC;
        """.format(user_id))
        return [{
                "author": authors.names_to_display(i[3], i[4], i[5]),
                "title": i[1],
                "book_id": i[0],
                "cover": i[2],
            } for i in res]
    
    def gen_author_average_preferences(self):  # Quite slow - This takes around 1/2 a second
        author_ids = self._authors.get_author_id_list()

        author_vectors = [data_structures.Vector(dimensions=self._available_genres, default_value=0) for i in range(len(author_ids))]

        res = self._connection.query("""
            SELECT books.author_id,
                books.book_id
            FROM books
        """)

        for author_id, book_id in res:
            author_vectors[author_id - 1] += self.gen_book_vector(book_id)

        return author_vectors


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

    account = accounts.Accounts(
        connection,
        config.get("passwords hashing_algorithm"),
        config.get("passwords salt"),
        config.get("passwords number_hash_passes"),
        None  # Reading lists object is not used, so passing None is safe.
    )
    recommendations = Recommendations(
        connection,
        config.get("books genre_match_threshold"),
        config.get("home number_display_genres"),
        authors.Authors(connection)
    )  # Only runs if this file is
    # run directly so as a scheduled task to generate new recommendations, and
    # the connection will be closed at the end of the program execution so
    # shouldn't cause issues.

    for i in account.get_user_id_list():  # Recommend all users a new set of books. Included to be set up as a cron job.
        recommendations.recommend_user_books(i)