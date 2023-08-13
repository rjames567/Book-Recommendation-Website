import json

def write_query(string):
    with open("data_insert.sql", "a+") as f:
        string = string.replace("\\", r"\\\\")
        f.write(string + "\n\n")
        f.write("-- " + "--" * 100)
        f.write("\n\n")
        
with open("data_insert.sql", "w+") as f:
    pass  # Remove existing data

query = "DELETE FROM reading_lists;\nDELETE FROM book_genres;\nDelete FROM books;\nDELETE FROM authors;"
write_query(query)

# -----------------------------------------------------------------------------
# authors
# -----------------------------------------------------------------------------
new_file = ""

isbn_lookup = dict()

with open("Original/metadata.json", "r") as f:
    query = "INSERT INTO authors (author_id, first_name, surname, about) VALUES\n"

    file = f.readlines()

    authors = set()
    for i, line in enumerate(file):
        data = json.loads(line)
        authors.add(data["authors"].split(", ")[0])

    author_lookup = dict()
    for i, k in enumerate(authors): # Set makes items unique
        if i != 0:
            query += ",\n"
        author_lookup[k] = i+1
        query += f'({i+1}, "{k}", "", "")'
    
    for i, line in enumerate(file):
        data = json.loads(line)
        data["authors"] = author_lookup[data["authors"].split(", ")[0]]
        isbn_lookup[data['item_id']] = i+1
        new_file += json.dumps(data) + "\n"
    query += ";"
    write_query(query)

with open("metadata.json", "w+") as f:
    f.write(new_file)

del query
del new_file
del f
del author_lookup
del file

# -----------------------------------------------------------------------------
# books
# -----------------------------------------------------------------------------
new_file = ""

with open("Original/metadata.json", "r") as f:
    query = "INSERT INTO books (book_id, author_id, title, clean_title, synopsis, cover_image, purchase_link, fiction, release_date, isbn) VALUES\n"
    for i, line in enumerate(f):
        if i != 0:
            query += ",\n"
        data = json.loads(line)
        if type(data['description']) == float:
            synopsis = ""
        else:
            # https://pythonguides.com/remove-unicode-characters-in-python/
            synopsis = data["description"].encode("ascii", "ignore").decode().replace('"', "'")
        title = data["title"].encode("ascii", "ignore").decode().replace('"', "'")
        query += '({book_id}, {author_id}, "{book_title}", "{clean_title}", "{synopsis}", "{cover_image}", "{link}", true, "{release_date}", "{isbn}")'.format(
            book_id = i+1,
            author_id = data['authors'],
            book_title = title,
            clean_title = "".join([i.lower() for i in title if i.isalnum() or i == " "]),
            synopsis = synopsis.replace('"', "'"),
            cover_image = data['img'],
            link = data['url'],
            release_date = str(data['year']) + "-01-01 " + " 00:00:00",
            isbn = data['item_id']
        )
    query += ";"
    write_query(query)

with open("metadata.json", "w+") as f:
    f.write(new_file)

del query
del new_file
del f

new_file = ""
with open("reviews.json", "w+") as fout:
    with open("Original/reviews.json", "r") as f:
        for i, line in enumerate(f):
            if i % 10 == 0:
                try:
                    data = json.loads(line)
                    book_id = isbn_lookup[data['item_id']]
                    data['item_id'] = book_id
                    fout.write(json.dumps(data) + "\n")
                except KeyError:
                    pass