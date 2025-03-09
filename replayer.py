import threading
import time

from controller import DefaultController

class HighResolutionTicker:
    def __init__(self, cancel=None):
        self.last = None
        self.cancel = cancel
    
    def next(self, duration):
        # We want to account for processing time.
        current_time = time.perf_counter()
        time_delta = 0 if self.last is None else current_time - self.last
        duration -= time_delta


        # Now we sleep for the remaining time. As we get close, instead of
        # calling sleep, we'll pass, increasing CPU usage as well as accuracy?
        start = time.perf_counter()
        while True:
            if self.cancel and self.cancel.is_set():
                break
            elapsed = time.perf_counter() - start
            remaining = duration - elapsed
            if remaining <= 0:
                # If we are somehow still behind, we'll adjust the last time to account for it.
                self.last = time.perf_counter() - remaining
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
        for event in self.events:
            if self.stop_event.is_set():
                break
            ticker.next(event.when)
            self.controller.exec(event)
