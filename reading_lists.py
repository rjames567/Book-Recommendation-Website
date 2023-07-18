# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
import configuration
import data_structures
import mysql_handler

# ------------------------------------------------------------------------------
# Instantiating import classes
# ------------------------------------------------------------------------------
config = configuration.Configuration("project_config.conf")
connection = mysql_handler.Connection(
    user=config.get("mysql username"),
    password=config.get("mysql password"),
    schema=config.get("mysql schema"),
    host=config.get("mysql host")
)

# ------------------------------------------------------------------------------
# List names
# ------------------------------------------------------------------------------
def get_names(user_id):
    res = connection.query(
        """
        SELECT list_name from reading_list_names
        WHERE user_id={};
        """.format(user_id)
    ) # List of single element tuples
    output_queue = data_structures.Queue()
    for i in res:
        output_queue.push(i[0]) # i is a single element tuple

    return output_queue