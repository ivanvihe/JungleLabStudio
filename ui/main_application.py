"""Enhanced main application with modern graphics support and improved UI."""

import sys
import os
import logging
import platform
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMessageBox, QSplashScreen, QStyleFactory,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame
)
from PySide6.QtGui import (
    QSurfaceFormat, QPixmap, QPalette, QColor, QFont, 
    QLinearGradient, QBrush, QPainter, QIcon
)
from PySide6.QtCore import QTimer, Qt, QSize, QThread, Signal, QObject

from utils.settings_manager import SettingsManager
from midi.midi_engine import MidiEngine
from visuals.visualizer_manager import VisualizerManager
from audio.audio_analyzer import AudioAnalyzer
from .mixer_window import MixerWindow
from .control_panel_window import ControlPanelWindow

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('audiovisualizer.log', mode='w', encoding='utf-8')
    ]
)

# Set specific logger levels
loggers_config = {
    'visuals.deck': logging.DEBUG,
    'ui.mixer_window': logging.INFO,
    'visuals.visualizer_manager': logging.INFO,
    'visuals.render_backend': logging.INFO
}

for logger_name, level in loggers_config.items():
    logging.getLogger(logger_name).setLevel(level)


class InitializationWorker(QObject):
    """Worker thread for heavy initialization tasks."""
    
    progress_updated = Signal(int, str)  # progress percentage, status message
    initialization_complete = Signal(object, object, object)  # managers
    error_occurred = Signal(str)

    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager

    def run(self):
        """Run initialization in separate thread."""
        try:
            self.progress_updated.emit(10, "Initializing audio system...")
            
            # Initialize audio analyzer
            audio_analyzer = AudioAnalyzer()
            self.progress_updated.emit(30, "Loading visualizers...")
            
            # Force reload of visualizer manager
            import importlib
            import visuals.visualizer_manager
            importlib.reload(visuals.visualizer_manager)
            
            # Initialize visualizer manager
            visualizer_manager = VisualizerManager()
            self.progress_updated.emit(60, "Setting up MIDI engine...")
            
            # Initialize MIDI engine
            midi_engine = MidiEngine(self.settings_manager, visualizer_manager)
            self.progress_updated.emit(80, "Preparing interface...")
            
            # Small delay to show progress
            QThread.msleep(500)
            
            self.progress_updated.emit(100, "Ready!")
            self.initialization_complete.emit(visualizer_manager, midi_engine, audio_analyzer)
            
        except Exception as e:
            logging.error(f"Initialization failed: {e}")
            self.error_occurred.emit(str(e))


class ModernSplashScreen(QSplashScreen):
    """Enhanced splash screen with modern design."""
    
    def __init__(self):
        # Create a modern gradient background
        pixmap = QPixmap(600, 400)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient background
        gradient = QLinearGradient(0, 0, 600, 400)
        gradient.setColorAt(0.0, QColor(45, 45, 60))
        gradient.setColorAt(0.5, QColor(60, 45, 80))
        gradient.setColorAt(1.0, QColor(80, 45, 60))
        
        painter.fillRect(pixmap.rect(), QBrush(gradient))
        
        # Add title
        painter.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, 
                        "Audio Visualizer Pro\nLoading...")
        
        painter.end()
        
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)


