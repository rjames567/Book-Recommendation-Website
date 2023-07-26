# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import re


# ------------------------------------------------------------------------------
# Application manipulation
# ------------------------------------------------------------------------------
class application():
    def get_target(environ):
        """
        Modifies the environ dictionary given when using WSGI, to contain the
        target sub application, as dictated by the first part of the URI.

        Example path: /application_name/sub_process
            Returns application_name

        Example path: /
            Returns None.

        Returns the target name, if applicable, as a string, otherwise it
        returns None
        """
        path = environ["REQUEST_URI"]
        temp = re.match("/[\w-]+/([\w-]+)", path)  # Should not include dashes in result, but included, so it does
        # not break if it does.
        if temp:
            return temp.group(1)
        return None

    def get_sub_target(environ):
        """
        Modifies the environ dictionary given when using WSGI, to contain the
        target process within the sub application, as dictated by the second
        part of the URI.

        Example path: /application_name/sub_process
            Returns sub_process

        Example path: /
            Returns None.

        Returns the target name, if applicable, as a string, otherwise it
        returns None
        """
        path = environ["REQUEST_URI"]
        temp = re.match("/[\w-]+/[\w-]+/([\w-]+)", path)  # Should not
        # include dashes in result, but included, so it does not break if it
        # does.
        if temp:
            return temp.group(1)
        return None