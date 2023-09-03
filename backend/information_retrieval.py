# -----------------------------------------------------------------------------
# Standard Python ibrary imports
# -----------------------------------------------------------------------------
import itertools

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import configuration
import mysql_handler

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------
def clean_data(string):
    return "".join([i.lower() for i in string if i.isalnum() or i == " "])


# -----------------------------------------------------------------------------
# Objects
# -----------------------------------------------------------------------------
class DocumentCollection:
    def __init__(self, connection):
        self._connection = connection
    
    def gen_unique_words(self):
        words = list(itertools.chain(*[i[0].split(" ") for i in self._connection.query("SELECT clean_title FROM books")]))
        words.append(list(itertools.chain(*[i[0].split() for i in self._connection.query("SELECT clean_name FROM authors")])))
        words.append(list(itertools.chain(*[i[0].split() for i in self._connection.query("SELECT clean_name from genres")])))

        unique_words = set(list(itertools.chain(*words)))

        self._connection.query("DELETE FROM unique_words")
        values = ""

        for i in unique_words:
            if i != "":
                if values != "":
                    values += ","
                values += f'("{i}")'
        
        self._connection.query(x:=f"INSERT INTO unique_words (word) VALUES {values}")

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

    document = DocumentCollection(connection)
    document.gen_unique_words()