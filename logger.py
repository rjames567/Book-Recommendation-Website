# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import datetime

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
class Logging:
    def __init__(self, filepath="logging/", clear=True):
        self._filepath = filepath
        self._clear = clear
        self._open()

    def _open(self):
        if self._clear:
            method = "w+"
            start = ""
        else:
            method = "a+"
            start = "\n\n"

        now = datetime.datetime.now()
        start += ("-" * 80) + "\nNew session created: "
        start += now.strftime("%d-%m-%Y %H:%M:%S") + "\n" + ("-" * 80) + "\n"

        self._output_file = open(self._filepath + "output.log", method)
        self._output_file.write(start)

    def output_message(self, message):
        message = str(message)
        now = datetime.datetime.now()
        string = "[" + now.strftime("%d-%m-%Y %H:%M:%S") + "] "
        length = len(string)
        new_message = [message[i:i+(80-length)] for i in range(0, len(message), 80 - length)]
        print(new_message)
        string += ("\n" + " " * length).join(new_message) + "\n"
        self._output_file.write(string)

    def __del__(self):
        self._output_file.close()