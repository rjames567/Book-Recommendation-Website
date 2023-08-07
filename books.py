
import re

# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
import mysql_handler
import configuration

# ------------------------------------------------------------------------------
# Instantiating import classes
# ------------------------------------------------------------------------------
config = configuration.Configuration("project_config.conf")
connection = mysql_handler.Connection(
    user=config.get("mysql username"),
    password=config.get("mysql password"),
    schema=config.get("mysql schema"),
    host=config.get("mysql host")
)


# ------------------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------------------
class BookNotFoundError(Exception):
    """
    Exception for when a genre is not found.
    """

    def __init__(self, book_id):
        message = f"Book with ID '{book_id}' was not found."
        super().__init__(message)


# ------------------------------------------------------------------------------
# About data
# ------------------------------------------------------------------------------
def get_about_data(book_id, user_id):
    res = connection.query("""
        SELECT books.title,
            books.cover_image,
            books.synopsis,
            books.purchase_link,
            books.release_date,
            books.isbn,
            authors.first_name,
            authors.surname,
            authors.alias,
            authors.about,
            (SELECT COUNT(author_followers.author_id) FROM author_followers
                    WHERE author_followers.author_id=books.author_id) AS author_num_followers,
            (SELECT COUNT(reading_lists.book_id) FROM reading_lists
                    INNER JOIN reading_list_names ON reading_lists.list_id=reading_list_names.list_id
                    WHERE reading_list_names.list_name="Want to Read"
                            AND reading_lists.book_id=books.book_id) AS num_want_read,
            (SELECT COUNT(reading_lists.book_id) FROM reading_lists
                    INNER JOIN reading_list_names ON reading_lists.list_id=reading_list_names.list_id
                    WHERE reading_list_names.list_name="Currently Reading"
                            AND reading_lists.book_id=books.book_id) AS num_reading,
            (SELECT COUNT(reading_lists.book_id) FROM reading_lists
                    INNER JOIN reading_list_names ON reading_lists.list_id=reading_list_names.list_id
                    WHERE reading_list_names.list_name="Have Read"
                            AND reading_lists.book_id=books.book_id) AS num_read,
            authors.author_id
        FROM books
        INNER JOIN authors ON authors.author_id=books.author_id
        WHERE books.book_id={book_id};
    """.format(book_id=book_id))

    if len(res) == 0:
        raise BookNotFoundError(book_id)  # If the query result has 0 entries, no book was found with the target name
    else:
        res = res[0]

    first_name = res[6]
    surname = res[7]
    alias = res[8]
    if (alias is not None and
            (first_name is not None and surname is not None)):
        author = f"{alias} ({first_name} {surname})"
    elif (alias is not None and
          (first_name is None and surname is None)):
        author = alias
    else:
        author = f"{first_name} {surname}"

    genres = [i[0] for i in connection.query("""
        SELECT genres.name FROM genres
        INNER JOIN book_genres ON book_genres.genre_id=genres.genre_id
        WHERE book_genres.book_id={book_id};
    """.format(book_id=book_id))]  # The query returns a tuple, so this converts the list of tuples to a flat list

    output_dict = {
        "title": res[0],
        "cover_image": res[1],
        "synopsis": "</p><p>".join(("<p>" + res[2] + "</p>").split("\n")),  # Split at line breaks into paragraph blocks
        # Can just be inserted without any processing as it includes spacing because of p elements
        "purchase_link": res[3],
        "release_date": res[4].strftime("%d/%m/%Y"),
        "isbn": res[5],
        "author": author,
        "author_about": "</p><p>".join(("<p>" + res[9] + "</p>").split("\n")),
        "author_number_followers": res[10],
        "num_want_read": res[11],
        "num_reading": res[12],
        "num_read": res[13],
        "genres": genres,
        "author_id": res[14]
    }

    res = connection.query("""
            SELECT IFNULL(ROUND(AVG(overall_rating), 2), 0) AS average_rating,
            COUNT(overall_rating) AS num_ratings,
            (SELECT COUNT(overall_rating) from reviews
                WHERE overall_rating=5
                    AND book_id={book_id}) AS num_5_stars,
            (SELECT COUNT(overall_rating) from reviews
                WHERE overall_rating=4
                    AND book_id={book_id}) AS num_4_stars,
            (SELECT COUNT(overall_rating) from reviews
                WHERE overall_rating=3
                    AND book_id={book_id}) AS num_3_stars,
            (SELECT COUNT(overall_rating) from reviews
                WHERE overall_rating=2
                    AND book_id={book_id}) AS num_2_stars,
            (SELECT COUNT(overall_rating) from reviews
                WHERE overall_rating=1
                    AND book_id={book_id}) AS num_1_star
            FROM reviews
            WHERE book_id={book_id};
        """.format(book_id=book_id))[0]  # This always gives one tuple, regardless of whether there are any reviews.

    # Even if there is no reviews, the query has results of 0 for all these.
    output_dict["average_rating"] = float(res[0])  # The query gives a Decimal type, so cast to float to be useful.
    output_dict["num_ratings"] = res[1]
    output_dict["num_5_stars"] = res[2]
    output_dict["num_4_stars"] = res[3]
    output_dict["num_3_stars"] = res[4]
    output_dict["num_2_stars"] = res[5]
    output_dict["num_1_star"] = res[6]

    if user_id is None:
        output_dict["current_user_review"] = None
        user_id = -1  # This will match all entries, as it is never equal to an ID, as they are natural numbers.
    else:
        res = connection.query("""
                SELECT review_id, 
                    overall_rating,
                    plot_rating,
                    character_rating,
                    summary,
                    rating_body
                FROM reviews
                WHERE user_id={user_id};
            """.format(user_id=user_id))
        if len(res) == 0:
            output_dict["current_user_review"] = None
        else:
            body = res[0][5]
            if body is not None:
                body = "</p><p>".join(("<p>" + body + "</p>").split("\n"))
            output_dict["current_user_review"] = {
                "review_id": res[0][0],
                "overall_rating": res[0][1],
                "plot_rating": res[0][2],
                "character_rating": res[0][3],
                "summary": res[0][4],
                "rating_body": body
            }

    res = connection.query("""
        SELECT reviews.review_id,
            reviews.overall_rating,
            reviews.plot_rating,
            reviews.character_rating,
            reviews.summary,
            reviews.rating_body,
            reviews.date_added,
            users.username
        FROM reviews
        INNER JOIN users ON users.user_id=reviews.user_id
        WHERE reviews.user_id!={user_id}
            AND reviews.book_id={book_id};
    """.format(user_id=user_id,
               book_id=book_id))  # Inserting None will insert a string “None” so will not match any IDs.
    # Does not include the current user's review. If it is None it includes all users.

    review_arr = []
    for i in res:
        body = i[5]
        if body is not None:
            body = "</p><p>".join(("<p>" + body + "</p>").split("\n"))
        review_arr.append({
            "id": i[0],
            "overall_rating": i[1],
            "plot_rating": i[2],
            "character_rating": i[3],
            "summary": i[4],
            "rating_body": body,
            "date_added": i[6].strftime("%d/%m/%Y"),
            "username": i[7],
        })

    output_dict["reviews"] = review_arr

    output_dict["author_following"] = bool(len(connection.query("""
        SELECT author_id FROM author_followers
        WHERE author_id={author_id}
            AND user_id={user_id};
    """.format(author_id=output_dict["author_id"], user_id=user_id))))  # Finds all entries with the same user and
    # author id as required, which will either be 1 or 0. If it is 0, the user is not following the author, so the
    # author_following value should be false. If it is 1, they are, so it should be true. Len gets the number of results
    # (1 or 0), and bool converts this to the corresponding boolean value, which is whether the user is following the
    # author.

    return output_dict


# ------------------------------------------------------------------------------
# Reviews
# ------------------------------------------------------------------------------
def delete_review(review_id, user_id):
    connection.query("""
        DELETE FROM reviews
        WHERE user_id={user_id}
            AND review_id={review_id};
    """.format(user_id=user_id, review_id=review_id))

def leave_review(user_id, book_id, overall_rating, plot_rating, character_rating, summary, thoughts):
    thoughts = re.sub("\n+", "\n", thoughts)  # Remove repeated new lines from string.
    connection.query("""
        INSERT INTO reviews (user_id, book_id, overall_rating, plot_rating, character_rating, summary, rating_body) VALUES
        ({user_id}, {book_id}, {overall_rating}, {plot_rating}, {character_rating}, "{summary}", "{rating_body}");
    """.format(
        user_id=user_id,
        book_id=book_id,
        overall_rating=overall_rating,
        plot_rating=plot_rating,
        character_rating=character_rating,
        summary=summary,
        rating_body=thoughts
    ))