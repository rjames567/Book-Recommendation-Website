# -----------------------------------------------------------------------------
# Standard Python library imports
# -----------------------------------------------------------------------------
import math
import random

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import components.authors

import sys
sys.path.append("../backend")

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
        self._number_books = len(
            self._connection.query("SELECT book_id FROM books")
        )
        self._number_users = len(
            self._connection.query("SELECT user_id FROM users")
        )
        self._training = False
        self._u_fact = self._b_fact = None
        self._num_converge_iters = num_converge_iters
        self._hyperparam = hyperparam
        self._trained = trained
        self._book_id_lookup = dict()
        self._user_id_lookup = dict()

    def wals_step(self, ratings, fixed):
        I = data_structures.IdentityMatrix(self._number_factors)
        A = (fixed.transpose() * fixed) + I * self._hyperparam
        B = ratings * fixed
        A_inv = A.inverse()
        return (B * A_inv)

    def predict(self):
        return self.user_factors * self.book_factors

    @staticmethod
    def mean_squared_error(true, predicted):
        mask = true.get_zero_indexes()
        true = true.mask(mask)
        pred = true.mask(mask)
        return ml_utilities.mean_squared_error(true, predicted)

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
                m=self._number_factors
            )

            for book_id, tup in res:
                genres, strengths, book_true = tup
                ids = genres.split()
                strengths = strengths.split()
                for genre_id, strength in zip(ids, strengths):
                    self._book_id_lookup[book_id] = book_true
                    mat[genre_id][book_id] = strength

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
            self._connection.query("DELETE FROM book_genres")
            query = "INSERT INTO book_genres (book_id, genre_id, match_strength) VALUES"
            for genre_id, vals in enumerate(self._b_fact):
                for book_id, strength in enumerate(vals):
                    query += f" ({self._book_id_lookup[book_id]}, {genre_id + 1}, {strength}),"
            query = query[:-1]  # Remove trailing comma
            self._connection.query(query)
            self._b_fact = None  # This is done to free up memory as the matrix
            # will take up a large amount of memory (for the training data of
            # 250 books, 768 genres, this would take up ~1.46MiB for raw data).

    @property
    def user_factors(self):
        if self._u_fact is None and not self._trained:
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
                self._user_id_lookup[user_id] = i[0]  # Have to create a lookup
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

            for user_id, tup in res:
                genres, strengths, user_true = tup
                ids = genres.split()
                strengths = strengths.split()
                for genre_id, strength in zip(ids, strengths):
                    self._user_id_lookup[user_id] = user_true
                    mat[genre_id][user_id] = strength

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
            self._connection.query("DELETE FROM user_genres")
            query = "INSERT INTO user_genres (user_id, genre_id, match_strength) VALUES"
            for genre_id, vals in enumerate(self._u_fact):
                for user_id, strength in enumerate(vals):
                    query += f" ({self._user_id_lookup[user_id]}, {genre_id + 1}, {strength}),"
            query = query[:-1]  # Remove trailing comma
            self._connection.query(query)
            self._u_fact = None  # This is done to free up memory as the matrix
            # will take up a large amount of memory (for the training data of
            # 500 users, 768 genres, this would take up ~2.93MiB for raw data).
