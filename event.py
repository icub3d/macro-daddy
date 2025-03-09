from enum import Enum
import json

# Define the EventType enum
class EventType(str, Enum):
    MOUSE_MOVE = 'mouse_move'
    MOUSE_PRESS = 'mouse_click'
    MOUSE_RELEASE = 'mouse_release'
    MOUSE_SCROLL = 'mouse_scroll'
    KEY_PRESS = 'key_press'
    KEY_RELEASE = 'key_release'

# Define the Event class
class Event:
    def __init__(self, event_type, position=None, delta=None, button=None, when=None):
        self.event_type = event_type
        self.position = position
        self.delta = delta
        self.button = button
        self.when = when

    def __repr__(self):
        return f"Event(type={self.event_type}, position={self.position}, delta={self.delta}, button={self.button}, when={self.when})"

    def to_dict(self):
        return {
            'event_type': self.event_type,
            'position': self.position,
            'delta': self.delta,
            'button': self.button,
            'when': self.when
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            event_type=EventType(data.get('event_type')),
            position=data.get('position'),
            button=data.get('button'),
            delta=data.get('delta'),
            when=data.get('when')
        )
      
    def to_json(self):
        return json.dumps(self.to_dict())
