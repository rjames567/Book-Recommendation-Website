import os
import json
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import backend.configuration
import backend.mysql_handler

config = backend.configuration.Configuration("./project_config.conf")
connection = backend.mysql_handler.Connection(
    user=config.get("mysql username"),
    password=config.get("mysql password"),
    schema=config.get("mysql schema"),
    host=config.get("mysql host")
)

connection.query("""DROP TABLE IF EXISTS temp;""")
connection.query("""DELETE FROM book_genres;""")
connection.query("""CREATE TABLE temp (genre_id INT, score INT, book_id INT);""")

query = "INSERT INTO temp VALUES\n"
with open("survey_answers.json", "r") as f:
    for i, line in enumerate(f):
        if i != 0:
            query += ",\n"
        data = json.loads(line)
        query += '({tag}, {score}, {book})'.format(tag=data["tag_id"]+1, score=data["score"], book=data["book_id"]*2)
query += ";"

connection.query(query)

books = [i[0] for i in connection.query("SELECT book_id FROM books")]
query = "INSERT INTO book_genres (genre_id, book_id, match_strength) VALUES\n"
for j, i in enumerate(books):
    res = connection.query("""SELECT genre_id,
        AVG(score)/5 AS rating
        FROM temp
        WHERE book_id={}
        GROUP BY genre_id;
    """.format(i))

    for b, k in enumerate(res):
        if k[1] > 0:
            query += f"({k[0]}, {i}, {float(k[1])}),\n"
query = query[:-2] + ";"

connection.query(query)
        
connection.query("""DROP TABLE temp""")