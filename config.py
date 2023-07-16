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

class ConfigIndentationError (Exception):
    def __init__(self, line):
        message = f"Error at line {line}: Unexpected Indentation"
        super().__init__(message)

# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------
class Config:
    def __init__(self, filename):
        self._filename = filename
        self.load()

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

    def load(self):
        with open(self._filename, "r") as f:
            contents = f.readlines()

        heirachy = {}

        for line_num, line in enumerate(contents):
            heading_re = re.match("(\w+):\s*", line)
            if heading_re:
                heading = heading_re.group(1)
                heirachy[heading] = {}
            else:
                entry_re = re.match("\t|\s{4}(\w+)\s+([\w-]+)\s*:\s*(.+)", line)
                if heading is not None:
                    if entry_re:
                        heirachy[heading][entry_re.group(1)] = self._cast_to_type(
                            entry_re.group(2),
                            entry_re.group(3),
                            line_num+1
                        )
                    else:
                        heading = None
                else:
                    external_re = re.match("(\w+)\s+([\w-]+)\s*:\s*(.+)", line)
                    if external_re:
                        heirachy[external_re.group(1)] = self._cast_to_type(
                            external_re.group(2),
                            external_re.group(3),
                            line_num+1
                        )
                    else:
                        raise ConfigIndentationError(line_num+1)
        self._config = heirachy