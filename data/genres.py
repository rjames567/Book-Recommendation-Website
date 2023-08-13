import json

with open("tags.json", "r") as f:
    with open("genres.sql", "w+") as k:
        k.write("INSERT INTO genres (genre_id, name, about) VALUES\n")
        for i, line in enumerate(f):
            if i != 0:
                k.write(",\n")
            data = json.loads(line)
            k.write('({id}, "{tag}", "This genre does not have an about")'.format(id=data["id"] + 1, tag=data["tag"].replace('"', "'")))
        k.write(";")