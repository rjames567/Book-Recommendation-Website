# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import re
import os
import json

# ------------------------------------------------------------------------------
# Custom exceptions
# ------------------------------------------------------------------------------
class ConfigInvalidDataForType(Exception):
    """
    Exception for when a value in the configuration file is specified, but
    cannot be cast to the specified variable type.
    """

    def __init__(self, datatype, value, line):
        message = f"Error at line {line}: '{value}' is not a valid {datatype}"
        super().__init__(message)


class ConfigInvalidDataTypeError(Exception):
    """
    Exception for when a datatype is specified in the configuration file that is
    not known to the Configuration class.
    """

    def __init__(self, datatype, line):
        message = f"Error at line {line}: '{datatype}' datatype is not known"
        super().__init__(message)


class ConfigIndentationError(Exception):
    """
    Exception for when there is an unexpected indent in the config file.

    Note that missing indentation will not raise errors, as it is impossible to
    tell whether that the lack of indentation is intentional.
    """

    def __init__(self, line):
        message = f"Error at line {line}: Unexpected Indentation"
        super().__init__(message)


class ConfigVariableNotFound(Exception):
    """
    Exception for when a variable is requested from the configuration file
    associated with the configuration instance, but is not found in the file.
    """

    def __init__(self, variable, file):
        message = f"Configuration file '{file}' does not contain the variable '{variable}'"
        super().__init__(message)


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------
class Configuration:
    """
    Configuration class which handles the loading and requesting of data from
    the configuration file which is passed in.
    """

    def __init__(self, filename, default_conf_filename=None):
        """
        Constructor for the Configuration class.

        filename -> string
            Specifies the configuration file. This can be either an absolute or
            relative file path.

        Does not have a return value
        """
        self._filepath = os.path.join(os.path.split(os.path.dirname(__file__))[0], filename)
        # Needs to go back a directory, as this is in a folder that is further into the filesystem that the configuration files
        if default_conf_filename is not None:
            self._default_filepath = os.path.join(os.path.split(os.path.dirname(__file__))[0], default_conf_filename)
        else:
            self._default_filepath = None
        self. _load()

    def _cast_to_type(self, datatype, value, line_num):
        """
        Method to convert a string to any specified datatype, using the acronym
        which is in the configuration file.

        datatype -> string
            The acronym for the datatype that is included in the configuration
            file

        value -> string
            The value that is to be cast to a different data type

        line_num -> integer
            The line number in the configuration file where the datatype is
            specified

        Returns a value, which is the same as that specified by the datatype
        parameter.
        """
        if datatype == "int":
            try:
                return int(value)
            except ValueError:
                raise ConfigInvalidDataForType(datatype, value, line_num)
        elif datatype == "str":
            try:
                return str(value)
            except ValueError:
                raise ConfigInvalidDataForType(datatype, value, line_num)
        elif datatype == "float":
            try:
                return float(value)
            except ValueError:
                raise ConfigInvalidDataForType(datatype, value, line_num)
        elif datatype == "bin-str":
            try:
                return value.encode("utf-8")
            except ValueError:
                raise ConfigInvalidDataForType(datatype, value, line_num)
        elif datatype == "bool":
            if value == "true":
                return True
            elif value == "false":
                return False
            else:
                raise ConfigInvalidDataForType(datatype, value, line_num)
        else:
            raise ConfigInvalidDataTypeError(datatype, line_num)
        # Case statement to switch the datatype. Uses if-else as the switch
        # statement cannot be used in the required python version.

    def  _load(self):
        """
        Method to load the configuration file, and convert it into a dictionary.

        Does not have a return value
        """
        with open(self._filepath, "r") as f:  # Implicitly closes the file after opening. Opens as read only
            contents = f.readlines()

        if self._default_filepath is not None:
            with open(self._default_filepath, "r") as f:
                hierarchy = json.loads(f.readline())  # Load the json from the file and creeate dictionary with it.
                # This is the default values. They will be overwritten as needed.
        else:
            hierarchy = {}

        heading = ""  # No header as an empty string
        for line_num, line in enumerate(contents):
            heading_re = re.match("(\w+):\s*", line)  # Match headers in the line
            if heading_re:  # Runs if there is a match to a heading
                heading = heading_re.group(1).lower() + " "  # .lower ensures case insensitivity
            else:
                entry_re = re.match("\t|\s{4}(\w+)\s+([\w-]+)\s*:\s*(.+)", line)  # Match indented records in line
                if heading != "":  # If it is, it should be indented
                    if entry_re:
                        string = heading + entry_re.group(1)
                        hierarchy[string.lower()] = self._cast_to_type(
                            entry_re.group(2).lower(),
                            entry_re.group(3),
                            line_num + 1
                        )  # Change the datatype to the specified one
                    else:  # There must be an unindented record, so it removes the header
                        heading = ""
                if heading == "":
                    external_re = re.match("(\w+)\s+([\w-]+)\s*:\s*(.+)", line)  # Match unindented records in line
                    if external_re:
                        hierarchy[external_re.group(1).lower()] = self._cast_to_type(
                            external_re.group(2).lower(),
                            external_re.group(3),
                            line_num + 1  # Increments the line number by 1 to give the line number of the exception    
                        )
                    elif not (re.match("\s*", line)):   # If there is no header, and there is non-space characters on the
                        # line, it must be invalid indentation
                        raise ConfigIndentationError(line_num + 1)
        self._file_config = hierarchy

    def get(self, query_string):
        """
        Method to get a specific variable from the configuration file.

        query_string -> string
            String to specify which variable to retrieve:
                Header Variable
                or
                Variable

        Note that it is not case-sensitive

        Returns the value stored in the specified variable, with the specified
        datatype.
        """
        query_string = query_string.lower()  # Prevent case sensitivity

        if query_string in self._file_config.keys():  # Avoids needing the try-catch statement - is faster
            return self._file_config[query_string]
        else:
            raise ConfigVariableNotFound(query_string, self._filepath)  # Raises exception if it does not exist

# Similar to YAML - but with more datatypes - binary strings
