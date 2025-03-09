
import threading
import time

import pydirectinput as pdi
import pynput

from event import EventType

class HighResolutionTicker:
    def __init__(self):
        self.last = None
    
    def next(self, duration):
        # We want to account for processing time.
        current_time = time.perf_counter()
        time_delta = 0 if self.last is None else current_time - self.last
        duration -= time_delta


        # Now we sleep for the remaining time. As we get close, instead of
        # calling sleep, we'll pass, increasing CPU usage as well as accuracy?
        start = time.perf_counter()
        while True:
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


class EventReplayer:
    def __init__(self, events=[]):
        self.events = events
        self.stop_event = threading.Event()

    def replay(self):
        self.stop_event.clear()
        pressed_keys = set()
        keyboard_controller = pynput.keyboard.Controller()

        ticker = HighResolutionTicker()
        for event in self.events:
            if self.stop_event.is_set():
                break

            ticker.next(event.when)

            # Not sure why this is the case (research more) but Roblox seems
            # to only work with the pdi.Mouse and the pynput.Keyboard. It 
            # doesn't work with the opposites.
            if event.event_type == EventType.MOUSE_MOVE:
                pdi.moveTo(event.position[0], event.position[1], _pause=False)
            elif event.event_type == EventType.MOUSE_PRESS:
                button = event.button.removeprefix("Button.")
                pdi.moveTo(event.position[0], event.position[1], _pause=False)
                pdi.mouseDown(button=button, _pause=False)
            elif event.event_type == EventType.MOUSE_RELEASE:
                button = event.button.removeprefix("Button.")
                pdi.moveTo(event.position[0], event.position[1], _pause=False)
                pdi.mouseUp(button=button, _pause=False)
            elif event.event_type == EventType.MOUSE_SCROLL:
                print("scroll not implemented")
            elif event.event_type == EventType.KEY_PRESS:
                key = event.button.removeprefix("Key.")
                key = getattr(pynput.keyboard.Key, key, str(key[1]))
                keyboard_controller.press(key)
                pressed_keys.add(key)
            elif event.event_type == EventType.KEY_RELEASE:
                key = event.button.removeprefix("Key.")
                key = getattr(pynput.keyboard.Key, key, str(key[1]))
                keyboard_controller.release(key)
                pressed_keys.discard(key)

        # Release any keys that were pressed
        pdi.keyUp('shift')
        pdi.keyUp('ctrl')
        pdi.keyUp('alt')
        pdi.keyUp('win')
        for key in pressed_keys:
            pdi.keyUp(key)

    def stop(self):
        self.stop_event.set()