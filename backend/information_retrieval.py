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
        self.gen_tf_values()
        self._idf_values = None

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
    
    def gen_tf_values(self, term=None):
        if term is None:
            for count, document in enumerate(self._documents_dict):
                tf = dict()
                arr = document["words"].split(" ")
                one_over_n = 1 / len(arr)
                for i in arr:
                    if i != " ":
                        if i in tf:
                            tf[i] += one_over_n
                        else:
                            tf[i] = one_over_n
                self._documents_dict[count]["tf"] = tf
        else:
            arr = term.split(" ")
            tf = dict()
            one_over_n = 1 / len(arr)
            for word in arr:
                if word != " ":
                    if word in tf:
                        tf[word] += one_over_n
                    else:
                        tf[word] = one_over_n
            return tf
    
    def num_documents_containing(self, string):
        return sum(string in i for i in self._documents)

    def gen_idf_values(self):
        num_documents = len(self._documents)
        self._idf_values = dict()
        for word_id, word in self._connection.query("SELECT word_id, word FROM unique_words"):
            idf = math.log10(num_documents / self.num_documents_containing(word))
            self._connection.query("""
                UPDATE unique_words
                    SET idf_values={idf}
                WHERE word_id={word_id}
            """.format(
                idf=idf,
                word_id=word_id
            ))

            self._idf_values[word] = idf
    
    @property
    def idf_values(self):
        if self._idf_values is not None: # Should be faster as it only needs to be fetched from the DB once
            return self._idf_values
        else:
            self._idf_values = dict()
            for word, idf in self._connection.query("""SELECT word, idf_values FROM unique_words"""):
                self._idf_values[word] = idf
            return self._idf_values
    
    def gen_tfidf_values(self, document=None, search_terms=None):
        if document is None:
            for count, document in enumerate(self._documents_dict):
                document_words = document["words"].split(" ")
                if search_terms is None:
                    new_search_terms = document_words
                else:
                    new_search_terms = search_terms
                
                res = {i: 0 for i in new_search_terms}
                for i in res.keys():
                    if i in self.idf_values and i in document_words:
                        res[i] = document["tf"][i] * self.idf_values[i]
                
                self._documents_dict[count]["tfidf"] = res
        else:
            document_words = document.split(" ")
            tf = self.gen_tf_values(document)
            res = {i: 0 for i in document_words}
            for i in res.keys():
                if i in self.idf_values and i in document_words:
                    res[i] = tf[i] * self.idf_values[i]
            return res

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

    document.gen_tfidf_values()
