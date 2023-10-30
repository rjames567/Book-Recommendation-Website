# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import re
import os


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

    def __init__(self, filename, default_dict={}):
        """
        Constructor for the Configuration class.

        filename -> string
            Specifies the configuration file. This can be either an absolute or
            relative file path.

        Does not have a return value
        """
        self._filepath = os.path.join(os.path.split(os.path.dirname(__file__))[0], filename)
        self.load()
        self._default_config = default_dict

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

    def load(self):
        """
        Method to load the configuration file, and convert it into a dictionary.

        Does not have a return value
        """
        with open(self._filepath, "r") as f:
            contents = f.readlines()

        hierarchy = {}
        heading = None

        for line_num, line in enumerate(contents):
            heading_re = re.match("(\w+):\s*", line)
            if heading_re:
                heading = heading_re.group(1).lower()
                hierarchy[heading] = {}
            else:
                entry_re = re.match("\t|\s{4}(\w+)\s+([\w-]+)\s*:\s*(.+)", line)
                if heading is not None:
                    if entry_re:
                        hierarchy[heading][entry_re.group(1).lower()] = self._cast_to_type(
                            entry_re.group(2).lower(),
                            entry_re.group(3),
                            line_num + 1
                        )
                    else:
                        heading = None
                else:
                    external_re = re.match("(\w+)\s+([\w-]+)\s*:\s*(.+)", line)
                    if external_re:
                        hierarchy[external_re.group(1).lower()] = self._cast_to_type(
                            external_re.group(2).lower(),
                            external_re.group(3),
                            line_num + 1
                        )
                    elif not (re.match("\s*", line)):
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
        query_string = query_string.lower()

        query_arr = query_string.split()
        if query_arr[0] in self._file_config.keys():
            res = self._file_config[query_arr[0]]
            if len(query_arr) == 2:
                if query_arr[1] in res.keys():
                    res = res[query_arr[1]]
                else:
                    raise ConfigVariableNotFound(query_string, self._filepath)
        elif query_arr[0] in self._default_config.keys():
            res = self._default_config[query_arr[0]]
            if len(query_arr) == 2:
                if query_arr[1] in res.keys():
                    res = res[query_arr[1]]
                else:
                    raise ConfigVariableNotFound(query_string, self._filepath)
        else:
            raise ConfigVariableNotFound(query_string, self._filepath)
        return res  # TODO make this faster by making this part a direct dictionary lookup

# Similar to YAML - but with more datatypes - binary strings
