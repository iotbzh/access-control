import threading
from collections import OrderedDict

class LRUCache:
    def __init__(self, maxsize=1000):
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        self.maxsize = maxsize

    def get(self, sid):
        with self.lock:
            if sid not in self.cache:
                return None
            # Move to end (most recently used)
            self.cache.move_to_end(sid)
            return self.cache[sid]

    def set(self, sid, value):
        with self.lock:
            if sid in self.cache:
                self.cache.move_to_end(sid)
            self.cache[sid] = value
            if len(self.cache) > self.maxsize:
                # Pop the oldest item (least recently used)
                self.cache.popitem(last=False)

    def delete(self, sid):
        with self.lock:
            if sid in self.cache:
                del self.cache[sid]

    def clear(self):
        with self.lock:
            self.cache.clear()
