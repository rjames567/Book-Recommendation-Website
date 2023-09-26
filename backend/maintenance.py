# -----------------------------------------------------------------------------
# Standard Python library imports
# -----------------------------------------------------------------------------
import json
import urllib.parse

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import components.accounts
import components.authors
import components.books
import components.diaries
import components.genres
import components.information_retrieval
import components.reading_lists
import components.recommendations

import configuration
import environ_manipulation
import logger
import mysql_handler

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


# -----------------------------------------------------------------------------
# Class instantiation
# -----------------------------------------------------------------------------
diaries = components.diaries.Diaries(connection)
genres = components.genres.Genres(connection)
sessions = components.accounts.Sessions(connection, token_size)
authors = components.authors.Authors(connection, genre_required_match, number_summaries_home)
recommendations = components.recommendations.Recommendations(
    connection,
    genre_required_match,
    num_display_genres,
    authors
)
reading_lists = components.reading_lists.ReadingLists(
    connection,
    number_summaries_home,
    genre_required_match,
    num_display_genres,
    recommendations
)
books = components.books.Books(
    connection,
    reading_lists,
    genre_required_match,
    number_similarities_about,
    number_summaries_home,
    num_display_genres
)
accounts = components.accounts.Accounts(
    connection,
    hashing_algorithm,
    hashing_salt,
    number_hash_passes,
    reading_lists
)
information_retrieval = components.information_retrieval.DocumentCollection(
    connection,
    books,
    authors,
    genres,
    num_search_results
)

# -----------------------------------------------------------------------------
# Recommendations
# -----------------------------------------------------------------------------
for i in accounts.get_user_id_list():
    recommendations.recommend_user_books(i)