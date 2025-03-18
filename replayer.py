import threading
import time

from controller import DefaultController
from replay import Replay

class HighResolutionTicker:
    def __init__(self, cancel=None, duration=None):
        self.start = time.perf_counter()
        self.expected = 0 if duration is None else duration
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
        duration = self._replay(None)
        while self.repeat and not self.stop_event.is_set():
            duration = self._replay(duration)

    def _replay(self, duration=None):
        ticker = HighResolutionTicker(cancel=self.stop_event, duration=duration)
        for event in self.events:
            if self.stop_event.is_set():
                break
            ticker.next(event.when)
            self.controller.exec(event)

        actual = time.perf_counter() - ticker.start
        print(f"expected: {ticker.expected}, actual: {actual}, diff: {actual - ticker.expected}")
        return actual - ticker.expected
