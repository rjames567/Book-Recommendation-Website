# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import re

# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
import configuration
import mysql_handler

# ------------------------------------------------------------------------------
# Instantiating import classes
# ------------------------------------------------------------------------------
config = configuration.Configuration("./project_config.conf")
connection = mysql_handler.Connection(
    user=config.get("mysql username"),
    password=config.get("mysql password"),
    schema=config.get("mysql schema"),
    host=config.get("mysql host")
)


# ------------------------------------------------------------------------------
# Add diary entry
# ------------------------------------------------------------------------------
def add_entry(user_id, book_id, overall_rating, character_rating, plot_rating, summary, thoughts, pages_read):
    params = locals()
    params = {i: "null" if k is None else k for i, k in zip(params.keys(), params.values())}
    if thoughts is not None:
        params["thoughts"] = '"' + re.sub("\n+", "\n", params["thoughts"]) + '"'
    if summary is not None:
        params["summary"] = '"' + params["summary"] + '"'
    connection.query("""
        INSERT INTO diary_entries (user_id, book_id, overall_rating, character_rating, plot_rating, summary, thoughts, pages_read)
        VALUES
        ({user_id}, {book_id}, {overall_rating}, {character_rating}, {plot_rating}, {summary}, {thoughts}, {pages_read});
    """.format(
        user_id=params["user_id"],
        book_id=params["book_id"],
        overall_rating=params["overall_rating"],
        character_rating=params["character_rating"],
        plot_rating=params["plot_rating"],
        summary=params["summary"],
        thoughts=params["thoughts"],
        pages_read=params["pages_read"]
    ))