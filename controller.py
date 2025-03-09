import pydirectinput as pdi
import pynput

from replay import EventType

def DefaultController():
    return CleanupController(CombinedController(PyDirectInputController(), PynputController()))

class PyDirectInputController:
    def __init__(self):
        pass

    def to_key(self, event):
        return event.button.removeprefix("Key.").removeprefix("'").removesuffix("'")
    
    def to_button(self, event):
        return event.button.removeprefix("Button.")

    def close(self):
        pass

    def exec(self, event):
        if event.event_type == EventType.MOUSE_MOVE:
            pdi.moveTo(event.position[0], event.position[1], _pause=False)
        elif event.event_type == EventType.MOUSE_PRESS:
            pdi.moveTo(event.position[0], event.position[1], _pause=False)
            pdi.mouseDown(button=self.to_button(event), _pause=False)
        elif event.event_type == EventType.MOUSE_RELEASE:
            pdi.moveTo(event.position[0], event.position[1], _pause=False)
            pdi.mouseUp(button=self.to_button(event), _pause=False)
        elif event.event_type == EventType.MOUSE_SCROLL:
            print("scrolling not implemented for pydirectinput")
        elif event.event_type == EventType.KEY_PRESS:
            pdi.keyDown(self.to_key(event), _pause=False)
        elif event.event_type == EventType.KEY_RELEASE:
            pdi.keyUp(self.to_key(event), _pause=False)
        else:
            raise ValueError(f"unknown event type: {event.event_type}")

class PynputController:
    def __init__(self):
        self.mouse_controller = pynput.mouse.Controller()
        self.keyboard_controller = pynput.keyboard.Controller()

    def close(self):
        pass

    def to_button(self, event):
        return getattr(pynput.mouse.Button, event.button.removeprefix("Button."))
    
    def to_key(self, event):
        key = event.button.removeprefix("Key.")
        return getattr(pynput.keyboard.Key, key, str(key[1]))

    def exec(self, event):
        if event.event_type == EventType.MOUSE_MOVE:
            self.mouse_controller.position = event.position
        elif event.event_type == EventType.MOUSE_PRESS:
            self.mouse_controller.position = event.position
            self.mouse_controller.press(self.to_button(event))
        elif event.event_type == EventType.MOUSE_RELEASE:
            self.mouse_controller.position = event.position
            self.mouse_controller.release(self.to_button(event))
        elif event.event_type == EventType.MOUSE_SCROLL:
            self.mouse_controller.scroll(event.delta[0], event.delta[1])
        elif event.event_type == EventType.KEY_PRESS:
            self.keyboard_controller.press(self.to_key(event))
        elif event.event_type == EventType.KEY_RELEASE:
            self.keyboard_controller.release(self.to_key(event))
        else:
            raise ValueError(f"unknown event type: {event.event_type}")

class CombinedController:
    def __init__(self, mouse_controller, keyboard_controller):
        self.mouse_controller = mouse_controller
        self.keyboard_controller = keyboard_controller
    
    def close(self):
        self.mouse_controller.close()
        self.keyboard_controller.close()

    def to_button(self, event):
        return self.mouse_controller.to_button(event)
    
    def to_key(self, event):
        return self.keyboard_controller.to_key(event)

    def exec(self, event):
        if event.event_type in (EventType.MOUSE_MOVE, EventType.MOUSE_PRESS, EventType.MOUSE_RELEASE, EventType.MOUSE_SCROLL):
            self.mouse_controller.exec(event)
        else:
            self.keyboard_controller.exec(event)

class CleanupController:
    def __init__(self, controller):
        self.controller = controller
        self.pressed_keys = set()

    def close(self):
        self.controller.close()
        for key in self.pressed_keys:
            self.controller.exec(Event(EventType.KEY_RELEASE, button=key, when=0))
        
        # Also release ctrl, shift, alt, win
        self.controller.exec(Event(EventType.KEY_RELEASE, button="Key.ctrl", when=0))
        self.controller.exec(Event(EventType.KEY_RELEASE, button="Key.shift", when=0))
        self.controller.exec(Event(EventType.KEY_RELEASE, button="Key.alt", when=0))
        self.controller.exec(Event(EventType.KEY_RELEASE, button="Key.win", when=0))
    
    def exec(self, event):
        self.controller.exec(event)

        if event.event_type == EventType.KEY_PRESS:
            self.pressed_keys.add(event.button)
        elif event.event_type == EventType.KEY_RELEASE:
            self.pressed_keys.discard(event.button)

if __name__ == "__main__":
    from replay import Event, EventType
    events = [
        Event(EventType.MOUSE_MOVE, position=(300, 300), when=0),
        Event(EventType.MOUSE_PRESS, position=(300, 300), button="Button.left", when=0.1),
        Event(EventType.MOUSE_RELEASE, position=(300, 300), button="Button.left", when=0.2),
        Event(EventType.KEY_PRESS, button="'d'", when=0.3),
        Event(EventType.KEY_RELEASE, button="'d'", when=0.4),
        Event(EventType.KEY_PRESS, button="'d'", when=0.5),
        Event(EventType.KEY_RELEASE, button="'d'", when=0.6),
    ]

    controller = CombinedController(PyDirectInputController(), PynputController())
    for event in events:
        controller.exec(event)