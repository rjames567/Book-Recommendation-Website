# python3 -m unittest -v test_configuration.py

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backend.configuration as configuration


class IntegerTest(unittest.TestCase):
    def test_positive_integer(self):
        config = configuration.Configuration("tests/test_configurations/integer_positive.conf")
        assert(config.get("value1") == 2)
        assert(type(config.get("value1")) == int)

        assert(config.get("value2") == 5678923423)
        assert (type(config.get("value2")) == int)

        assert(config.get("value3") == 10)
        assert (type(config.get("value3")) == int)

        assert(config.get("value4") == 567)
        assert (type(config.get("value4")) == int)

    def test_negative_integer(self):
        config = configuration.Configuration("tests/test_configurations/integer_negative.conf")
        assert (config.get("value1") == -2)
        assert (type(config.get("value1")) == int)

        assert (config.get("value2") == -5678923423)
        assert (type(config.get("value2")) == int)

        assert (config.get("value3") == -10)
        assert (type(config.get("value3")) == int)

        assert (config.get("value4") == -567)
        assert (type(config.get("value4")) == int)

if __name__ == '__main__':
    unittest.main()
