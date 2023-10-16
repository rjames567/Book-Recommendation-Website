# -----------------------------------------------------------------------------
# Standard Python library imports
# -----------------------------------------------------------------------------
import math
import random

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
# import components.authors

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import data_structures
import ml_utilities

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
    def __init__(self, connection, genre_match_threshold, num_display_genres, authors, num_converge_iters, hyperparam,
                 trained=True):
        self._authors = authors
        self._connection = connection
        self._num_display_genres = num_display_genres
        self._genre_match_threshold = genre_match_threshold
        self._number_factors = len(
            self._connection.query("SELECT genre_id FROM genres")
        )
        self._user_id_lookup = dict()
        res = self._connection.query("SELECT book_id FROM books")
        self._number_books = len(res)
        self._b_id_look = dict()
        for count, i in enumerate(res):
            self._book_id_lookup[count] = i[0]
        res = self._connection.query("SELECT user_id FROM users")
        for count, i in enumerate(res):
            self._user_id_lookup[count] = i[0]
        self._number_users = len(res)
        self._training = False
        self._u_fact = self._b_fact = None
        self._num_converge_iters = num_converge_iters
        self._hyperparam = hyperparam
        self._trained = trained
        self._recommendation_number = 15
        self._following_percentage_increase = 0.5
        self._default_value = 0.2  # If a user has not got any explicit data, multiplying will not work, so

    def wals_step(self, ratings, fixed):
        I = data_structures.IdentityMatrix(self._number_factors)
        A = (fixed.transpose() * fixed) + I * self._hyperparam
        B = ratings * fixed
        A_inv = A.inverse()
        return (B * A_inv)

    def fit(self):
        train, test = self._gen_test_train_data()
        self._training = True
        self._trained = False

        self._number_factors = train.n
        self._number_users = train.m

        self.test_mse_record = []
        self.train_mse_record = []

        for i in range(self._num_converge_iters):
            print(f"Iteration: {i} of {self._num_converge_iters}")
            self.user_factors = self.wals_step(train, self.book_factors)
            self.book_factors = self.wals_step(train.transpose(), self.user_factors)

            predictions = self.predict()

            test_mse = self.mean_squared_error(test, predictions)
            train_mse = self.mean_squared_error(train, predictions)
            self.test_mse_record.append(test_mse)
            self.train_mse_record.append(train_mse)

        self._save_user_factors()
        self._save_book_factors()

        self._training = False
        self._trained = True

    def predict(self):
        return self.user_factors * self.book_factors

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

        target_vec = data_structures.Vector(
            dimensions=self._number_factors,
            default_value=0
        )

        for avg, genre_id in res:
            target_vec[genre_id] = avg

        rec = target_vec.transpose() * self.book_factors

        output = []
        for count, val in enumerate(rec[0]):
            output.append({
                "id": self._book_id_lookup[count],
                "strength": val
            })

        output.sort(key=lambda x: x["strength"], reverse=True)

        return output[:self._recommendation_number]

    def _save_user_factors(self):
        self._connection.query("DELETE FROM user_genres")
        query = "INSERT INTO user_genres (user_id, genre_id, match_strength) VALUES"

        self._u_fact = self.remove_floating_point_errors(self._u_fact, 1E-15)

        for genre_id, vals in enumerate(self._u_fact):
            for user_id, strength in enumerate(vals):
                query += f" ({self._user_id_lookup[user_id]}, {genre_id + 1}, {strength}),"
        query = query[:-1]  # Remove trailing comma
        self._connection.query(query)
        self._u_fact = None  # This is done to free up memory as the matrix

        # will take up a large amount of memory (for the training data of
        # 500 users, 768 genres, this would take up ~2.93MiB for raw data).

    def _save_book_factors(self):
        self._connection.query("DELETE FROM book_genres")
        query = "INSERT INTO book_genres (book_id, genre_id, match_strength) VALUES"

        self._b_fact = self.remove_floating_point_errors(self._b_fact, 1E-15)
        # Reduce the size of the stored data by removing very small, non-zero values

        for genre_id, vals in enumerate(self._b_fact):
            for book_id, strength in enumerate(vals):
                query += f" ({self._book_id_lookup[book_id]}, {genre_id + 1}, {strength}),"
        query = query[:-1]  # Remove trailing comma
        self._connection.query(query)
        self._b_fact = None  # This is done to free up memory as the matrix

        # will take up a large amount of memory (for the training data of
        # 250 books, 768 genres, this would take up ~1.46MiB for raw data).

    def gen_review_matrix(self):
        mat = data_structures.Matrix(
            m=self._number_users,
            n=self._number_books,
            default_value=0
        )

        user_ids = [i[0] for i in self._connection.query("SELECT user_id FROM users")]
        for user in user_ids:
            reviews = self._connection.query("""
                SELECT book_id,
                    (overall_rating + IFNULL(character_rating, overall_rating) + IFNULL(plot_rating, overall_rating)) / 3
                FROM reviews
                WHERE user_id={}
                GROUP BY review_id;
            """.format(user))

            if self._trained:
                books = self._connection.query("""
                    SELECT initial_preferences.user_id,
                        GROUP_CONCAT(book_genres.match_strength),
                        GROUP_CONCAT(book_genres.genre_id)
                    FROM initial_preferences
                    INNER JOIN books
                        ON books.author_id=initial_preferences.author_id
                    INNER JOIN book_genres
                        ON book_genres.book_id=books.book_id
                    WHERE user_id={}
                    GROUP BY books.book_id
                    ORDER BY book_genres.genre_id ASC
                """.format(user))
            else:
                books = self._connection.query("""
                    SELECT book_id from initial_preferences
                    WHERE user_id={}
                """.format(user))

            for book_id, average in reviews:
                used_book_id = list(self._book_id_lookup.values()).index(book_id)  # This finds the key for the value stored in the lookup table.
                # geeksforgeeks.org/python-get-key-from-value-in-dictionary
                mat[user - 1][used_book_id] = float(average)  # The user_ids won't work if a user is deleted, however this is not supported, so is not an issue.
            if len(reviews) <= 10:  # Until the user has left 10 reviews, still use their initial preferences.
                if len(books) > 0:
                    if self._trained:
                        avg_vec = data_structures.Vector(
                            dimensions=self._number_factors,
                            default_value=0
                        )

                        for strength, genre_id in books:
                            avg_vec[genre_id - 1] = strength  # Need to reduce id as SQL indexes from 1 not 0.

                        expected = avg_vec.transpose() * self.book_factors
                        output = []
                        for count, match in enumerate(expected[0]):
                            output.append({
                                "id": count,
                                "cosim": match
                            })
                        output.sort(key=lambda x: x["cosim"])
                        for i in output:
                            mat[user - 1][i["id"]] = math.tanh(i["cosim"]/self._number_factors)  # tanh limits results between 0 and 1, and with many genres is almost linear. Will always range from 0 to ~ 0.762
                    else:
                        for i in books:
                            used_book_id = list(self._book_id_lookup.values()).index(i[0])
                            mat[user - 1][used_book_id] = self._default_value  # This is a non-zero value so recommendation is made. This is not affected by the average preference expressed
                            # by all the user's selected authors.
                else:
                    continue  # skip immediately to the next user if they have not started their recommendations, to prevent incorrect alterations to the book matrix.
            elif len(books):
                self._connection.query("""
                    DELETE FROM initial_preferences
                    WHERE user_id={}
                """.format(user))

            lists = self._connection.query("""
                SELECT reading_lists.book_id
                FROM reading_lists
                INNER JOIN reading_list_names
                    ON reading_lists.list_id=reading_list_names.list_id
                WHERE reading_lists.user_id={}
                GROUP BY reading_lists.book_id;
            """.format(user))

            for i in lists:
                used_book_id = list(self._book_id_lookup.values()).index(int(i[0]))
                if mat[user - 1][used_book_id] == 0:
                    mat[user - 1][used_book_id] = self._default_value
                else:
                    mat[user - 1][used_book_id] *= (1 + self._following_percentage_increase)

            following = self._connection.query("""
                SELECT GROUP_CONCAT(books.book_id)
                FROM author_followers
                INNER JOIN books
                    ON books.author_id=author_followers.author_id
                WHERE user_id={}
                GROUP BY author_followers.author_id;
            """.format(user))

            for i in following:
                for k in i[0].split(","):
                    used_book_id = list(self._book_id_lookup.values()).index(int(k))
                    if mat[user - 1][used_book_id] == 0:
                        mat[user - 1][used_book_id] = self._default_value
                    else:
                        mat[user - 1][used_book_id] *= (1 + self._following_percentage_increase)

        indexes = [count for count, i in enumerate(mat) if sum(i) == 0]
        indexes.sort(reverse=True)  # Needs to be done from last to first, as if it were done the other way, the indexes would change and could raise errors or delete incorrect rows.
        for i in indexes:
            mat.remove_row(i)  # Remove rows that are only zero. This is so that any users who have not specified their recommendations yet do not affect the book matrix

        return mat

    def _gen_test_train_data(self):
        ratings = self.gen_review_matrix()
        copy = ratings
        while ratings == copy:
            copy = ratings.copy()
            num_items = len(copy)

            for i in range(random.randint(num_items//8, num_items//4)):
                copy[random.randint(0, copy.m - 1)][random.randint(0, copy.n - 1)] = random.random()

        return ratings, copy

    @staticmethod
    def remove_floating_point_errors(matrix, threshold):
        for row, row_val in enumerate(matrix):
            for col, val in enumerate(row_val):
                if val <= threshold:
                    matrix[row][col] = 0
        return matrix

    @staticmethod
    def mean_squared_error(true, predicted):
        mask = true.get_zero_indexes()
        pred = predicted.mask(mask)
        true = true.mask(mask)
        return ml_utilities.mean_squared_error(true, pred)

    @property
    def _book_id_lookup(self):
        if self._b_id_look is None:
            self._b_id_look = dict()
            res = self._connection.query("""
                SELECT book_id
                FROM books
            """)

            for book_id, i in enumerate(res):
                self._b_id_look[book_id] = i[0]
        return self._b_id_look

    @property
    def book_factors(self):
        if self._b_fact is None and not self._trained:
            self._b_fact = data_structures.Matrix(
                n=self._number_books,
                m=self._number_factors,
                default_value=random.random
            )
            res = self._connection.query("""
                SELECT book_id FROM books
                ORDER BY book_id ASC
            """)

            for book_id, i in enumerate(res):
                self._book_id_lookup[book_id] = i[0]  # Have to create a lookup
                # table as it cannot be guaranteed that the book IDs are
                # sequential, with not gaps.

        elif (self._b_fact is None and self._trained):
            res = self._connection.query("""
                SELECT GROUP_CONCAT(genre_id) as genres,
                    GROUP_CONCAT(match_strength) as strengths,
                    book_id
                FROM book_genres
                GROUP BY book_id
                ORDER BY book_id ASC
            """)

            mat = data_structures.Matrix(
                n=self._number_books,
                m=self._number_factors,
                default_value=0
            )

            for book_id, tup in enumerate(res):
                genres, strengths, book_true = tup
                ids = genres.split(",")
                strengths = strengths.split(",")
                for genre_id, strength in zip(ids, strengths):
                    mat[int(genre_id) - 1][book_id - 1] = float(strength)

            for book_id, i in enumerate(res):
                self._book_id_lookup[book_id] = i[2]  # Have to create a lookup
                # table as it cannot be guaranteed that the book IDs are
                # sequential, with not gaps.

            return mat  # Does not update the stored value of the book factor
            # matrix. This is because it cannot guarantee whether the contents
            # stored in the database has changed, because of being run in
            # multiple locations. This therefore means that it must assume that
            # it has changed.
        return self._b_fact  # If it is being trained, it should update the
        # actual matrix, and return it.

    @book_factors.setter
    def book_factors(self, matrix):
        self._b_fact = matrix
        if not self._training:
            self._save_book_factors()

    @property
    def user_factors(self):
        if self._u_fact is None and not self._trained:
            print(1)
            self._u_fact = data_structures.Matrix(
                n=self._number_users,
                m=self._number_factors,
                default_value=random.random
            )
            res = self._connection.query("""
                SELECT user_id FROM users
                ORDER BY user_id ASC
            """)

            for user_id, i in enumerate(res):
                self._user_id_lookups[user_id] = i[0]  # Have to create a lookup
                # table as it cannot be guaranteed that the book IDs are
                # sequential, with not gaps.

        elif (self._u_fact is None and self._trained):
            res = self._connection.query("""
                SELECT GROUP_CONCAT(genre_id) as genres,
                    GROUP_CONCAT(match_strength) as strengths,
                    user_id
                FROM user_genres
                GROUP BY user_id
                ORDER BY user_id ASC
            """)

            mat = data_structures.Matrix(
                n=self._number_books,
                m=self._number_factors
            )

            for user_id, tup in enumerate(res):
                genres, strengths, user_true = tup
                ids = genres.split(",")
                strengths = strengths.split(",")
                self._user_id_lookup[user_id] = user_true
                for genre_id, strength in zip(ids, strengths):
                    mat[int(genre_id) - 1][user_id - 1] = float(strength)

            return mat  # Does not update the stored value of the book factor
            # matrix. This is because it cannot guarantee whether the contents
            # stored in the database has changed, because of being run in
            # multiple locations. This therefore means that it must assume that
            # it has changed.
        return self._u_fact  # If it is being trained, it should update the
        # actual matrix, and return it.

    @user_factors.setter
    def user_factors(self, matrix):
        self._u_fact = matrix
        if not self._training:
            self._save_user_factors()



# # -----------------------------------------------------------------------------
# # Project imports
# # -----------------------------------------------------------------------------
# import components.authors

import configuration
import mysql_handler

# # -----------------------------------------------------------------------------
# # Project constants
# # -----------------------------------------------------------------------------
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

# # -----------------------------------------------------------------------------
# # Class instantiation
# # -----------------------------------------------------------------------------
# authors = components.Authors(connection, genre_required_match, number_summaries_home)
print("RUNNING")
rec = Recommendations(connection, genre_required_match, num_display_genres, None, 1, 0.1)

rec.fit()