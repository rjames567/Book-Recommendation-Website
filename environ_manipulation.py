# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import re

# ------------------------------------------------------------------------------
# Application manipulation
# ------------------------------------------------------------------------------
class application:
    def add_target(environ):
        path = environ["PATH_INFO"]
        application = re.match("/[a-z-]+/([a-z-]+)", path).group(1) # Should not
            # include dashes in result, but included so it does not break if it
            # does.
        environ["TARGET_APPLICATION"] = application # Will change the dictionary
            # passed.