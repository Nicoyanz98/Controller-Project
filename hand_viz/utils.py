import threading

class MutexValue():
    def __init__(self, value=None):
        self.lock = threading.Lock()
        self.value = value
        self.default = value

    def update(self, new_value):
        with self.lock:
            self.value = new_value

    def get(self):
        copy = self.default
        with self.lock:
            copy = self.value

        return copy