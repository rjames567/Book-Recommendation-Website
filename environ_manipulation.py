# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import re

# ------------------------------------------------------------------------------
# Application manipulation
# ------------------------------------------------------------------------------
class application:
    def add_target(environ):
        """
        Modifies the environ dictionary given when using WSGI, to contain the
        target sub application, as dictated by the first part of the URI.

        Example path: /application_name/sub_process
            Adds TARGET_APPLICATION, with value application_name

        Modifies the environ dictionary, and adds "TARGET_APPLICATION" to it.
        This can be accessed directly, and does not need to be reassigned.

        Does not have a return value
        """
        path = environ["PATH_INFO"]
        application = re.match("/[\w-]+/([\w-]+)", path).group(1) # Should not
            # include dashes in result, but included so it does not break if it
            # does.
        environ["TARGET_APPLICATION"] = application # Will change the dictionary
            # passed.