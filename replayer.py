import threading
import time

from controller import DefaultController
from replay import Replay

class HighResolutionTicker:
    def __init__(self, cancel=None):
        self.start = time.perf_counter()
        self.expected = 0
        self.cancel = cancel
    
    def next(self, duration):
        self.expected += duration
        actual = time.perf_counter() - self.start

        # If we are already behind, we'll just skip the sleep.
        if actual > self.expected:
            return


        # Now we sleep for the remaining time. As we get close, instead of
        # calling sleep, we'll pass, increasing CPU usage as well as accuracy?
        duration = self.expected - actual
        start = time.perf_counter()
        while True:
            if self.cancel and self.cancel.is_set():
                break
            elapsed = time.perf_counter() - start
            remaining = duration - elapsed
            if remaining <= 0:
                break
            if remaining > 0.02:
                time.sleep(max(remaining / 2, 0.0001))
            else:   
                pass

class Replayer:
    def __init__(self, controller=DefaultController(), repeat=False, events=[]):
        self.events = events
        self.controller = controller
        self.repeat = repeat
        self.stop_event = threading.Event()
        self.replay_thread = None

    def start(self):
        self.stop_event.clear()
        self.replay_thread = threading.Thread(target=self._repeat_replay)
        self.replay_thread.start()

    def stop(self):
        self.stop_event.set()
        if self.replay_thread:
            self.replay_thread.join()
        
    def _repeat_replay(self):
        self._replay()
        while self.repeat and not self.stop_event.is_set():
            self._replay()

    def _replay(self):
        ticker = HighResolutionTicker(self.stop_event)
        actual = time.perf_counter()
        expected = 0
        for event in self.events:
            if self.stop_event.is_set():
                break
            expected += event.when
            ticker.next(event.when)
            self.controller.exec(event)

        actual = time.perf_counter() - actual
        print(f"expected: {expected}, actual: {actual}, diff: {actual - expected}")


if __name__ == "__main__":
    # Test the high resolution ticker with file given on command line.
    import argparse
    parser = argparse.ArgumentParser(description="test high resolution ticker")
    parser.add_argument("replay_file", type=str, help="path to the replay file")
    args = parser.parse_args()
    replay = Replay.load(args.replay_file)

    ticker = HighResolutionTicker()
    expected = 0
    actual = time.perf_counter()
    for event in replay.events:
        ticker.next(event.when)
        expected += event.when

    actual = time.perf_counter() - actual
    print(f"expected: {expected}, actual: {actual}, diff: {actual - expected}")