import threading
import time

from pynput import mouse, keyboard

from replay import Event, EventType

class Recorder:
    def __init__(self, ignore_keys=[], events=[]):
        self.events = events
        self.ignore_keys = ignore_keys
        self.last = None
        self.mouse_listener = mouse.Listener(on_move=self.on_mouse_move, on_click=self.on_mouse_click, on_scroll=self.on_mouse_scroll)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_keyboard_press, on_release=self.on_keyboard_release)

    def elapsed_time(self):
        elapsed =  time.perf_counter() - self.last
        self.last = time.perf_counter()
        return elapsed

    def on_mouse_move(self, x, y):
        self.events.append(Event(EventType.MOUSE_MOVE, position=(x, y), when=self.elapsed_time()))

    def on_mouse_click(self, x, y, button, pressed):
        event_type = EventType.MOUSE_PRESS if pressed else EventType.MOUSE_RELEASE
        self.events.append(Event(event_type, position=(x, y), button=str(button), when=self.elapsed_time()))

    def on_mouse_scroll(self, x, y, dx, dy):
        self.events.append(Event(EventType.MOUSE_SCROLL, position=(x, y), delta=(dx, dy), when=self.elapsed_time()))

    def on_keyboard_press(self, key):
        # ignore our start/stop keys
        if key in self.ignore_keys:
            return
        self.events.append(Event(EventType.KEY_PRESS, button=str(key), when=self.elapsed_time()))

    def on_keyboard_release(self, key):
        # ignore our start/stop keys
        if key in self.ignore_keys:
            return
        self.events.append(Event(EventType.KEY_RELEASE, button=str(key), when=self.elapsed_time()))

    def record_initial_mouse_position(self):
        self.initial_mouse_position = mouse.Controller().position
        self.events.append(Event(EventType.MOUSE_MOVE, position=self.initial_mouse_position, when=0))

    def start(self):
        self.events.clear()
        self.running = True
        self.last = time.perf_counter()
        self.record_initial_mouse_position()
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def stop(self):
        self.running = False
        self.mouse_listener.stop()
        self.keyboard_listener.stop()
        return self.events