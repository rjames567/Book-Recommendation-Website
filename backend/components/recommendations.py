# -----------------------------------------------------------------------------
# Standard Python library imports
# -----------------------------------------------------------------------------
import math
import random
import datetime
import numpy as np
import matplotlib.pyplot as plt
import sklearn.metrics

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import os
import sys
import authors

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import configuration
import mysql_handler

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
class NoUserPreferencesError(Exception):
    def __init__(self, user_id):
        message = f"User with id {user_id}, has no preferences"
        super().__init__(message)

# -----------------------------------------------------------------------------
# Recommendations
# -----------------------------------------------------------------------------
class Recommendations:
    def __init__(self, connection, num_converge_iters, hyperparam, number_display_genres, debug=False):
        self._connection = connection
        self._num_converge_iters = num_converge_iters
        self._hyperparam = hyperparam
        self._num_factors = len(self._connection.query("SELECT * FROM genres"))
        self.debug = debug
        self._num_users = len(self._connection.query("SELECT user_id FROM users"))
        self._num_books = len(self._connection.query("SELECT book_id FROM books"))
        self._number_recommendations = 10
        self._num_display_genres = number_display_genres
        self.test_mse_record = []
        self.train_mse_record = []

        self.gen_lookup_tables()

    def fit(self):
        train, test, = self.create_train_test()

        self._num_users, self._num_books = train.shape

        self.book_factors = np.random.random((self._num_books, self._num_factors))
        self.user_factors = np.random.random((self._num_users, self._num_factors))

        if self.debug:  # Debug is about 10 times slower
            self.test_mse_record = []
            self.train_mse_record = []

            for i in range(self._num_converge_iters):
                print(f"Iteration {i + 1} of {self._num_converge_iters}")
                self.user_factors = self.wals_step(train, self.book_factors)
                self.item_factors = self.wals_step(train.T, self.user_factors)

                predict = self.predict()

                self.train_mse_record.append(self.mean_squared_error(train, predict))
                self.test_mse_record.append(self.mean_squared_error(test, predict))

            return self.test_mse_record, self.train_mse_record

        else:
            for i in range(self._num_converge_iters):
                print(f"Iteration {i + 1} of {self._num_converge_iters} Start")   # This is here for development. TODO remove this
                self.user_factors = self.wals_step(train, self.book_factors)
                self.item_factors = self.wals_step(train.T, self.user_factors)
                print(f"Iteration {i + 1} of {self._num_converge_iters} End")

            self.save_book_genres()  # Not included in the debug option, as it increases time cost,
            # and would likely be rerun a lot to find optimum parameters, so is unnecessary.

    def save_book_genres(self):
        query = "INSERT INTO book_genres (book_id, genre_id, match_strength) VALUES "
        for count, facts in enumerate(self.book_factors):
            # i will be the rating for each the genres.
            book_id = self.book_lookup_table[count]
            query += ",".join(
                f"({book_id}, {self.genre_lookup_table[i]}, {strength})" for i, strength in enumerate(facts)) + ","

        self._connection.query("DELETE FROM book_genres")  # Done here to minimise time without data in DB
        self._connection.query(query[:-1])

    def predict(self):
        return self.user_factors.dot(self.item_factors.T)

    def gen_review_matrix(self):
        # x = np.array([[0.0 for i in range(num_books)] for k in range(num_users)])
        mat = np.zeros((self._num_users, self._num_books))
        for user in self.user_lookup_table:
            user_id = self.user_lookup_table[user]
            reviews = self._connection.query("""
                SELECT book_id,
                    (overall_rating + IFNULL(character_rating, overall_rating) + IFNULL(plot_rating, overall_rating)) / 3
                FROM reviews
                WHERE user_id={}
                GROUP BY review_id;
            """.format(user_id))

            for book_id, rating in reviews:
                used_book_id = list(self.book_lookup_table.values()).index(book_id)  # This finds the key for the value stored in the lookup table.
                # geeksforgeeks.org/python-get-key-from-value-in-dictionary
                mat[user][used_book_id] = float(rating)
        return mat

        # TODO include users initial preferences
        # TODO include presence of books in reading lists
        # TODO include users following authors
        # TODO include bad recommendations

    def create_train_test(self, ratings=None):
        if ratings is None:
            self.ratings = self.gen_review_matrix()
        else:
            self.ratings = ratings

        train = self.ratings.copy()

        while self.ratings.tolist() == train.tolist():
            train = self.ratings.copy()
            for user in range(self._num_users):
                nonzero = self.ratings[user].nonzero()[0]
                indexes = np.random.choice(
                    nonzero,
                    size=round(len(nonzero) * 0.2),
                    replace=True
                )

                for i in indexes:
                    train[user, i] = 0.0

        return train, self.ratings

    def wals_step(self, ratings, fixed):
        A = fixed.T.dot(fixed) + np.eye(self._num_factors) * self._hyperparam
        B = ratings.dot(fixed)
        A_inv = np.linalg.inv(A)
        return B.dot(A_inv)

    def gen_lookup_tables(self):
        self.user_lookup_table = dict()
        users = self._connection.query("SELECT user_id FROM users")
        for count, i in enumerate(users):
            self.user_lookup_table[count] = i[0]

        self.book_lookup_table = dict()
        books = self._connection.query("SELECT book_id FROM books")
        for count, i in enumerate(books):
            self.book_lookup_table[count] = i[0]

        self.genre_lookup_table = dict()
        genres = self._connection.query("SELECT genre_id FROM genres")
        for count, i in enumerate(genres):
            self.genre_lookup_table[count] = i[0]

    def gen_recommendations(self):
        predictions = self.predict()

        query = "INSERT INTO recommendations (user_id, book_id, certainty) VALUES "

        for user, books in enumerate(predictions):
            user_books = []
            user_id = self.user_lookup_table[user]

            avoid_recs = {
                i[0] for i in self._connection.query("""
                        SELECT book_id
                        FROM recommendations
                        WHERE user_id={}
                            AND date_added<=DATE_SUB(NOW(), INTERVAL 2 DAY)
                    """.format(user_id))
            }  # sets are faster for "is val in list" operations

            for i in self.get_bad_recommendations(user_id):
                avoid_recs.add(i)

            for book, rating in enumerate(books):
                book_id = self.book_lookup_table[book]
                if book_id not in avoid_recs:
                    user_books.append({
                        "id": book_id,
                        "dot_product": rating
                    })

            user_books.sort(key=lambda x: x["dot_product"], reverse=True)
            user_books = user_books[:self._number_recommendations]

            for count, i in enumerate(user_books):  # Done after as this is faily expensive, to avoid unecessary calculations
                user_books[count]["certainty"] = self.calculate_certainty(
                    i["id"],
                    user_id,
                    i["dot_product"]
                )

            query += ",".join(
                f"({user_id}, {i['id']}, {i['certainty']})" for i in user_books[:self._number_recommendations]) + ","

        self._connection.query("""
            DELETE FROM test_recommendations
            WHERE date_added<=DATE_SUB(NOW(), INTERVAL 2 DAY)
        """)
        self._connection.query(query[:-1])

        # TODO books in reading lists

    def delete_recommendation(self, user_id, book_id):
        # This includes marking a recommendation as bad - it is implicitly the same thing
        self._connection.query("""
            DELETE FROM recommendations
            WHERE user_id={user_id}
                AND book_id={book_id}
        """.format(
            user_id=user_id,
            book_id=book_id
        ))

        self._connection.query(
            "INSERT INTO bad_recommendations (user_id, book_id) VALUES ({user_id}, {book_id})".format(
                user_id=user_id,
                book_id=book_id
            )
        )

    def get_bad_recommendations(self, user_id):
        bad_recommendations = self._connection.query("""
            SELECT recommendation_id,
                book_id,
                date_added
            FROM bad_recommendations
            WHERE user_id={}
        """.format(user_id))

        return_vals = []
        remove = []
        for rec_id, book, date in bad_recommendations:
            if date + datetime.timedelta(weeks=10) > datetime.datetime.now():
                # 10 week expiry, so it can start recommending books if the user's preferences have changed. 10 weeks is
                # a long enough time for it to be plausible to be a good recommendation
                return_vals.append(book)
            else:
                remove.append(rec_id)

        self._connection.query(
            "DELETE FROM bad_recommendations WHERE recommendation_id IN ({})".format(",".join(str(i) for i in remove)))
        # Delete expired recommendations.

        return return_vals

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
        """.format(
            user_id))  # ORDER BY does not use calculated certainty for higher accuracy, and avoiding collisions
        # IFNULL prevents any null values - replace with 0s.

        if len(items) == 0:
            raise NoUserPreferencesError(user_id)

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

    def calculate_certainty(self, book_id, user_id, dot_product):
        book_id = list(self.book_lookup_table.values()).index(book_id)
        book_vec = [i for i in self.book_factors[book_id]]
        user_id = list(self.user_lookup_table.values()).index(user_id)
        user_vec = [i for i in self.user_factors[user_id]]

        abs_book_vec = math.sqrt(sum(i ** 2 for i in book_vec))
        abs_user_vec = math.sqrt(sum(i ** 2 for i in user_vec))

        similarity = dot_product / (abs_book_vec * abs_user_vec)
        if similarity > 1:  # Slim chance it ends up larger than 100%, so limits it artificially.
            similarity = 1
        return similarity

    def add_user(self, user_id, author_ids):
        vals = [f"({user_id}, {author_id})" for author_id in author_ids]
        self._connection.query(
            "INSERT INTO initial_preferences (user_id, author_id) VALUES {}".format(
                ",".join(vals)
            )
        )

        res = self._connection.query("""
                SELECT AVG(book_genres.match_strength),
                    book_genres.genre_id
                FROM book_genres
                INNER JOIN books
                    ON book_genres.book_id=books.book_id
                INNER JOIN authors
                    ON books.author_id=authors.author_id
                WHERE authors.author_id IN ({})
                GROUP BY book_genres.genre_id;
            """.format(
                ",".join(str(i) for i in author_ids)
            )
        )

        target_vec = np.zeros(self._num_factors)

        for avg, genre_id in res:
            genre = list(self.genre_lookup_table.values()).index(genre_id)
            target_vec[genre] = avg

        rec = target_vec * self.book_factors

        output = []
        for count, val in enumerate(rec[0]):
            output.append({
                "book_id": self.book_lookup_table[count],
                "strength": val
            })

        output.sort(key=lambda x: x["strength"], reverse=True)

        output = output[:self._number_recommendations]

        for count, i in enumerate(output):
            output[count]["certainty"] = self.calculate_certainty(
                i["book_id"],
                user_id,
                i["strength"]
            )

        self._connection.query("INSERT INTO recommendations (user_id, book_id, certainty) VALUES {}".format(",".join(f"({user_id}, {i['book_id']}, {i['certainty']})" for i in output)))

        return output

    @staticmethod
    def mean_squared_error(true, pred):
        mask = np.nonzero(true)
        mse = sklearn.metrics.mean_squared_error(true[mask], pred[mask])
        return mse


# -----------------------------------------------------------------------------
# Plotting functions
# -----------------------------------------------------------------------------
def plot_learning_curve(model):
    """visualize the training/testing loss"""
    linewidth = 3
    plt.plot(model.test_mse_record, label='Test', linewidth=linewidth)
    plt.plot(model.train_mse_record, label='Train', linewidth=linewidth)
    plt.xlabel('iterations')
    plt.ylabel('MSE')
    plt.legend(loc='best')
    plt.show()


# -----------------------------------------------------------------------------
# Project constants
# -----------------------------------------------------------------------------
config = configuration.Configuration("./project_config.conf")
debugging = config.get("debugging")  # Toggle whether logs are shown
number_hash_passes = config.get("passwords number_hash_passes")
hashing_salt = config.get("passwords salt")  # Stored in the config as binary
hashing_algorithm = config.get("passwords hashing_algorithm")
token_size = config.get("session_id_length")
genre_required_match = config.get("books genre_match_threshold")
number_summaries_home = config.get("home number_home_summaries")
number_similarities_about = config.get("home number_about_similarities")
num_display_genres = config.get("home number_display_genres")
num_search_results = config.get("search number_results")

# -----------------------------------------------------------------------------
# Database connection
# -----------------------------------------------------------------------------
connection = mysql_handler.Connection(
    user=config.get("mysql username"),
    password=config.get("mysql password"),
    schema=config.get("mysql schema"),
    host=config.get("mysql host")
)

if __name__ == "__main__":
    connection.query("DELETE FROM recommendations")
    rec = Recommendations(connection, 100, 0.1, 5)
    # rec.fit()
    # rec.gen_recommendations()
    print(rec.gen_review_matrix().tolist())