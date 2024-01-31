# python3 -m unittest -v test_data_structures.py

import unittest
import random
import sys
import os

sys.path.append("/".join(os.getcwd().split("/")[:-1]) + "/backend/")

import data_structures as structures

class QueueTest(unittest.TestCase):
    def test_order(self):
        queue = structures.Queue()
        items = [random.randrange(0, 100) for i in range(100)]
        for i in items:
            queue.push(i)

        out = [queue.pop() for i in range(100)]

        assert(items == out)

    def test_overflow(self):

        queue = structures.Queue(max_length=100)
        for i in range(100):
            queue.push(random.randrange(0, 100))


        self.assertRaises(
            structures.QueueOverflowError,
            queue.push,
            random.random()
        )

    def test_underflow(self):
        queue = structures.Queue()

        self.assertRaises(
            structures.QueueUnderflowError,
            queue.pop
        )


if __name__ == '__main__':
    unittest.main()
