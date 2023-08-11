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
            self._m = m
            self._n = n
            self._matrix = [[0 for i in range(self._n)] for k in range(self._m)]