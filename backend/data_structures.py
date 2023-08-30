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
