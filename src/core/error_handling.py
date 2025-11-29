"""Centralized error handling and logging system"""

import logging
import sys
from enum import Enum
from typing import Optional, Callable, Any
from pathlib import Path
from datetime import datetime


class ErrorSeverity(Enum):
    """Error severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization"""
    SHADER = "shader"
    MEDIA = "media"
    GRAPH = "graph"
    FILE_IO = "file_io"
    MIDI = "midi"
    AUDIO = "audio"
    RENDERING = "rendering"
    EDITOR = "editor"
    UNKNOWN = "unknown"


class ErrorHandler:
    """Centralized error handler with logging and user notifications"""

    def __init__(self, log_file: Optional[Path] = None):
        self.logger = self._setup_logger(log_file)
        self.error_callbacks = []
        self.suppress_dialogs = False  # For testing or headless mode

    def _setup_logger(self, log_file: Optional[Path] = None) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("JungleLabStudio")
        logger.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s [%(name)s] %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s [%(name)s] %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        return logger

    def register_callback(self, callback: Callable[[str, ErrorSeverity, ErrorCategory], None]):
        """Register a callback for error notifications"""
        self.error_callbacks.append(callback)

    def _notify_callbacks(self, message: str, severity: ErrorSeverity, category: ErrorCategory):
        """Notify all registered callbacks"""
        for callback in self.error_callbacks:
            try:
                callback(message, severity, category)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")

    def log(self, message: str, severity: ErrorSeverity = ErrorSeverity.INFO,
            category: ErrorCategory = ErrorCategory.UNKNOWN):
        """Log a message with severity and category"""
        log_msg = f"[{category.value}] {message}"

        if severity == ErrorSeverity.DEBUG:
            self.logger.debug(log_msg)
        elif severity == ErrorSeverity.INFO:
            self.logger.info(log_msg)
        elif severity == ErrorSeverity.WARNING:
            self.logger.warning(log_msg)
        elif severity == ErrorSeverity.ERROR:
            self.logger.error(log_msg)
        elif severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_msg)

        # Notify callbacks for warnings and above
        if severity.value in ['warning', 'error', 'critical']:
            self._notify_callbacks(message, severity, category)

    def handle_shader_error(self, shader_name: str, error_msg: str,
                           source_code: Optional[str] = None) -> None:
        """Handle shader compilation errors with detailed logging"""
        msg = f"Shader compilation failed: {shader_name}\n{error_msg}"
        self.log(msg, ErrorSeverity.ERROR, ErrorCategory.SHADER)

        if source_code:
            # Extract line number from error if present
            lines = error_msg.split('\n')
            for line in lines:
                if 'ERROR:' in line and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        try:
                            line_num = int(parts[2])
                            # Show context around error
                            source_lines = source_code.split('\n')
                            start = max(0, line_num - 3)
                            end = min(len(source_lines), line_num + 2)
                            context = '\n'.join([
                                f"{i+1:4d}: {source_lines[i]}"
                                for i in range(start, end)
                            ])
                            self.logger.debug(f"Shader context:\n{context}")
                        except (ValueError, IndexError):
                            pass

    def handle_media_error(self, file_path: Path, error_msg: str) -> None:
        """Handle media file loading errors"""
        msg = f"Media file error: {file_path}\n{error_msg}"
        self.log(msg, ErrorSeverity.WARNING, ErrorCategory.MEDIA)

    def handle_graph_error(self, graph_file: Optional[Path], error_msg: str,
                          severity: ErrorSeverity = ErrorSeverity.ERROR) -> None:
        """Handle graph loading/validation errors"""
        if graph_file:
            msg = f"Graph error in {graph_file.name}: {error_msg}"
        else:
            msg = f"Graph error: {error_msg}"
        self.log(msg, severity, ErrorCategory.GRAPH)

    def handle_file_io_error(self, file_path: Path, operation: str, error: Exception) -> None:
        """Handle file I/O errors"""
        msg = f"File {operation} failed: {file_path}\n{type(error).__name__}: {error}"
        self.log(msg, ErrorSeverity.ERROR, ErrorCategory.FILE_IO)

    def safe_execute(self, func: Callable, *args,
                    category: ErrorCategory = ErrorCategory.UNKNOWN,
                    fallback: Any = None,
                    error_msg: Optional[str] = None, **kwargs) -> Any:
        """
        Safely execute a function with error handling

        Args:
            func: Function to execute
            *args: Arguments for the function
            category: Error category
            fallback: Value to return on error
            error_msg: Custom error message
            **kwargs: Keyword arguments for the function

        Returns:
            Function result or fallback value on error
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            msg = error_msg or f"Error executing {func.__name__}: {type(e).__name__}: {e}"
            self.log(msg, ErrorSeverity.ERROR, category)
            return fallback


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    global _error_handler
    if _error_handler is None:
        log_dir = Path("logs")
        log_file = log_dir / f"jungle_lab_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        _error_handler = ErrorHandler(log_file)
    return _error_handler


def init_error_handler(log_file: Optional[Path] = None) -> ErrorHandler:
    """Initialize the global error handler"""
    global _error_handler
    _error_handler = ErrorHandler(log_file)
    return _error_handler


# Convenience functions
def log_info(message: str, category: ErrorCategory = ErrorCategory.UNKNOWN):
    """Log an info message"""
    get_error_handler().log(message, ErrorSeverity.INFO, category)


def log_warning(message: str, category: ErrorCategory = ErrorCategory.UNKNOWN):
    """Log a warning message"""
    get_error_handler().log(message, ErrorSeverity.WARNING, category)


def log_error(message: str, category: ErrorCategory = ErrorCategory.UNKNOWN):
    """Log an error message"""
    get_error_handler().log(message, ErrorSeverity.ERROR, category)


def log_debug(message: str, category: ErrorCategory = ErrorCategory.UNKNOWN):
    """Log a debug message"""
    get_error_handler().log(message, ErrorSeverity.DEBUG, category)
