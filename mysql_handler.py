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
    def __init__(self, user, password, database_schema, host):
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
        
        database_schema -> string
            The database at the host that is to be connected to.
        
        host -> string
            The host IP address or host name for the server to connect to.
        
        Does not have a return value.
        """
        self._user = user
        self._password = password
        self._schema = database_schema
        self._host = host
        self._connect() # Establish database connection
    
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
    
    def query(self, query, testing=False):
        """
        Method to query the connected database.
        
        query -> string
            The MySQL query that is to be performed on the database that the
            object is connecting to.
        
        
        testing -> boolean
            Specifies whether the query is for testing. If it is, any errors
            from the query still occur, but any changes to the database are not
            applied if is True.
            
            Defaults to False.
        
        Returns a list of tuples - each tuple is one row in the response from
        the database. An empty list means that the query result was an empty 
        set.
        """
        try:
            self._cursor.execute(query)
        except mysql.connectorError:
            self._connect() # Some databases specifies connections close after
                # certain amount of time inactive. This repoens the connection
                # if a timeout occurs
        
        if not testing: # If it is testing, it has does not affect the db
            self._connection.commit() # Applies changes from the query to the db

        return self._cursor.fetchall()
    
    def __del__(self):
        """
        Custom destructor for the connection class. Closes the connection with
        the databse whenever the program is terminated or the instance is 
        deleted manually.
        
        Does not have a return value
        """
        self._connection.close()