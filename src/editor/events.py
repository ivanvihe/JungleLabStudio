"""Event system for editor"""

from typing import Dict, List, Callable, Any
from dataclasses import dataclass


@dataclass
class Event:
    """Base event"""
    type: str
    data: Any = None


class EventSystem:
    """Central event dispatcher"""

    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        if callback not in self.listeners[event_type]:
            self.listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event"""
        if event_type in self.listeners:
            if callback in self.listeners[event_type]:
                self.listeners[event_type].remove(callback)

    def emit(self, event_type: str, data: Any = None):
        """Emit an event to all subscribers"""
        if event_type in self.listeners:
            event = Event(type=event_type, data=data)
            for callback in self.listeners[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in event handler for '{event_type}': {e}")

    def clear(self):
        """Clear all listeners"""
        self.listeners.clear()


# Event type constants
class Events:
    # Graph events
    NODE_ADDED = "node.added"
    NODE_REMOVED = "node.removed"
    NODE_MOVED = "node.moved"
    NODE_SELECTED = "node.selected"
    NODE_DESELECTED = "node.deselected"

    CONNECTION_ADDED = "connection.added"
    CONNECTION_CREATED = "connection.created"  # Alias for CONNECTION_ADDED
    CONNECTION_REMOVED = "connection.removed"

    # Edit events
    PARAM_CHANGED = "param.changed"
    ANIMATION_ADDED = "animation.added"
    ANIMATION_REMOVED = "animation.removed"
    TRIGGER_ADDED = "trigger.added"
    TRIGGER_REMOVED = "trigger.removed"

    # File events
    FILE_NEW = "file.new"
    FILE_OPENED = "file.opened"
    FILE_SAVED = "file.saved"
    FILE_MODIFIED = "file.modified"
    FILE_CLOSED = "file.closed"

    # MIDI events
    MIDI_MESSAGE = "midi.message"
    MIDI_LEARN_STARTED = "midi.learn.started"
    MIDI_LEARN_COMPLETED = "midi.learn.completed"
    MIDI_BINDING_ADDED = "midi.binding.added"
    MIDI_BINDING_REMOVED = "midi.binding.removed"

    # Playback events
    PLAYBACK_STARTED = "playback.started"
    PLAYBACK_STOPPED = "playback.stopped"
    PLAYBACK_FRAME = "playback.frame"

    # UI events
    INSPECTOR_CHANGED = "inspector.changed"
    YAML_CHANGED = "yaml.changed"
    CANVAS_ZOOM_CHANGED = "canvas.zoom.changed"


# Global event system instance
event_system = EventSystem()
