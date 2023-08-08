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


# ------------------------------------------------------------------------------
# Delete diary entry
# ------------------------------------------------------------------------------
def delete_entry(user_id, entry_id):
    # The user id is just a way of helping preventing a random deletion of a list. The corresponding user_id must be
    # known.
    connection.query("""
        DELETE from diary_entries
        WHERE user_id={user_id}
            AND entry_id={entry_id};
    """.format(user_id=user_id, entry_id=entry_id))


# ------------------------------------------------------------------------------
# Get diary entries
# ------------------------------------------------------------------------------
def get_entries(user_id):
    res = connection.query(x:="""
        SELECT diary_entries.entry_id,
            diary_entries.book_id,
            diary_entries.overall_rating,
            diary_entries.character_rating,
            diary_entries.plot_rating,
            diary_entries.summary,
            diary_entries.thoughts,
            diary_entries.date_added,
            diary_entries.pages_read,
            books.cover_image,
            books.title,
            authors.author_id,
            authors.first_name,
            authors.surname,
            authors.alias,
            (SELECT IFNULL(ROUND(AVG(reviews.overall_rating), 2), 0)
                FROM reviews
                WHERE reviews.book_id=books.book_id) AS average_rating,
            (SELECT COUNT(reviews.overall_rating)
                FROM reviews
                WHERE reviews.book_id=books.book_id) AS num_rating
        FROM diary_entries
        INNER JOIN books ON books.book_id=diary_entries.book_id
        INNER JOIN authors ON books.author_id=authors.author_id
        WHERE diary_entries.user_id={}
        ORDER BY diary_entries.date_added DESC;
    """.format(user_id)) # Order by ensures that most recent is at the top.

    output_dict = dict()
    for i, k in enumerate(res):
        first_name = k[12]
        surname = k[13]
        alias = k[14]
        if (alias is not None and
                (first_name is not None and surname is not None)):
            author = f"{alias} ({first_name} {surname})"
        elif (alias is not None and
              (first_name is None and surname is None)):
            author = alias
        else:
            author = f"{first_name} {surname}"
        output_dict[i] = {
            "entry_id": k[0],
            "book_id": k[1],
            "overall_rating": k[2],
            "character_rating": k[3],
            "plot_rating": k[4],
            "summary": k[5],
            "thoughts": k[6],
            "date_added": k[7],
            "pages_read": k[8],
            "cover_image": k[9],
            "title": k[10],
            "author_id": k[11],
            "author_name": author,
            "average_rating": float(k[15]),
            "number_ratings": k[16]
        }

    return output_dict