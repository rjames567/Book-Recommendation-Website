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

    def __init__(self, book_title):
        message = f"Book '{book_title}' was not found"
        super().__init__(message)


# ------------------------------------------------------------------------------
# About data
# ------------------------------------------------------------------------------
def get_about_data(book_title, user_id):
    res = connection.query("""
        SELECT books.book_id,
            books.title,
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
                            AND reading_lists.book_id=books.book_id) AS num_read
        FROM books
        INNER JOIN authors ON authors.author_id=books.book_id
        WHERE books.title="{book_title}";
    """.format(book_title=book_title))

    if len(res) == 0:
        raise BookNotFoundError(book_title)  # If the query result has 0 entries, no book was found with the target name
    else:
        res = res[0]

    book_id = res[0]  # Avoids joins for subsequent queries
    first_name = res[7]
    surname = res[8]
    alias = res[9]
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
        "title": res[1],
        "cover_image": res[2],
        "synopsis": res[3],
        "purchase_link": res[4],
        "release_date": res[5],
        "isbn": res[6],
        "author": author,
        "author_about": res[10],
        "author_number_followers": res[11],
        "num_want_read": res[12],
        "num_reading": res[13],
        "num_read": res[14],
        "genres": genres,
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
                SELECT overall_rating,
                    plot_rating,
                    character_rating,
                    IFNULL(summary, "") AS summary,
                    IFNULL(rating_body, "") AS body
                FROM reviews
                WHERE user_id={user_id};
            """.format(user_id=user_id))
        if len(res) == 0:
            output_dict["current_user_review"] = None
        else:
            output_dict["current_user_review"] = {
                "overall_rating": res[0][0],
                "plot_rating": res[0][1],
                "character_rating": res[0][2],
                "summary": res[0][3],
                "rating_body": res[0][4]
            }


    res = connection.query("""
        SELECT reviews.overall_rating,
            reviews.plot_rating,
            reviews.character_rating,
            IFNULL(reviews.summary, "") AS summary,
            IFNULL(reviews.rating_body, "") AS body,
            reviews.date_added,
            users.username
        FROM reviews
        INNER JOIN users ON users.user_id=reviews.user_id
        WHERE users.user_id!={user_id};
    """.format(user_id=user_id))  # Inserting None will insert a string “None” so will not match any IDs.
    # Does not include the current user's review. If it is None it includes all users.

    review_arr = []
    for i in res:
        review_arr.append({
            "overall_rating": i[0],
            "plot_rating": i[1],
            "character_rating": i[2],
            "summary": i[3],
            "rating_body": i[4],
            "date_added": i[5],
            "username": i[6],
        })

    output_dict["reviews"] = review_arr

    return output_dict
