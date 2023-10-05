# ------------------------------------------------------------------------------
# Standard Python library imports
# ------------------------------------------------------------------------------
import math
import itertools

# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
import searching_algorithms

# ------------------------------------------------------------------------------
# Custom exceptions
# ------------------------------------------------------------------------------
class QueueOverflowError(Exception):
    def __init__(self):
        super().__init__("Tried to push too many items into the queue")


class QueueUnderflowError(Exception):
    def __init__(self):
        super().__init__("Tried to get a value from an empty queue")


class StackOverflowError(Exception):
    def __init__(self):
        super().__init__("Tried to push too many items into the stack")


class StackUnderflowError(Exception):
    def __init__(self):
        super().__init__("Tried to get a value from an empty stack")


# ------------------------------------------------------------------------------
# Queue
# ------------------------------------------------------------------------------
class Queue:
    def __init__(self, max_length=None):
        self._items = []
        self._max_length = max_length

    def push(self, item):
        if self._max_length is not None and self.size + 1 > self._max_length:
            # Checks if it is not None, and if so does not check second clause
            raise QueueOverflowError
        self._items.append(item)  # Appends to end

    def pop(self):
        if not self.size:
            raise QueueUnderflowError
        return self._items.pop(0)  # List is reverse order - FILO

    def peek(self):
        if not self.size:
            raise QueueUnderflowError
        return self._items[0]

    @property
    def size(self):
        return len(self._items)


class PriorityQueue(Queue):
    def __init__(self, priority_func=None, max_length=None):
        super().__init__(max_length=max_length)
        if priority_func is None:
            self._priority_func = lambda x: x
        else:
            self._priority_func = priority_func

    def push(self, item, priority=None):
        if self._max_length is not None and self.size + 1 > self._max_length:
            # Checks if it is not None, and if so does not check second clause
            raise QueueOverflowError

        if priority is None:
            priority = self._priority_func(item)

        index = searching_algorithms.binary_search(self._items, priority, comparison_func=lambda x: x[1])  # This gets
        # the first item in the array with the value, and it is in reverse order

        if index is None:
            index = 0

        self._items.insert(index, [item, priority])

    def pop(self):
        if not self.size:
            raise QueueUnderflowError
        return super().pop()[0]  # The result from the super would be a list, where the first item is the inserted value
        # and the second is the priority
    
    def peek(self):
        if not self.size:
            raise QueueUnderflowError
        return super().peek()[0]

# ------------------------------------------------------------------------------
# Stack
# ------------------------------------------------------------------------------
class Stack:
    def __init__(self, max_length=None):
        self._items = []
        self._max_length = max_length

    def push(self, item):
        if self._max_length is not None and self.size + 1 > self._max_length:
            raise StackOverflowError
        self._items.append(item)

    def pop(self):
        if not self.size:
            raise StackUnderflowError
        return self._items.pop(-1)

    def peek(self):
        return self._items[-1]

    @property
    def size(self):
        return len(self._items)

# ------------------------------------------------------------------------------
# Binary Tree
# ------------------------------------------------------------------------------
# https://www.tutorialspoint.com/python_data_structure/python_binary_tree.htm
class BinaryTree:
    def __init__(self, value=None, access_function=None):
        self.left = self.right = None
        self.value = value
        if access_function is None:
            self.access_function = lambda x: x
        else:
            self.access_function = access_function

    def insert(self, value):
        if self.value is None:
            self.value = value
        else:
            if self.access_function(value) < self.access_function(self.value):
                if self.left:
                    self.left.insert(value)
                else:
                    self.left = BinaryTree(value, self.access_function)
            else:
                if self.right:
                    self.right.insert(value)
                else:
                    self.right = BinaryTree(value, self.access_function)

    def in_order_traversal(self, root=""):
        if root == "":  # Cannot be None, and an empty string cannot be used.
            root = self
        res = []
        if root is not None:
            res = self.in_order_traversal(root.left)
            res.append(root.value)
            res = res + self.in_order_traversal(root.right)
        return res

