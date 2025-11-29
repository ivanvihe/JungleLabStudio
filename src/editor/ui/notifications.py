"""Notification system for editor UI"""

from imgui_bundle import imgui
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum
import time


class NotificationType(Enum):
    """Notification types with visual styles"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class Notification:
    """A single notification message"""
    message: str
    type: NotificationType
    timestamp: float
    duration: float = 5.0  # seconds

    def is_expired(self) -> bool:
        """Check if notification has expired"""
        return time.time() - self.timestamp > self.duration


class NotificationManager:
    """Manages and displays notifications in the editor"""

    def __init__(self):
        self.notifications: List[Notification] = []
        self.max_notifications = 5

    def add(self, message: str, type: NotificationType = NotificationType.INFO, duration: float = 5.0):
        """Add a new notification"""
        notification = Notification(
            message=message,
            type=type,
            timestamp=time.time(),
            duration=duration
        )
        self.notifications.append(notification)

        # Keep only the most recent notifications
        if len(self.notifications) > self.max_notifications:
            self.notifications.pop(0)

    def info(self, message: str, duration: float = 3.0):
        """Add an info notification"""
        self.add(message, NotificationType.INFO, duration)

    def warning(self, message: str, duration: float = 5.0):
        """Add a warning notification"""
        self.add(message, NotificationType.WARNING, duration)

    def error(self, message: str, duration: float = 8.0):
        """Add an error notification"""
        self.add(message, NotificationType.ERROR, duration)

    def success(self, message: str, duration: float = 3.0):
        """Add a success notification"""
        self.add(message, NotificationType.SUCCESS, duration)

    def render(self, viewport_size: Tuple[float, float]):
        """Render all active notifications"""
        # Remove expired notifications
        self.notifications = [n for n in self.notifications if not n.is_expired()]

        if not self.notifications:
            return

        # Position notifications in top-right corner
        padding = 10.0
        notification_width = 350.0
        notification_height = 60.0
        x_pos = viewport_size[0] - notification_width - padding
        y_pos = padding + 25  # Below menu bar

        for i, notification in enumerate(reversed(self.notifications)):
            # Calculate alpha based on age
            age = time.time() - notification.timestamp
            fade_start = notification.duration - 0.5
            if age > fade_start:
                alpha = 1.0 - ((age - fade_start) / 0.5)
            else:
                alpha = 1.0

            # Set position for this notification
            imgui.set_next_window_pos(imgui.ImVec2(x_pos, y_pos))
            imgui.set_next_window_size(imgui.ImVec2(notification_width, notification_height))

            # Choose color based on type
            bg_color, text_color = self._get_colors(notification.type, alpha)

            # Set window style
            imgui.push_style_color(imgui.Col_.window_bg, imgui.ImVec4(*bg_color))
            imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(*text_color))
            imgui.push_style_var(imgui.StyleVar_.window_rounding, 5.0)
            imgui.push_style_var(imgui.StyleVar_.window_padding, imgui.ImVec2(10, 10))

            # Create window
            flags = (
                imgui.WindowFlags_.no_title_bar |
                imgui.WindowFlags_.no_resize |
                imgui.WindowFlags_.no_move |
                imgui.WindowFlags_.no_scrollbar |
                imgui.WindowFlags_.no_collapse |
                imgui.WindowFlags_.no_saved_settings
            )

            imgui.begin(f"##notification_{i}", flags=flags)

            # Draw icon
            icon = self._get_icon(notification.type)
            imgui.text(icon)
            imgui.same_line()

            # Draw message (wrapped)
            imgui.push_text_wrap_pos(imgui.get_content_region_avail().x)
            imgui.text(notification.message)
            imgui.pop_text_wrap_pos()

            imgui.end()

            # Restore style
            imgui.pop_style_var(2)
            imgui.pop_style_color(2)

            # Move down for next notification
            y_pos += notification_height + 5

    def _get_colors(self, type: NotificationType, alpha: float) -> Tuple[Tuple[float, float, float, float], Tuple[float, float, float, float]]:
        """Get background and text colors for notification type"""
        if type == NotificationType.INFO:
            bg = (0.2, 0.4, 0.7, alpha)
            text = (1.0, 1.0, 1.0, alpha)
        elif type == NotificationType.WARNING:
            bg = (0.8, 0.6, 0.2, alpha)
            text = (0.1, 0.1, 0.1, alpha)
        elif type == NotificationType.ERROR:
            bg = (0.8, 0.2, 0.2, alpha)
            text = (1.0, 1.0, 1.0, alpha)
        elif type == NotificationType.SUCCESS:
            bg = (0.2, 0.7, 0.3, alpha)
            text = (1.0, 1.0, 1.0, alpha)
        else:
            bg = (0.3, 0.3, 0.3, alpha)
            text = (1.0, 1.0, 1.0, alpha)

        return bg, text

    def _get_icon(self, type: NotificationType) -> str:
        """Get icon for notification type"""
        if type == NotificationType.INFO:
            return "ℹ"
        elif type == NotificationType.WARNING:
            return "⚠"
        elif type == NotificationType.ERROR:
            return "✗"
        elif type == NotificationType.SUCCESS:
            return "✓"
        else:
            return "•"

    def clear(self):
        """Clear all notifications"""
        self.notifications.clear()
