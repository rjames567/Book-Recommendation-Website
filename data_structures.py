# ------------------------------------------------------------------------------
# Queue
# ------------------------------------------------------------------------------
class Queue:
    def __init__(self, max_length=None):
        self._items = []
        self._max_length = max_length

    def push(self, item):
        self._items.append(item) # Appends to end

    def pop(self):
        return self._items.pop(0) # List is reverse order - FILO

    def peek(self):
        return self._items[0]

    @property
    def size(self):
        return len(self._items)