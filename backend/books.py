# -----------------------------------------------------------------------------
# Standard Python library imports
# -----------------------------------------------------------------------------
import re

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import authors as authors_mod
import recommendations as recommendations_mod
import reading_lists as reading_lists_mod
import configuration
import data_structures
import ml_utilities
import mysql_handler


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------
class BookNotFoundError(Exception):
    """
    Exception for when a book is not found.
    """

    def __init__(self, book_id):
        message = f"Book with ID '{book_id}' was not found."
        super().__init__(message)

# -----------------------------------------------------------------------------
# Objects
# -----------------------------------------------------------------------------
class Books:
    def __init__(self, connection, reading_lists, genre_required_match, number_similarities_about, number_summaries_home, num_display_genres):
        self._reading_lists = reading_lists
        self._num_display_genres = num_display_genres
        self._number_summaries_home = number_summaries_home
        self._number_similarities_about = number_similarities_about
        self._connection = connection
        self._genre_required_match = genre_required_match

    def get_similar_items(self, book_id):
        res = self._connection.query("""
            SELECT book_genres.book_id,
                GROUP_CONCAT(book_genres.genre_id) as genres,
                books.author_id
            FROM book_genres
            INNER JOIN books ON books.book_id=book_genres.book_id
            GROUP BY book_id;
        """)  # Match strength is included, as then more are more likely to appear, and
        # therefore will impact on the similarity.

        genre_dict = dict()
        for i in res:
            items = set(float(k) for k in i[1].split(","))
            items.add(-i[2])  # Must be negative, as otherwise it would be treated as a genre, which may not work
            genre_dict[i[0]] = items

        target_genres = genre_dict[book_id]
        genre_dict.pop(book_id)

        tree = data_structures.BinaryTree(access_function=lambda x: x["jaccard_distance"])  # Insert into tree using
        # similarity not id
        for i in genre_dict:
            tree.insert({
                "book_id": i,
                "jaccard_distance": 1 - ml_utilities.jaccard_similarity(target_genres, genre_dict[i])  # 1 - similarity
                # gives the distance, so this in ascending order gives them in similairty in descending order.
            })

        result = tree.in_order_traversal()[
                 :self._number_similarities_about]  # Get the books ordered by similarity. Note that the distance is
        # descending - This is correct, as 0 is identical genres, and 1 is different

        return [self.get_summary(i["book_id"]) for i in result]

    def get_summary(self, book_id=None, isbn=None):
        if book_id is not None:
            res = self._connection.query("""
                SELECT books.title,
                    books.book_id,
                    books.cover_image,
                    authors.first_name,
                    authors.surname,
                    authors.alias
                FROM books
                INNER JOIN authors ON books.author_id=authors.author_id
                WHERE books.book_id={}
            """.format(book_id))
        else:
            res = self._connection.query("""
                SELECT books.title,
                    books.book_id,
                    books.cover_image,
                    authors.first_name,
                    authors.surname,
                    authors.alias
                FROM books
                INNER JOIN authors ON books.author_id=authors.author_id
                WHERE books.isbn="{}"
            """.format(isbn))

        if len(res) == 0:
            raise BookNotFoundError(book_id)

        res = res[0]

        return {
            "author": authors_mod.names_to_display(res[3], res[4], res[5]),
            "title": res[0],
            "book_id": res[1],
            "cover": res[2],
        }

    def get_newest(self):
        res = self._connection.query("""
            SELECT books.title,
                books.book_id,
                books.cover_image,
                authors.first_name,
                authors.surname,
                authors.alias
            FROM books
            INNER JOIN authors ON books.author_id=authors.author_id
            ORDER BY books.date_added DESC;
        """)[:self._number_summaries_home]  # Get the first n books

        output_dict = dict()
        for i, k in enumerate(res):
            output_dict[i] = {
                "author": authors_mod.names_to_display(k[3], k[4], k[5]),
                "title": k[0],
                "book_id": k[1],
                "cover": k[2],
            }

        return output_dict

    def get_about_data(self, book_id, user_id):
        res = self._connection.query("""
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
            raise BookNotFoundError(
                book_id)  # If the query result has 0 entries, no book was found with the target name
        else:
            res = res[0]

        author = authors_mod.names_to_display(res[6], res[7], res[8])

        genres = [i[0] for i in self._connection.query("""
            SELECT genres.name FROM genres
            INNER JOIN book_genres ON book_genres.genre_id=genres.genre_id
            WHERE book_genres.book_id={book_id}
            ORDER BY book_genres.match_strength DESC;
        """.format(book_id=book_id))][
                 :self._num_display_genres]  # The query returns a tuple, so this converts the list of tuples to a flat list

        output_dict = {
            "title": res[0],
            "cover_image": res[1],
            "synopsis": "</p><p>".join(("<p>" + res[2] + "</p>").split("\n")),
            # Split at line breaks into paragraph blocks
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

        res = self._connection.query("""
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
            res = self._connection.query("""
                    SELECT review_id, 
                        overall_rating,
                        plot_rating,
                        character_rating,
                        summary,
                        rating_body
                    FROM reviews
                    WHERE user_id={user_id}
                        AND book_id={book_id};
                """.format(user_id=user_id, book_id=book_id))
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

        res = self._connection.query("""
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

        res = self._connection.query("""
            SELECT list_id FROM reading_list_names
            WHERE user_id={}
                AND list_name="Have Read"
        """.format(user_id))

        if len(res) == 0:  # Add have read list id to response, so leaving a review will mark it as read
            output_dict["list_id"] = None
        else:
            output_dict["list_id"] = res[0][0]  # List of one, single element tuple

        output_dict["reviews"] = review_arr

        output_dict["author_following"] = bool(len(self._connection.query("""
            SELECT author_id FROM author_followers
            WHERE author_id={author_id}
                AND user_id={user_id};
        """.format(author_id=output_dict["author_id"], user_id=user_id))))  # Finds all entries with the same user and
        # author id as required, which will either be 1 or 0. If it is 0, the user is not following the author, so the
        # author_following value should be false. If it is 1, they are, so it should be true. Len gets the number of results
        # (1 or 0), and bool converts this to the corresponding boolean value, which is whether the user is following the
        # author.

        return output_dict

    def delete_review(self, review_id, user_id):
        res = self._connection.query("""
            SELECT overall_rating,
                book_id
            FROM reviews
            WHERE review_id={review_id}
                AND user_id={user_id}
        """.format(review_id=review_id, user_id=user_id))[0]
        self._connection.query("""
            DELETE FROM reviews
            WHERE user_id={user_id}
                AND review_id={review_id};
        """.format(user_id=user_id, review_id=review_id))

        return res  # overall rating, book id

    def leave_review(self, user_id, book_id, overall_rating, plot_rating, character_rating, summary, thoughts, list_id):
        params = locals()
        params = {i: "null" if k is None else k for i, k in zip(params.keys(), params.values())}
        #  Convert all None parameters to null for insertion into query.
        if thoughts is not None:
            params["thoughts"] = '"' + re.sub("\n+", "\n", params["thoughts"]) + '"'
            params["summary"] = '"' + params[
                "summary"] + '"'  # There is a check to ensure that 'thoughts' cannot be given
            # without 'summary'.
        self._connection.query("""
            INSERT INTO reviews (user_id, book_id, overall_rating, plot_rating, character_rating, summary, rating_body) VALUES
            ({user_id}, {book_id}, {overall_rating}, {plot_rating}, {character_rating}, {summary}, {rating_body});
        """.format(
            user_id=params["user_id"],
            book_id=params["book_id"],
            overall_rating=params["overall_rating"],
            plot_rating=params["plot_rating"],
            character_rating=params["character_rating"],
            summary=params["summary"],
            rating_body=params["thoughts"]
        ))
        self._reading_lists.add_entry(user_id, list_id, book_id)
    
    def get_highly_rated(self):
        res = self._connection.query("""
            SELECT books.book_id,
            books.title,
            books.cover_image,
            authors.first_name,
            authors.surname,
            authors.alias,
                AVG(reviews.overall_rating) AS average_rating
            FROM books
            INNER JOIN authors ON books.author_id=authors.author_id
            INNER JOIN reviews ON reviews.book_id=books.book_id
            GROUP BY books.book_id
            ORDER BY average_rating DESC;
        """)

        output_dict = dict()
        for i, k in enumerate(res):
            output_dict[i] = {
                "author": authors_mod.names_to_display(k[3], k[4], k[5]),
                "title": k[0],
                "book_id": k[1],
                "cover": k[2],
            }

        return output_dict[:self._number_summaries_home]  # The number of summaries on the genre
        # page should be the same as the layout is the same


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

    recommendations = recommendations_mod.Recommendations(
        connection,
        config.get("books genre_match_threshold"),
        config.get("home number_display_genres"),
        authors_mod.Authors(connection, config.get("books genre_match_threshold"))
    )
    reading_lists = reading_lists_mod.ReadingLists(
        connection,
        config.get("home number_home_summaries"),
        config.get("books genre_match_threshold"),
        config.get("home number_display_genres"),
        recommendations
    )

    books = Books(
        connection,
        reading_lists,
        config.get("books genre_match_threshold"),
        config.get("home number_about_similarities"),
        config.get("home number_home_summaries"),
        config.get("home number_display_genres")
    )