# -----------------------------------------------------------------------------
# Standard Python library imports
# -----------------------------------------------------------------------------
import re

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import authors
import configuration
import mysql_handler


# -----------------------------------------------------------------------------
# Objects
# -----------------------------------------------------------------------------
class Diaries:
    def __init__(self, connection):
        self._connection = connection

    def add_entry(self, user_id, book_id, overall_rating, character_rating, plot_rating, summary, thoughts, pages_read):
        params = locals()
        params = {i: "null" if k is None else k for i, k in zip(params.keys(), params.values())}
        if thoughts is not None:
            params["thoughts"] = '"' + re.sub("\n+", "\n", params["thoughts"]) + '"'
        if summary is not None:
            params["summary"] = '"' + params["summary"] + '"'
        self._connection.query("""
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

    def delete_entry(self, user_id, entry_id):
        # The user id is just a way of helping preventing a random deletion of a list. The corresponding user_id must be
        # known.
        self._connection.query("""
            DELETE from diary_entries
            WHERE user_id={user_id}
                AND entry_id={entry_id};
        """.format(user_id=user_id, entry_id=entry_id))

    def get_entries(self, user_id):
        res = self._connection.query("""
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
        """.format(user_id))  # Order by ensures that most recent is at the top.

        output_dict = dict()
        for i, k in enumerate(res):
            author = authors.names_to_display(k[12], k[13], k[14])

            thoughts = k[6]
            if thoughts is not None:
                thoughts = "</p><p>".join(("<p>" + k[6] + "</p>").split("\n"))
            output_dict[i] = {
                "entry_id": k[0],
                "book_id": k[1],
                "overall_rating": k[2],
                "character_rating": k[3],
                "plot_rating": k[4],
                "summary": k[5],
                "thoughts": thoughts,
                "date_added": k[7].strftime("%d-%m-%Y"),
                "pages_read": k[8],
                "cover_image": k[9],
                "title": k[10],
                "author_id": k[11],
                "author_name": author,
                "average_rating": float(k[15]),
                "number_ratings": k[16]
            }

        return output_dict

# -----------------------------------------------------------------------------
# File execution
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    config = configuration.Configuration("./project_config.conf")
    connection = mysql_handler.Connection(
        user=config.get("mysql username"),
        password=config.get("mysql password"),
        schema=config.get("mysql schema"),
        host=config.get("mysql host")
    )

    diaries = Diaries(connection)