# -----------------------------------------------------------------------------
# Matrices
# -----------------------------------------------------------------------------
class Matrix:
    def __init__(self, *kwargs, m=None, n=None, default_value=None):
        if m is None:
            self._m = len(kwargs)
            self._n = len(kwargs[0])
            self._matrix = list(kwargs)
        else:
            self._m = m  # Rows
            self._n = n  # Columns
            if callable(default_value):
                self._matrix = [[default_value() for i in range(self._n)] for k in range(self._m)]
            else:
                self._matrix = [[default_value for i in range(self._n)] for k in range(self._m)]
        self._is_matrix = True

    def print(self):
        for i in self._matrix:
            print(" ".join(str(k) for k in i))

    def transpose(self):
        res = Matrix(m=self._n, n=self._m)
        for row, v1 in enumerate(self._matrix):
            for col, v2 in enumerate(v1):
                res[col][row] = v2
        return res

    def dot_product(self, op_matrix):
        result = self.transpose() * op_matrix
        if self._n == 1 and op_matrix.n == 1:
            return result[0][0]
        return result

    @property
    def m(self):
        return self._m

    @property
    def n(self):
        return self._n

    def determinant(self):
        # https://www.geeksforgeeks.org/determinant-of-a-matrix/
        # Above 2x2, the determinant of a matrix is complicated, beyond A-level
        # further maths, so use existing algorithm to do so
        mat = self.copy()
        temp = [0 for i in range(self._n)]
        total = det = 1

        for i in range(self._n):
            index = i
            while (index < self._n) and (mat[index][i] == 0):
                index += 1

            if (index == self._n):
                continue

            if (index != i):
                for j in range(self._n):
                    mat[index][j], mat[i][j] = mat[i][j], mat[index][j]

                det *= -1 ** index - i

            for j in range(self._n):
                temp[j] = mat[i][j]

            for j in range(i + 1, self._n):
                num1 = temp[i]
                num2 = mat[j][i]

                for k in range(self._n):
                    mat[j][k] = (num1 * mat[j][k]) - (num2 * temp[k])

                total *= num1

        for i in range(self._n):
            det *= mat[i][i]

        return int(det / total)

    def copy(self):
        return Matrix(*[[i for i in k] for k in self._matrix])  # This does not
        # work with self._matrix, as it modifies both the copy and the original.
        # It does not work with .copy() either

    def inverse(self):
        # https://github.com/ThomIves/MatrixInverse, MatrixInversion.py
        self_copy = self.copy()
        identity = IdentityMatrix(size=self._m)
        indices = list(range(self._n))
        for fd in range(self._n):  # fd stands for focus diagonal
            # in the source, this is range(1, self._n), which is wrong.
            fd_scaler = 1.0 / self_copy[fd][fd]
            for j in range(self._n):
                self_copy[fd][j] *= fd_scaler
                identity[fd][j] *= fd_scaler

            for i in indices[:fd] + indices[fd + 1:]:  # skips the row with fd in it.
                cr_scaler = self_copy[i][fd]  # cr stands for current row
                for j in range(self._n):
                    self_copy[i][j] = self_copy[i][j] - cr_scaler * self_copy[fd][j]
                    identity[i][j] = identity[i][j] - cr_scaler * identity[fd][j]
        return identity

    def __pow__(self, power, modulo=None):
        if power >= 1:
            output = self.copy()
            for i in range(1, power):
                output *= output
        elif power == -1:
            output = self.inverse()

        return output

    def __getitem__(self, index):
        return self._matrix[index]  # Returns a list, but doing [a][b] will work as
        # [b] is performed in resulting arr

    def __add__(self, op_matrix):
        res = Matrix(m=self._m, n=self._n)
        for count, v1, v2 in zip(list(range(self._m)), self._matrix, op_matrix):
            for i in range(self._n):
                res[count][i] = v1[i] + v2[i]
        return res

    def __sub__(self, op_matrix):
        return self.__add__(-op_matrix)

    def __neg__(self):
        if self._is_matrix:
            return Matrix(*[[-k for k in i] for i in self._matrix])  # Asterix means it is treated as multiple params
        return Vector(*[-i[0] for i in self._matrix])  # Vectors are arrays of single element arrays, so this
        # flattens for the correct params

    def __pos__(self):
        if self._is_matrix:
            return Matrix(*[[abs(k) for k in i] for i in self._matrix])
        return Vector(*[abs(i[0]) for i in self._matrix])

    # https://en.wikipedia.org/wiki/Matrix_multiplication_algorithm
    def __mul__(self, op_value):
        if type(op_value) == Matrix:
            res = Matrix(m=self._m, n=op_value.n, default_value=0)
            for m in range(res.m):
                for n in range(res.n):
                    for k in range(self.n):
                        res[m][n] += self[m][k] * op_value[k][n]
        else:
            res = Matrix(m=self._m, n=self._n)
            for row, v1 in enumerate(self._matrix):
                for col, v2 in enumerate(v1):
                    res[row][col] = op_value * v2
        return res

    def __truediv__(self, value):
        return self.__mul__(1/value)  # Equivilent to dividing bur will only
        # work with scalars.

    def __iter__(self):
        return iter(self._matrix)
    
    def __eq__(self, matrix):
        return self._matrix == matrix._matrix  # Needs to be rewritten as 
        # comparing two objects with the same contents are treated as not 
        # equal. This is required to check this. Just checks the stored array
        # that is used to store the matrix data.

    def __len__(self):
        return self._m * self._n
    
    def to_array(self):
        return self._matrix
    
    def to_flat_array(self):
        return list(itertools.chain(*self._matrix))
    
    def get_nonzero(self):
        arr = self.to_flat_array().sort()
        return arr[arr.index(1):]  # This approach is significantly faster and more scalable than finding the number
        # of 0s, and iterating that many times and removing them. for a 100×200 matrix, this method takes ~0.09 sec 
        # for 10, and the one described takes ~4.6sec.

    def get_nonzero_indexes(self):
        indexes = []
        for row, val in enumerate(self._matrix):
            for col, i in enumerate(val):
                if not(i):
                    indexes.append((row, col))

        return indexes

    def mask(self, arr):
        copy = self._matrix
        arr.sort(reverse=True)
        print(arr)
        print(copy)
        for i, k in arr:
            print(i,k)
            print(copy[i])
            copy[i].pop(k)
        return list(itertools.chain(*copy))


