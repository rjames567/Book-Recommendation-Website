def binary_search(arr, target, comparison_func=None):
    if not len(arr):
        return None

    if comparison_func is None:
        comparison_func = lambda x: x
    # geeksforgeeks.org/python-program-for-binary-search/
    top = len(arr) - 1
    bottom = 0

    while bottom <= top:
        mid = (top + bottom) // 2
        if comparison_func(arr[mid]) > target:
            bottom = mid + 1
        elif comparison_func(arr[mid]) < target:
            top = mid - 1
        else:
            return mid

    return None
