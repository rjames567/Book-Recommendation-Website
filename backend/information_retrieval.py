# -----------------------------------------------------------------------------
# Standard Python ibrary imports
# -----------------------------------------------------------------------------
import enum
import itertools
import math

# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import configuration
import mysql_handler


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------
class DocumentType(enum.Enum):
    AUTHOR = enum.auto
    GENRE = enum.auto
    BOOK = enum.auto

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
        self.load_documents_dict()

    def load_documents_dict(self):
        self._documents_dict = []
        self._documents = []
        for k in [i[0] for i in self._connection.query("SELECT clean_title FROM books")]:
            self._documents_dict.append({
                "type": DocumentType.BOOK,
                "words": k
            })
            self._documents.append(k)
        
        for k in [i[0] for i in self._connection.query("SELECT clean_name FROM genres")]:
            self._documents_dict.append({
                "type": DocumentType.GENRE,
                "words": k
            })
            self._documents.append(k)
        
        for k in [i[0] for i in self._connection.query("SELECT clean_name FROM authors")]:
            self._documents_dict.append({
                "type": DocumentType.AUTHOR,
                "words": k
            })
            self._documents.append(k)

    def gen_unique_words(self):
        words = list(itertools.chain(*[i["words"].split(" ") for i in self._documents_dict]))

        unique_words = set(words)

        self._connection.query("DELETE FROM unique_words")
        values = ""

        for i in unique_words:
            if i != "":
                if values != "":
                    values += ","
                values += f'("{i}")'
        
        self._connection.query(x:=f"INSERT INTO unique_words (word) VALUES {values}")
    
    def num_documents_containing(self, string):
        return sum(string in i for i in self._documents)

    def gen_idf_values(self):
        num_documents = len(self._documents)

        for word_id, word in self._connection.query("SELECT word_id, word FROM unique_words"):
            self._connection.query("""
                UPDATE unique_words
                    SET idf_values={idf}
                WHERE word_id={word_id}
            """.format(
                idf=math.log10(num_documents / self.num_documents_containing(word)),
                word_id=word_id
            ))

    
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
