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

    def test_positve_expression(self):
        config = configuration.Configuration("tests/test_configurations/integer_positive_expression.conf")
        assert (config.get("value1") == (1*10**2))
        assert (type(config.get("value1")) == int)

        assert (config.get("value2") == (1*10**5))
        assert (type(config.get("value2")) == int)

        assert (config.get("value3") == (3.23*10**4))
        assert (type(config.get("value3")) == int)

        assert (config.get("value4") == (1*10**456))
        assert (type(config.get("value4")) == int)

    def test_negative_expression(self):
        config = configuration.Configuration("tests/test_configurations/integer_negative_expression.conf")
        assert (config.get("value1") == (-1*10**2))
        assert (type(config.get("value1")) == int)

        assert (config.get("value2") == (-1*10**5))
        assert (type(config.get("value2")) == int)

        assert (config.get("value3") == (-3.23*10**4))
        assert (type(config.get("value3")) == int)

        assert (config.get("value4") == (-1*10**456))
        assert (type(config.get("value4")) == int)

    def test_invalid_integer(self):
        self.assertRaises(
            configuration.ConfigInvalidDataForType,
            configuration.Configuration("tests/test_configurations/integer_invalid.conf")
        )  # Error is thrown wehn config passed


class StringTest(unittest.TestCase):
    def test_values(self):
        config = configuration.Configuration("tests/test_configurations/string.conf")
        assert (config.get("value1") == "string" and type(config.get("value1")) == str)
        assert (config.get("value2") == "string 2 with spaces & special characters!" and type(config.get("value2")) == str)
        assert (config.get("value3") == "450" and type(config.get("value3")) == str)
        assert (config.get("value4") == "-450" and type(config.get("value4")) == str)
        assert (config.get("value5") == "true" and type(config.get("value5")) == str)
        assert (config.get("value6") == "false" and type(config.get("value6")) == str)
        assert (config.get("value7") == "6.901" and type(config.get("value7")) == str)
        assert (config.get("value8") == "-6.901" and type(config.get("value8")) == str)


class FloatTest(unittest.TestCase):
    def test_floating_point(self):
        config = configuration.Configuration("tests/test_configurations/floating_point_valid.conf")
        assert (config.get("value1") == 1.02 and type(config.get("value1")) == float)
        assert (config.get("value2") == 6002.30523 and type(config.get("value2")) == float)
        assert (config.get("value3") == -1.02  and type(config.get("value3")) == float)
        assert (config.get("value4") == -6002.30523 and type(config.get("value4")) == float)

    def test_integer(self):
        config = configuration.Configuration("tests/test_configurations/floating_point_valid.conf")
        assert (config.get("value1") == 10032 and type(config.get("value1")) == float)
        assert (config.get("value2") == 123 and type(config.get("value2")) == float)
        assert (config.get("value3") == -10032 and type(config.get("value3")) == float)
        assert (config.get("value4") == -123 and type(config.get("value4")) == float)


if __name__ == '__main__':
    unittest.main()