class IdentityMatrix(Matrix):
    def __init__(self, size):
        self._m = self._n = size
        self._matrix = [[int(i == k) for i in range(self._n)] for k in range(self._m)]
        self._is_matrix = True


class Vector(Matrix):  # Vectors are a type of matrix
    def __init__(self, *kwargs, dimensions=None, default_value=None):
        if dimensions is None:
            kwargs = [[i] for i in kwargs]  # Convert kwargs to 2D array

        super().__init__(*kwargs,
            m=dimensions,
            n=1,
            default_value=default_value
        ) # This handles processing and value checking
                
        self._is_matrix = False

    def dot_product(self, op_vector):
        # Dot product on vectors will always return an integer, so can be done
        # differently which is faster ~ 3x
        return sum(self[i] * k for i, k in enumerate(op_vector))

    def cosine_sim(self, op_vector):
        return self.dot_product(op_vector) / (abs(self) * abs(op_vector))  # Gives a a value between 0 and 1, cosine
        # converts to an angle between the vectors

    def __abs__(self):
        return math.sqrt(sum(i[0]**2 for i in self._matrix))

    def __getitem__(self, index):
        return self._matrix[index][0]
    
    def __setitem__(self, index, value):
        self._matrix[index][0] = value
    
    def __iter__(self):
        return iter(i[0] for i in self._matrix)

    def __mul__(self, op_value):  # Can only multiply Vector by scalar
        # Overwritten as multiplication is only by a scalar, must have a vector
        # result, and can be performed with one less iteration.
        res = Vector(dimensions=self._m)
        for count, arr in enumerate(self._matrix):
            res[count] = op_value * arr[0]  # The values are stored as lists of
            # single elements
        return res

    def __add__(self, op_vector):
        # This is overwritten as it can be done with fewer iterations, and the
        # result must be a vector not a matrix.
        res = Vector(dimensions=self._m)
        for count, v1, v2 in zip(list(range(self._m)), self._matrix, op_vector):
            res[count] = v1[0] + v2  # v1 is a list with one element in it.
        return res
