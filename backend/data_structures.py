# ------------------------------------------------------------------------------
# Custom exceptions
# ------------------------------------------------------------------------------
class QueueOverflowError(Exception):
    def __init__(self):
        super().__init__("Tried to push too many items into the queue")


class QueueUnderflowError(Exception):
    def __init__(self):
        super().__init__("Tried to get a value from an empty queue")


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
            raise QueueOverflowError()
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
            self._matrix = [[default_value for i in range(self._n)] for k in range(self._m)]

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
        return Matrix(*[[-k for k in i] for i in self._matrix])  # Asterix means it is treated as multiple params

    def __pos__(self):
        return Matrix(*[[abs(k) for k in i] for i in self._matrix])

    # https://en.wikipedia.org/wiki/Matrix_multiplication_algorithm
    def __mul__(self, op_value):
        if type(op_value) == int:
            res = Matrix(m=self._m, n=self._n)
            for row, v1 in enumerate(self._matrix):
                for col, v2 in enumerate(v1):
                    res[row][col] = v2 * op_value
        else:
            res = Matrix(m=self._m, n=op_value.n)
            for m in range(res.m):
                for n in range(res.n):
                    for k in range(self.n):
                        res[m][n] += self[m][k] * op_value[k][n]
        return res

    def __iter__(self):
        if self._m > 1:
            return iter(self._matrix)
        else:
            return iter(self._matrix[0])


class Vector(Matrix):  # Vectors are a type of matrix
    def __init__(self, *kwargs, dimensions=None, default_value=None):
        if dimensions is None:
            kwargs = [[i] for i in kwargs]  # Convert kwargs to 2D array

        super().__init__(*kwargs,
            m=dimensions,
            n=1,
            default_value=default_value
        ) # This handles processing and value checking

    def __getitem__(self, index):
        return self._matrix[index][0]
    
    def __setitem__(self, index, value):
        self._matrix[index][0] = value
    
    def __iter__(self):
        return iter(i[0] for i in self._matrix)
