# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import time

# ------------------------------------------------------------------------------
# Third party Python library imports
# ------------------------------------------------------------------------------
import mysql.connector

# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------
class Connection:
    """
    Database connection class. Encapsulates the complexity of connecting to the
    database, including error handling, into a single class, to make queries
    more readable and simpler to make.
    """
    def __init__(self, user, password, schema, host):
        """
        Constructor for the Connection class

        Establishes the connection to the database.

        user -> string
            The identifying username for the database that the connection should
            use. Change for different levels of database permissions.
            Administrator priviledges are not recommended, as major,
            irreversable alterations are easy to make.

        password -> string
            The corresponding password to the username, to establish the
            database connection.

        schema -> string
            The database at the host that is to be connected to.

        host -> string
            The host IP address or host name for the server to connect to.

        Does not have a return value.
        """
        self._user = user
        self._password = password
        self._schema = schema
        self._host = host
        self._connect() # Establish database connection
        self._query_time = None

    def _connect(self):
        """
        Method to establish a database connection. Called when an object is
        instantiated and whenever a query is made, and the database has
        terminated the connection.

        Does not have a return value.
        """
        self._connection = mysql.connector.connect(
            user=self._user,
            password=self._password,
            host=self._host,
            database=self._schema
        )

        self._cursor = self._connection.cursor()

    def query(self, query):
        """
        Method to query the connected database.

        query -> string
            The MySQL query that is to be performed on the database that the
            object is connecting to.

        Returns a list of tuples - each tuple is one row in the response from
        the database. An empty list means that the query result was an empty
        set.
        """

        start_time = time.time() # Changes this first incase multi-threading is
            # used in the future - a query may be made in a different thread.
        self._query_time = None

        try:
            self._cursor.execute(query)
        except mysql.connector.Error:
            self._connect() # Some databases specifies connections close after
                # certain amount of time inactive. This repoens the connection
                # if a timeout occurs

        try:
            result = self._cursor.fetchall() # Needs to come before the if
                # statement as otherwise can result in 'unread result found' error
        except mysql.connector.errors.InterfaceError:
            result = [] # Incase the method does not provide any result, like
                # INSERT

        self._connection.commit() # Applies changes from the query to the db

        self._query_time = time.time() - start_time

        return result # Use tuples as they are faster


    @property
    def query_time(self):
        """
        Getter method for the query time of the previous query.

        Time includes processing within the class, such as committing changes.

        Returns a floating point number for the time in seconds of the previous
        query, or None if a query has not yet been made, or there is one in
        progress.
        """
        return self._query_time

    def __del__(self):
        """
        Custom destructor for the connection class. Closes the connection with
        the databse whenever the program is terminated or the instance is
        deleted manually.

        Does not have a return value
        """
        self._connection.close()