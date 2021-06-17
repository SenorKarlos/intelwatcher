from time import time


class Stopwatch:
    def __init__(self):
        self.start = time()

    def pause(self):
        return round(time() - self.start, 1)
