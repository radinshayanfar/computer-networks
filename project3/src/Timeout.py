import random
import time
from math import floor


class Timeout:
    MAX_TIMEOUT = 64
    INITIAL_TIMEOUT = 4
    MAX_COUNT = 5

    def __init__(self):
        self.timeout: int = Timeout.INITIAL_TIMEOUT
        self.random: int
        self.last_time: int = 0
        self.count: int = 0
        self.__randomize()

    def __randomize(self):
        self.random = random.randint(-1, 1)

    def start_time(self):
        self.last_time = time.time()

    def get_timeout(self) -> int:
        current_time = time.time()
        retransmit = False
        if self.last_time + self.timeout + self.random < current_time:  # timed out
            if self.count >= Timeout.MAX_COUNT:
                return -1
            self.last_time = time.time()
            self.timeout = min(self.timeout << 1, Timeout.MAX_TIMEOUT)
            self.__randomize()
            self.count += 1
            print(f"Timed out! New timeout: {self.timeout + self.random}")
            retransmit = True

        return floor(self.last_time + self.timeout + self.random - time.time()), retransmit
