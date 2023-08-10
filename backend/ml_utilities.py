# https://www.kdnuggets.com/2020/11/most-popular-distance-metrics-knn.html
# https://milvus.io/docs/metric.md
def jaccard_similarity(set_1, set_2):
    # set_1 and set_2 must be sets not lists.
    # Sets are faster for union+intersection etc, as they are unordered and cannot have duplicate values.
    union = set_1.union(set_2)
    intersection = set_1.intersection(set_2)
    return len(intersection) / len(union)