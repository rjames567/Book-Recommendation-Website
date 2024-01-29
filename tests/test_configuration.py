# python3 -m unittest -v test_configuration.py

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import backend.configuration as configuration

class IntegerTest(unittest.TestCase):
    def positive_integer(self):
        config = configuration.Configuration("data_type_test.conf")

if __name__ == '__main__':
    unittest.main()
