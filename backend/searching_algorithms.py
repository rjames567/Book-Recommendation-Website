def binary_search(arr, target):
    # geeksforgeeks.org/python-program-for-binary-search/
    top = len(arr) - 1
    bottom = 0

    while bottom <= top:
        mid = (top + bottom) // 2
        if arr[mid] < target:
            bottom = mid + 1
        elif arr[mid] > target:
            top = mid - 1
        else:
            return mid

    return None
