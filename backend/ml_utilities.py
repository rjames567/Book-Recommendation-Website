# -----------------------------------------------------------------------------
# Similarity Measures
# -----------------------------------------------------------------------------
# https://www.kdnuggets.com/2020/11/most-popular-distance-metrics-knn.html
# https://milvus.io/docs/metric.md
def jaccard_similarity(set_1, set_2):
    # set_1 and set_2 must be sets not lists.
    # Sets are faster for union+intersection etc, as they are unordered and cannot have duplicate values.
    union = set_1.union(set_2)
    intersection = set_1.intersection(set_2)
    return len(intersection) / len(union)

# -----------------------------------------------------------------------------
# Vector manipulation
# -----------------------------------------------------------------------------
def dot_product(arr_1, arr_2):
    return sum(i * k for i, k in zip(arr_1, arr_2))

# -----------------------------------------------------------------------------
# Matricies
# -----------------------------------------------------------------------------
class Matrix:
    def __init__(self, *kwargs, m=None, n=None):
        if m is None:
            self._m = len(kwargs)
            self._n = len(kwargs[0])
            self._matrix = list(kwargs)
        else:
            self._m = m  # Rows
            self._n = n  # Columns
            self._matrix = [[0 for i in range(self._n)] for k in range(self._m)]
    
    def print(self):
        for i in self._matrix:
            print(" ".join(str(k) for k in i))
        
    def transpose(self):
        res = Matrix(m=self._n, n=self._m)
        for row, v1 in enumerate(self._matrix):
            for col, v2 in enumerate(v1):
                res[col][row] = v2
        return res
    
    @property
    def m(self):
        return self._m
    
    @property
    def n(self):
        return self._n

    def __getitem__(self, index):
        return self._matrix[index] # Returns a list, but doing [a][b] will work as 
        # [b] is performed in resulting arr

    def __add__(self, op_matrix):
        res = Matrix(m=self._m, n=self._n)
        for count, v1, v2 in zip(list(range(self._m)), self._matrix, op_matrix):
            for i in range(self._n):
                res[count][i] = v1[i] + v2[i]
        return res
    
    # https://en.wikipedia.org/wiki/Matrix_multiplication_algorithm
    def __mul__(self, op_value):
        if type(op_value) == int:
            res = Matrix(m=self._m, n=self._n)
            for row, v1 in enumerate(self._matrix):
                for col, v2 in enumerate(v1):
                    res[row][col] = v2 * op_value
        else:
            res = Matrix(n=self._n, m=op_value.m)
            for i in range(self._n):
                for k in range(op_value.m):
                    res[i][k] += sum(self._matrix[i][j] * op_value[j][k] for j in range(self._m))
        return res
    
    def __iter__(self):
        return iter(self._matrix)
