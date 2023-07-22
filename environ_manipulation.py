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

        Example path: /
            Adds TARGET_APPLICATION, with value None.

        Modifies the environ dictionary, and adds "TARGET_APPLICATION" to it.
        This can be accessed directly, and does not need to be reassigned.

        Does not have a return value
        """
        path = environ["REQUEST_URI:"]
        temp = re.match("/[\w-]+/([\w-]+)", path)  # Should not include dashes in result, but included, so it does
        # not break if it does.
        if temp:
            target = temp.group(1)
        else:
            target = None
        environ["TARGET_APPLICATION"] = target  # Will change the dictionary
        # passed.

    def add_sub_target(environ):
        """
        Modifies the environ dictionary given when using WSGI, to contain the
        target process within the sub application, as dictated by the second
        part of the URI.

        Example path: /application_name/sub_process/
            Adds APPLICATION_PROCESS, with value sub_process

        Example path: /application_name/
            Adds APPLICATION_PROCESS, with value None.

        Modifies the environ dictionary, and adds "APPLICATION_PROCESS" to it.
        This can be accessed directly, and does not need to be reassigned.

        Does not have a return value
        """
        path = environ["REQUEST_URI:"]
        temp = re.match("/[\w-]+/[\w-]+/([\w-]+)", path)  # Should not
        # include dashes in result, but included, so it does not break if it
        # does.
        if temp:
            sub = temp.group(1)
        else:
            sub = None
        environ["APPLICATION_PROCESS"] = sub