class MainApplication:
    """Enhanced main application with modern UI and improved graphics support."""
    
    def __init__(self):
        logging.info("🚀 Initializing Audio Visualizer Pro...")
        
        self.app = None
        self.splash = None
        self.mixer_window = None
        self.control_panel = None
        self.worker_thread = None
        self.worker = None
        
        self._setup_application()

    def _setup_application(self):
        """Set up the main application with enhanced graphics."""
        try:
            # Configure OpenGL format for maximum compatibility
            self._configure_opengl()
            
            # Set up high DPI and modern UI
            self._configure_ui_attributes()
            
            # Create application instance
            self.app = QApplication(sys.argv)
            self._apply_modern_styling()
            
            logging.info("✅ Application setup complete")
            
        except Exception as e:
            logging.error(f"❌ Application setup failed: {e}")
            raise

    def _configure_opengl(self):
        """Configure OpenGL with multiple fallback options."""
        # Try different OpenGL configurations for maximum compatibility
        configs = [
            # Modern Core Profile
            {
                'version': (4, 1),
                'profile': QSurfaceFormat.OpenGLContextProfile.CoreProfile,
                'description': 'OpenGL 4.1 Core'
            },
            # Fallback Core Profile
            {
                'version': (3, 3),
                'profile': QSurfaceFormat.OpenGLContextProfile.CoreProfile,
                'description': 'OpenGL 3.3 Core'
            },
            # Compatibility Profile
            {
                'version': (3, 3),
                'profile': QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile,
                'description': 'OpenGL 3.3 Compatibility'
            },
            # Legacy fallback
            {
                'version': (2, 1),
                'profile': QSurfaceFormat.OpenGLContextProfile.NoProfile,
                'description': 'OpenGL 2.1 Legacy'
            }
        ]
        
        for config in configs:
            try:
                format = QSurfaceFormat()
                format.setVersion(config['version'][0], config['version'][1])
                format.setProfile(config['profile'])
                format.setDepthBufferSize(24)
                format.setStencilBufferSize(8)
                format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
                format.setSamples(4)  # Anti-aliasing
                format.setSwapInterval(1)  # VSync
                
                QSurfaceFormat.setDefaultFormat(format)
                logging.info(f"✅ OpenGL configured: {config['description']}")
                break
                
            except Exception as e:
                logging.warning(f"⚠️ Failed to set {config['description']}: {e}")
                continue
        else:
            logging.warning("⚠️ All OpenGL configurations failed, using defaults")

    def _configure_ui_attributes(self):
        """Configure UI attributes for modern appearance."""
        # High DPI support
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        
        # Improve rendering quality
        if hasattr(Qt.ApplicationAttribute, 'AA_UseDesktopOpenGL'):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)

    def _apply_modern_styling(self):
        """Apply modern dark theme and styling."""
        # Set application metadata
        self.app.setApplicationName("Audio Visualizer Pro")
        self.app.setApplicationVersion("2.0")
        self.app.setApplicationDisplayName("Audio Visualizer Pro")
        
        # Use Fusion style for better cross-platform appearance
        if "Fusion" in QStyleFactory.keys():
            self.app.setStyle("Fusion")
        
        # Create modern dark palette
        palette = self._create_dark_palette()
        self.app.setPalette(palette)
        
        # Set application icon if available
        try:
            if os.path.exists("assets/icon.png"):
                self.app.setWindowIcon(QIcon("assets/icon.png"))
        except:
            pass

    def _create_dark_palette(self) -> QPalette:
        """Create a modern dark color palette."""
        palette = QPalette()
        
        # Base colors
        dark_color = QColor(30, 30, 35)
        darker_color = QColor(25, 25, 30)
        light_color = QColor(240, 240, 240)
        accent_color = QColor(100, 150, 255)
        highlight_color = QColor(80, 120, 200)
        
        # Set palette colors
        palette.setColor(QPalette.ColorRole.Window, dark_color)
        palette.setColor(QPalette.ColorRole.WindowText, light_color)
        palette.setColor(QPalette.ColorRole.Base, darker_color)
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 50))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(60, 60, 70))
        palette.setColor(QPalette.ColorRole.ToolTipText, light_color)
        palette.setColor(QPalette.ColorRole.Text, light_color)
        palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 55))
        palette.setColor(QPalette.ColorRole.ButtonText, light_color)
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 100, 100))
        palette.setColor(QPalette.ColorRole.Link, accent_color)
        palette.setColor(QPalette.ColorRole.Highlight, highlight_color)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        # Disabled colors
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(80, 80, 80))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(127, 127, 127))
        
        return palette

    def show_splash_screen(self):
        """Show enhanced splash screen during initialization."""
        self.splash = ModernSplashScreen()
        self.splash.show()
        self.app.processEvents()

    def initialize_components(self):
        """Initialize application components with progress tracking."""
        try:
            # Show splash screen
            self.show_splash_screen()
            
            # Initialize settings manager
            self.splash.showMessage("Initializing settings...", Qt.AlignmentFlag.AlignBottom, QColor(255, 255, 255))
            self.app.processEvents()
            
            settings_manager = SettingsManager()
            
            # Start background initialization
            self.worker_thread = QThread()
            self.worker = InitializationWorker(settings_manager)
            self.worker.moveToThread(self.worker_thread)
            
            # Connect signals
            self.worker.progress_updated.connect(self._update_splash_progress)
            self.worker.initialization_complete.connect(self._on_initialization_complete)
            self.worker.error_occurred.connect(self._on_initialization_error)
            self.worker_thread.started.connect(self.worker.run)
            
            # Start worker thread
            self.worker_thread.start()
            
        except Exception as e:
            logging.error(f"❌ Component initialization failed: {e}")
            self._show_error_dialog("Initialization Error", str(e))

    def _update_splash_progress(self, progress: int, message: str):
        """Update splash screen with progress."""
        if self.splash:
            self.splash.showMessage(f"{message} ({progress}%)", 
                                  Qt.AlignmentFlag.AlignBottom, 
                                  QColor(255, 255, 255))
            self.app.processEvents()

    def _on_initialization_complete(self, visualizer_manager, midi_engine, audio_analyzer):
        """Handle successful initialization."""
        try:
            # Close splash screen
            if self.splash:
                # Close and delete the splash screen explicitly to avoid it
                # hanging around if initialization completes successfully
                self.splash.close()
                self.splash.deleteLater()
                self.splash = None
                
            # Create main windows
            self._create_main_windows(visualizer_manager, midi_engine, audio_analyzer)
            
            # Clean up worker thread
            if self.worker_thread:
                self.worker_thread.quit()
                self.worker_thread.wait()
                
            logging.info("✅ Application initialization complete")
            
        except Exception as e:
            logging.error(f"❌ Failed to complete initialization: {e}")
            self._show_error_dialog("Startup Error", str(e))

    def _on_initialization_error(self, error_message: str):
        """Handle initialization error."""
        if self.splash:
            # Ensure the splash is closed even when initialization fails
            self.splash.close()
            self.splash.deleteLater()
            self.splash = None
            
        self._show_error_dialog("Initialization Failed", error_message)

    def _create_main_windows(self, visualizer_manager, midi_engine, audio_analyzer):
        """Create and show main application windows."""
        try:
            # Create mixer window (main output)
            self.mixer_window = MixerWindow(
                visualizer_manager=visualizer_manager,
                settings_manager=SettingsManager(),
                audio_analyzer=audio_analyzer
            )
            
            # Create control panel
            self.control_panel = ControlPanelWindow(
                visualizer_manager=visualizer_manager,
                mixer_window=self.mixer_window,
                settings_manager=SettingsManager(),
                midi_engine=midi_engine,
                audio_analyzer=audio_analyzer
            )
            
            # Position windows nicely
            self._position_windows()
            
            # Show windows
            self.mixer_window.show()
            self.control_panel.show()
            
            # Bring to front
            self.mixer_window.raise_()
            self.mixer_window.activateWindow()
            
            logging.info("✅ Main windows created and shown")
            
        except Exception as e:
            logging.error(f"❌ Failed to create main windows: {e}")
            raise

    def _position_windows(self):
        """Position windows in an optimal layout."""
        if self.mixer_window and self.control_panel:
            # Get screen geometry
            screen = self.app.primaryScreen().geometry()
            
            # Position mixer window (left side)
            mixer_width = min(800, screen.width() // 2)
            mixer_height = min(600, screen.height() - 100)
            self.mixer_window.resize(mixer_width, mixer_height)
            self.mixer_window.move(50, 50)
            
            # Position control panel (right side)
            panel_width = min(400, screen.width() // 3)
            panel_height = mixer_height
            self.control_panel.resize(panel_width, panel_height)
            self.control_panel.move(mixer_width + 70, 50)

    def _show_error_dialog(self, title: str, message: str):
        """Show error dialog with modern styling."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setDetailedText(f"Check the log file for more details: audiovisualizer.log")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def setup_error_handling(self):
        """Set up global error handling."""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
                
            logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
            
            if self.app:
                self._show_error_dialog(
                    "Unexpected Error",
                    f"An unexpected error occurred: {exc_value}"
                )
        
        sys.excepthook = handle_exception

    def run(self):
        """Run the application."""
        try:
            # Set up error handling
            self.setup_error_handling()
            
            # Initialize components
            self.initialize_components()
            
            # Run event loop
            logging.info("🎬 Starting application event loop...")
            exit_code = self.app.exec()
            
            logging.info(f"📋 Application finished with exit code: {exit_code}")
            return exit_code
            
        except Exception as e:
            logging.error(f"❌ Application run failed: {e}")
            if self.app:
                self._show_error_dialog("Critical Error", str(e))
            return 1
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up application resources."""
        try:
            logging.info("🧹 Cleaning up application resources...")
            
            # Clean up worker thread
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.quit()
                self.worker_thread.wait(3000)  # Wait up to 3 seconds
                
            # Close windows
            if self.mixer_window:
                self.mixer_window.close()
            if self.control_panel:
                self.control_panel.close()
                
            # Close splash if still open
            if self.splash:
                self.splash.close()
                
            logging.info("✅ Cleanup complete")
            
        except Exception as e:
            logging.error(f"❌ Cleanup failed: {e}")


def main():
    """Main entry point with enhanced error handling."""
    # Set up platform-specific optimizations
    if platform.system() == "Windows":
        # Enable high DPI awareness on Windows
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return 1
    
    # Check for required dependencies
    required_modules = ['PySide6', 'numpy', 'taichi']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing required modules: {', '.join(missing_modules)}")
        print("Please install them using: pip install " + " ".join(missing_modules))
        return 1
    
    # Create and run application
    try:
        app = MainApplication()
        return app.run()
    except Exception as e:
        logging.error(f"❌ Failed to start application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())