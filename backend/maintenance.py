# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import components.accounts
import components.recommendations

import configuration
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
sessions = components.accounts.Sessions(connection, token_size)
recommendations = components.recommendations.Recommendations(
    connection,
    config.get("recommendations number_converge_iterations"),
    config.get("recommendations hyperparameter"),
    config.get("home number_display_genres"),
    config.get("recommendations inital_recommendation_matrix_value"),
    config.get("recommendations reading_list_percentage_increase"),
    config.get("recommendations author_following_percentage_increase"),
    config.get("recommendations bad_recommendations_matrix_value"),
    config.get("recommendations minimum_required_reviews"),
    config.get("recommendations number_recommendations"),
)

# -----------------------------------------------------------------------------
# Sessions
# -----------------------------------------------------------------------------
for i in sessions.get_session_id_list():
    try:
        sessions.get_user_id(i)
    except components.accounts.SessionExpiredError:
        pass

# -----------------------------------------------------------------------------
# Recommendations
# -----------------------------------------------------------------------------
recommendations.fit()
recommendations.gen_recommendations()