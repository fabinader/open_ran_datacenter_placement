import time


class Timer:
    def __init__(self, name="Execution"):
        self.name = name
        self.start = None
        self.end = None
        self.elapsed = None

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()
        self.elapsed = self.end - self.start
        print(f"{self.name} took: {self.elapsed:.2f} seconds")
