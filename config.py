# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import re

# ------------------------------------------------------------------------------
# Custom exceptions
# ------------------------------------------------------------------------------
class ConfigInvalidDataForType (Exception):
    def __init__(self, datatype, value, line):
        message = f"Error at line {line}: '{value}' is not a valid {datatype}"
        super().__init__(message)

class ConfigInvalidDataTypeError (Exception):
    def __init__(self, datatype, line):
        message = f"Error at line {line}: '{datatype}' datatype is not known"
        super().__init__(message)

# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------
class Config:
    def __init__(self, filename):
        self._filename = filename

    def _cast_to_type(self, datatype, value, line_num):
        match datatype:
            case "int":
                try:
                    return int(value)
                except ValueError:
                    raise ConfigInvalidDataForType(datatype, value, line_num)
            case "str":
                try:
                    return str(value)
                except ValueError:
                    raise ConfigInvalidDataForType(datatype, value, line_num)
            case "float":
                try:
                    return float(value)
                except ValueError:
                    raise ConfigInvalidDataForType(datatype, value, line_num)
            case "bin-str":
                try:
                    return value.encode("utf-8")
                except ValueError:
                    raise ConfigInvalidDataForType(datatype, value, line_num)
            case "bool":
                if value == "true":
                    return True
                elif value == "false":
                    return False
                else:
                    raise ConfigInvalidDataForType(datatype, value, line_num)
            case _:
                raise ConfigInvalidDataTypeError(datatype, line_num)