# -----------------------------------------------------------------------------
# Python Imports
# -----------------------------------------------------------------------------
import random

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import ml_utilities

# -----------------------------------------------------------------------------
# Book Data
# -----------------------------------------------------------------------------
genres = {
    1: 'Genre 1',
    2: 'Genre 2',
    3: 'Genre 3',
    4: 'Genre 4',
    5: 'Genre 5',
    6: 'Genre 6',
    7: 'Genre 7',
    8: 'Genre 8',
    9: 'Genre 9',
    10: 'Genre 10',
    11: 'Genre 11',
    12: 'Genre 12',
    13: 'Genre 13',
    14: 'Genre 14',
    15: 'Genre 15',
    16: 'Genre 16',
    17: 'Genre 17',
    18: 'Genre 18',
    19: 'Genre 19',
    20: 'Genre 20'
}

# books = {k: list(set(random.choice(list(genres.keys())) for i in range(random.randint(1, 20)))) for k in range(1, 20)}

books = {
    1: [19, 11, 20, 6, 3, 12, 16, 13],
    2: [4, 3, 7, 0, 8, 13, 15, 2, 20],
    3: [1, 19, 17, 11, 5, 7, 2, 18],
    4: [13, 1, 16, 18, 19],
    5: [15, 20, 5, 2, 11, 4, 3, 18, 9, 1],
    6: [10, 9, 13, 20, 8, 5],
    7: [16, 8, 4, 5, 18, 13, 19, 7, 3, 9],
    8: [2, 7, 10, 3, 1, 19, 9, 15, 13],
    9: [6, 5, 2, 10, 8, 16, 4],
    10: [15, 8, 3, 12, 13, 17, 7, 11, 14],
    11: [13, 12, 5, 9, 16, 4, 6, 19],
    12: [14, 1, 8, 9, 5, 10, 7, 18],
    13: [2, 8, 17, 15, 7, 14, 10],
    14: [3, 13, 7, 10, 11, 9, 14],
    15: [10, 13, 11, 14, 16, 6, 8],
    16: [1, 15, 16, 10, 3, 18, 19, 12],
    17: [7, 2, 19, 14, 3, 1],
    18: [16, 19, 11, 17, 1, 4, 9, 10, 13],
    19: [14, 19, 1, 9, 16, 13, 6, 4, 2],
    20: [4, 10, 13, 16, 2, 17, 19, 18, 5]
}

# users = {k: list(set(random.choice(list(genres.keys())) for i in range(random.randint(5, 15)))) for k in range(1, 31)}

# print("users = {")
# for i in users:
#     print(f"    {i}: [{', '.join(str(i) for i in users[i])}],")
# print("}")

users = {
    1: [3, 4, 5, 6, 8, 11, 13, 15, 20],
    2: [2, 3, 12, 13, 14, 15, 17],
    3: [2, 5, 6, 7, 11, 13, 14, 16, 17],
    4: [1, 2, 3, 5, 6, 10, 13, 14, 19],
    5: [1, 2, 7, 9, 10, 11, 12, 13, 14, 15, 16, 19, 20],
    6: [1, 2, 3, 4, 11, 12, 16, 19],
    7: [2, 5, 7, 9, 11, 12, 13, 17, 18, 19],
    8: [6, 10, 11, 13, 15, 16, 17, 19],
    9: [1, 2, 3, 4, 6, 9, 16, 19],
    10: [3, 4, 5, 7, 9, 11, 12, 13, 14, 16, 18, 19, 20],
    11: [1, 2, 4, 6, 7, 10, 11, 12, 13, 15, 16],
    12: [1, 6, 9, 12, 13, 15, 17, 18, 19],
    13: [1, 2, 3, 6, 13, 14, 15],
    14: [2, 7, 8, 11, 12, 16, 18, 19],
    15: [1, 2, 5, 9, 10, 12, 14, 17, 18],
    16: [2, 3, 4, 5, 7, 9, 13, 18, 19],
    17: [1, 2, 4, 5, 6, 7, 10, 12, 16, 18, 19, 20],
    18: [1, 3, 5, 8, 10, 11, 19, 20],
    19: [1, 2, 5, 6, 8, 9, 14, 16, 18, 20],
    20: [6, 9, 13, 16, 17, 18, 19],
    21: [2, 3, 9, 10, 11, 12, 15, 18],
    22: [4, 6, 9, 11, 13, 16, 20],
    23: [2, 7, 8, 12, 13, 16, 18],
    24: [2, 6, 7, 8, 9, 10, 13, 14, 17, 18, 19],
    25: [2, 3, 4, 8, 9, 10, 14, 15, 17, 18, 20],
    26: [1, 5, 7, 9, 10, 11, 15, 17, 18],
    27: [1, 4, 7, 11, 12, 13, 14, 18, 19],
    28: [1, 2, 3, 5, 6, 7, 11, 17, 19, 20],
    29: [2, 9, 13, 15, 16, 19],
    30: [2, 4, 5, 10, 14, 18, 19],
}


# -----------------------------------------------------------------------------
# Output data
# -----------------------------------------------------------------------------
def output_data():
    print("Genres")
    for i in genres:
        num = str(i) + ":"
        if i % 2 == 0:
            output = "\n"
            if i / 10 < 1:
                num += " "    
            num += " "
        elif i / 10 >= 1:
            output = "    "
        else:
            output = "     "
            num += " "

        print(f"{num}   {genres[i]}{output}", end="")
        

    print("\n\nBook Genres")
    for i in books:
        num = str(i) + ":"
        if i / 10 < 1:
            num += " "
        print(f"{num}   {', '.join(str(i) for i in sorted(books[i]))}")


    print("\n\nUser Genres")
    for i in users:
        num = str(i) + ":"
        if i / 10 < 1:
            num += " "
        print(f"{num}   {', '.join(str(i) for i in users[i])}")
    print("\n\n\n")


# -----------------------------------------------------------------------------
# Data processing
# -----------------------------------------------------------------------------
def books_to_matched_genre_list():
    res = dict()
    for i in books:
        genres_list = books[i]
        arr = []
        for k in genres:
            if k in genres_list:
                arr.append(1)
            else:
                arr.append(0)
        res[i] = arr
    return res

def users_to_matched_genre_list():
    res = dict()
    for i in users:
        genres_list = users[i]
        arr = []
        for k in users:
            if k in genres_list:
                arr.append(1)
            else:
                arr.append(0)
        res[i] = arr
    return res

# -----------------------------------------------------------------------------
# Content-based filtering
# -----------------------------------------------------------------------------
def content_recommend(user):
    user_preference = users_to_matched_genre_list()[user]
    book_data = books_to_matched_genre_list()

    weightings = []
    for i in book_data:
        book_genres = book_data[i]
        weightings.append({
            "id": i,
            "dot_product": ml_utilities.dot_product(book_genres, user_preference) # Order does not matter
        })
    
    return [i["id"] for i in sorted(weightings, key=lambda x: x["dot_product"], reverse=True)][:10]