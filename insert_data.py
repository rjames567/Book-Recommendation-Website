import json
import random

from gensim.summarization.summarizer import summarize
from gensim.summarization import keywords


def write_query(string):
    with open("data/data_insert.sql", "a+") as f:
        string = string.replace("\\", r"\\\\")
        f.write(string + "\n\n")
        f.write("-- " + "--" * 100)
        f.write("\n\n")


with open("data/data_insert.sql", "w+") as f:
    pass  # Remove existing data

query = "DELETE FROM reading_lists;\nDELETE FROM book_genres;\nDELETE FROM books;\nDELETE FROM authors;\nDELETE FROM reviews;\nDELETE FROM reading_list_names;\nDELETE FROM sessions;\nDELETE FROM users;"
write_query(query)

# -----------------------------------------------------------------------------
# authors
# -----------------------------------------------------------------------------
new_file = ""
isbn_lookup = dict()

with open("data/Original/metadata.json", "r") as f:
    query = "INSERT INTO authors (author_id, first_name, surname, about) VALUES\n"

    file = f.readlines()

    authors = set()
    for i, line in enumerate(file):
        data = json.loads(line)
        authors.add(data["authors"].split(", ")[0])

    author_lookup = dict()
    for i, k in enumerate(authors):  # Set makes items unique
        if i != 0:
            query += ",\n"
        author_lookup[k] = i + 1
        query += f'({i + 1}, "{k}", "", "")'

    for i, line in enumerate(file):
        data = json.loads(line)
        data["authors"] = author_lookup[data["authors"].split(", ")[0]]
        isbn_lookup[data['item_id']] = i + 1
        new_file += json.dumps(data) + "\n"
    query += ";"
    write_query(query)

with open("data/metadata-altered.json", "w+") as f:
    f.write(new_file)

with open("data/Original/survey_answers.json") as f:
    with open("data/survey_answers.json", "w+") as k:
        for line in f:
            data = json.loads(line)
            try:
                book = isbn_lookup[data["item_id"]]
                data.pop("item_id")
                data["book_id"] = book
                if data["score"] == -1:
                    data["score"] = 0
                k.write(json.dumps(data) + "\n")
            except KeyError:
                pass


del query
del new_file
del f
del author_lookup
del file

# -----------------------------------------------------------------------------
# books
# -----------------------------------------------------------------------------
new_file = ""

with open("data/metadata-altered.json", "r") as f:
    query = "INSERT INTO books (book_id, author_id, title, clean_title, synopsis, cover_image, purchase_link, fiction, release_date, isbn) VALUES\n"
    for i, line in enumerate(f):
        if i != 0:
            query += ",\n"
        data = json.loads(line)
        if type(data['description']) == float:
            synopsis = ""
        else:
            # https://pythonguides.com/remove-unicode-characters-in-python/
            synopsis = data["description"].encode("ascii", "ignore").decode().replace('"', "'").replace(";", "")
        title = data["title"].encode("ascii", "ignore").decode().replace('"', "'")
        query += '({book_id}, {author_id}, "{book_title}", "{clean_title}", "{synopsis}", "{cover_image}", "{link}", true, "{release_date}", "{isbn}")'.format(
            book_id=i + 1,
            author_id=data['authors'],
            book_title=title,
            clean_title="".join([i.lower() for i in title if i.isalnum() or i == " "]),
            synopsis=synopsis.replace('"', "'"),  # .replace("\n", "\\n"),
            cover_image=data['img'],
            link=data['url'],
            release_date=str(data['year']) + "-01-01 " + " 00:00:00",
            isbn=data['item_id']
        )
    query += ";"
    write_query(query)

with open("data/metadata-altered.json", "w+") as f:
    f.write(new_file)

del query
del new_file
del f

# -----------------------------------------------------------------------------
# Users
# -----------------------------------------------------------------------------
query1 = "INSERT INTO users (user_id, username, password_hash, first_name, surname) VALUES\n"
query2 = "INSERT INTO reading_list_names (list_id, user_id, list_name) VALUES\n"
query3 = "INSERT INTO reading_lists (entry_id, list_id, book_id, user_id) VALUES\n"
prev = None
count = 1
for i in range(1, 601):
    if i != 1:
        query1 += ",\n"
        query2 += ",\n"
    query1 += '({num}, "user{num}", "5d557544916fde5c6b162cfcbce84181fb2cbe8798439b643edf96ee4c5826b4", "f{num}", "s{num}")'.format(
        num=i)  # Password is password
    query2 += '({list}, {user}, "Want to Read"),'.format(list=((i - 1) * 3) + 1, user=i)
    query2 += '({list}, {user}, "Currently Reading"),'.format(list=((i - 1) * 3) + 2, user=i)
    query2 += '({list}, {user}, "Have Read")'.format(list=((i - 1) * 3) + 3, user=i)
    available = list(range(1, 501))
    # if i != prev:
    #     query3 += ""
    for k in range(30):
        chance = random.randint(1, 10)
        book = random.choice(available)
        available.remove(book)
        if chance == 1:
            query3 += '({count}, {num}, {book}, {user})'.format(count=count, num=((i - 1) * 3) + 1, book=book, user=i)
            query3 += ",\n"
            count += 1
        elif chance == 2:
            query3 += '({count}, {num}, {book}, {user})'.format(count=count, num=((i - 1) * 3) + 2, book=book, user=i)
            query3 += ",\n"
            count += 1
        elif chance == 3:
            query3 += '({count}, {num}, {book}, {user})'.format(count=count, num=((i - 1) * 3) + 3, book=book, user=i)
            query3 += ",\n"
            count += 1

query1 += ";"
query2 += ";"
query3 = query3[:-2] + ";"
write_query(query1)
write_query(query2)
write_query(query3)

# -----------------------------------------------------------------------------
# Reviews
# -----------------------------------------------------------------------------
query = "INSERT INTO reviews (user_id, book_id, summary, overall_rating, character_rating, plot_rating, rating_body) VALUES\n"
with open("data/reviews.json", "r") as f:
    # https://www.turing.com/kb/5-powerful-text-summarization-techniques-in-python
    prev = None
    available = list(range(1, 601))
    for i, line in enumerate(f):
        #        if i != 0 and len(available) > 1:
        #            query += ",\n"
        while line[-2] != '}':
            line += f.readline()
        data = json.loads(line)
        # https://pythonguides.com/remove-unicode-characters-in-python/
        body = data["txt"].encode("ascii", "ignore").decode().replace('"', "'").replace(";", "")

        if data['item_id'] != prev:
            available = list(range(1, 601))
            prev = data['item_id']

        if body == "":
            body = summary = "null"
        else:
            try:
                summary = summarize(body, word_count=50)
            except ValueError:
                summary = body
                body = "null"

        if len(available):
            user_id = random.choice(available)
            available.remove(user_id)

            overall_rating = random.randint(0, 5)
            if random.randint(0, 1):
                character_rating = random.randint(0, 5)
            else:
                character_rating = "null"
            if random.randint(0, 1):
                plot_rating = random.randint(0, 5)
            else:
                plot_rating = "null"
            query += '({user_id}, {book_id}, "{summary}", {overall_rating}, {character_rating}, {plot_rating}, "{rating_body}")'.format(
                user_id=user_id,
                book_id=data['item_id'],
                summary=summary,
                overall_rating=overall_rating,
                character_rating=character_rating,
                plot_rating=plot_rating,
                rating_body=body  # .replace("\n", "\\n")
            )
            query += ",\n"
    query = query[:-2] + ";"
    write_query(query)