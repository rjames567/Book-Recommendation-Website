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
