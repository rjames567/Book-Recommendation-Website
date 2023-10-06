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
        self._training = False
        self._u_fact = self._b_fact = None
        self._num_converge_iters = num_converge_iters
        self._hyperparam = hyperparam
        self._trained = trained

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
        elif (self._b_fact is None and self._trained):
            res = self._connection.query("""
                SELECT GROUP_CONCAT(genre_id) as genres,
                    GROUP_CONCAT(match_strength) as strengths,
                    book_id
                FROM book_genres
                GROUP BY book_id;
            """)

            mat = data_structures.Matrix(
                n=self._number_books,
                m=self._number_factors,
                default_value=random.random
            )

            for genres, strengths, book in res:
                ids = genres.split()
                strengths = strengths.split()
                for genre_id, strength in zip(ids, strengths):
                    mat[genre_id][book] = strength

            return mat  # Does not update the stored value of the book factor
            # matrix. This is because it cannot guarantee whether the contents
            # stored in the database has changed, because of being run in
            # multiple locations. This therefore means that it must assume that
            # it has changed.
        return self._b_fact  # If it is being trained, it should update the
        # actual matrix, and return it.