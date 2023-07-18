# ------------------------------------------------------------------------------
# Custom exceptions
# ------------------------------------------------------------------------------
class QueueOverflowError (Exception):
    def __init__(self):
        super().__init__("Tried to push too many items into the queue")

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
        self._items.append(item) # Appends to end

    def pop(self):
        return self._items.pop(0) # List is reverse order - FILO

    def peek(self):
        return self._items[0]

    @property
    def size(self):
        return len(self._items)