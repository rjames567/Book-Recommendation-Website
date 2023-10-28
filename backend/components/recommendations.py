# -----------------------------------------------------------------------------
# Standard Python library imports
# -----------------------------------------------------------------------------
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
    def __init__(self, connection, num_converge_iters, hyperparam, debug=False):
        self._connection = connection
        self._num_converge_iters = num_converge_iters
        self._hyperparam = hyperparam
        self._num_factors = len(self._connection.query("SELECT * FROM test_genres"))
        self.debug = debug
        self._num_users = len(self._connection.query("SELECT user_id FROM test_users"))
        self._num_books = len(self._connection.query("SELECT book_id FROM test_books"))
        self._number_recommendations = 10

        self.gen_lookup_tables()

    def fit(self):
        train, test, = self.create_train_test()

        self._num_users, self._num_books = train.shape

        self.book_factors = np.random.random((self._num_books, self._num_factors))
        self.user_factors = np.random.random((self._num_users, self._num_factors))

        if self.debug:  # Debug is about 10 times slower
            test_mse_record = []
            train_mse_record = []

            for i in range(self._num_converge_iters):
                print(f"Iteration {i + 1} of {self._num_converge_iters}")
                self.user_factors = self.wals_step(train, self.book_factors)
                self.item_factors = self.wals_step(train.T, self.user_factors)

                predict = self.predict()

                train_mse_record.append(self.mean_squared_error(train, predict))
                test_mse_record.append(self.mean_squared_error(test, predict))

            return test_mse_record, train_mse_record

        else:
            for i in range(self._num_converge_iters):
                self.user_factors = self.wals_step(train, self.book_factors)
                self.item_factors = self.wals_step(train.T, self.user_factors)

            self.save_book_genres()  # Not included in the debug option, as it increases time cost,
            # and would likely be rerun a lot to find optimum parameters, so is unnecessary.

    def save_book_genres(self):
        query = "INSERT INTO test_book_genres (book_id, genre_id, match_strength) VALUES "
        for count, facts in enumerate(self.book_factors):
            # i will be the rating for each the genres.
            book_id = self.book_lookup_table[count]
            query += ",".join(
                f"({book_id}, {self.genre_lookup_table[i]}, {strength})" for i, strength in enumerate(facts)) + ","

        self._connection.query("DELETE FROM test_book_genres")  # Done here to minimise time without data in DB
        self._connection.query(query[:-1])

    def predict(self):
        return self.user_factors.dot(self.item_factors.T)

    def gen_recommendation_matrix(self, percentage_books_rated_user=30):
        # x = np.array([[0.0 for i in range(num_books)] for k in range(num_users)])
        reviews = np.zeros((self._num_users, self._num_books))

        for i in range(self._num_users):
            indexes = list(range(self._num_books))
            for k in range(int(self._num_books * (percentage_books_rated_user / 100))):
                option = random.choice(indexes)
                indexes.remove(option)
                reviews[i][option] = random.random()

        return reviews

        # TODO Use real recommendation data
        # TODO include users initial preferences
        # TODO include presence of books in reading lists
        # TODO include users following authors
        # TODO include bad recommendations

    def create_train_test(self, ratings=None):
        if ratings is None:
            self.ratings = self.gen_recommendation_matrix()
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
        users = self._connection.query("SELECT user_id FROM test_users")
        for count, i in enumerate(users):
            self.user_lookup_table[count] = i[0]

        self.book_lookup_table = dict()
        books = self._connection.query("SELECT book_id FROM test_books")
        for count, i in enumerate(books):
            self.book_lookup_table[count] = i[0]

        self.genre_lookup_table = dict()
        genres = self._connection.query("SELECT genre_id FROM test_genres")
        for count, i in enumerate(genres):
            self.genre_lookup_table[count] = i[0]

    def gen_recommendations(self):
        predictions = self.predict()

        query = "INSERT INTO test_recommendations (user_id, book_id, certainty) VALUES "

        for user, books in enumerate(predictions):
            user_books = []
            user_id = self.user_lookup_table[user]

            avoid_recs = {
                i[0] for i in self._connection.query("""
                        SELECT book_id
                        FROM test_recommendations
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
                        "certainty": rating
                    })

            user_books.sort(key=lambda x: x["certainty"], reverse=True)

            query += ",".join(
                f"({user_id}, {i['id']}, {i['certainty']})" for i in user_books[:self._number_recommendations]) + ","

        self._connection.query("""
            DELETE FROM test_recommendations
            WHERE date_added<=DATE_SUB(NOW(), INTERVAL 2 DAY)
        """)
        self._connection.query(query[:-1])

        # TODO books in reading lists
        # TODO convert dot products into percentage matches using cosine similarity

    def delete_recommendation(self, user_id, book_id):
        # This includes marking a recommendation as bad - it is implicitly the same thing
        self._connection.query("""
            DELETE FROM test_recommendations
            WHERE user_id={user_id}
                AND book_id={book_id}
        """.format(
            user_id=user_id,
            book_id=book_id
        ))

        self._connection.query(
            "INSERT INTO test_bad_recommendations (user_id, book_id) VALUES ({user_id}, {book_id})".format(
                user_id=user_id,
                book_id=book_id
            )
        )

    def get_bad_recommendations(self, user_id):
        bad_recommendations = self._connection.query("""
            SELECT recommendation_id,
                book_id,
                date_added
            FROM test_bad_recommendations
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
            "DELETE FROM test_bad_recommendations WHERE recommendation_id IN ({})".format(",".join(str(i) for i in remove)))
        # Delete expired recommendations.

        return return_vals

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
    rec = Recommendations(connection, 100, 0.1)
    rec.fit()
    rec.gen_recommendations()

# TODO add method to get specific user's recommendations
# TODO add method to add a new user
# TODO add method to get users recommendations
# TODO add method to set initial user preferences
# TODO create method to get recommendation summaries for specific user
