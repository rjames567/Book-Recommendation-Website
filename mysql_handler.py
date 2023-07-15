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
        self._connection = mysql.connector.connect(
            user=self._user,
            password=self._password,
            host=self._host,
            database=self._schema
        )
        
        self._cursor = self._connection.cursor()
    
    def __del__(self):
        self._connection.close()