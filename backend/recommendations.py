# -----------------------------------------------------------------------------
# Project imports
# -----------------------------------------------------------------------------
import configuration
import ml_utilities
import mysql_handler

# -----------------------------------------------------------------------------
# Recommendations
# -----------------------------------------------------------------------------
class Recommendations:
    def __init__(self, connection):
        self._connection = connection

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

    recommendations = Recommendations(connection)