from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QGroupBox,
    QDialogButtonBox,
    QApplication,
    QLabel,
    QMessageBox,
)
import logging

class PreferencesDialog(QDialog):
    def __init__(self, settings_manager, midi_engine, audio_analyzer, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.midi_engine = midi_engine
        self.audio_analyzer = audio_analyzer
        self.setWindowTitle("Preferences")
        # Slightly larger window to ensure all groups are visible on high DPI
        # displays and small screens.
        self.setFixedSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Monitor assignment section
        monitor_group = QGroupBox("Monitor Assignment")
        monitor_layout = QFormLayout(monitor_group)
        
        # Get available screens
        self.screens = QApplication.screens()
        screen_names = [f"Monitor {i+1}: {screen.name()}" for i, screen in enumerate(self.screens)]
        
        # Control Panel monitor selector
        self.control_panel_monitor = QComboBox()
        self.control_panel_monitor.addItems(screen_names)
        current_cp_monitor = self.settings_manager.get_setting("control_panel_monitor", 0)
        if current_cp_monitor < len(screen_names):
            self.control_panel_monitor.setCurrentIndex(current_cp_monitor)
        monitor_layout.addRow("Control Panel:", self.control_panel_monitor)
        
        # Main Window monitor selector
        self.main_window_monitor = QComboBox()
        self.main_window_monitor.addItems(screen_names)
        current_main_monitor = self.settings_manager.get_setting("main_window_monitor", 0)
        if current_main_monitor < len(screen_names):
            self.main_window_monitor.setCurrentIndex(current_main_monitor)
        monitor_layout.addRow("Main Window:", self.main_window_monitor)
        
        layout.addWidget(monitor_group)
        
        # Device setup section
        device_group = QGroupBox("Device Setup")
        device_layout = QFormLayout(device_group)
        
        # MIDI device selector
        self.midi_device_selector = QComboBox()
        self.midi_device_selector.addItem("No Device")
        self.populate_midi_devices()
        # Set current MIDI device from settings
        current_midi = self.settings_manager.get_setting("last_midi_device", "")
        if current_midi:
            index = self.midi_device_selector.findText(current_midi)
            if index >= 0:
                self.midi_device_selector.setCurrentIndex(index)
        self.midi_device_selector.currentTextChanged.connect(self.on_midi_device_changed)
        device_layout.addRow("MIDI Input:", self.midi_device_selector)
        
        # Audio device selector
        self.audio_device_selector = QComboBox()
        self.audio_device_selector.addItem("No Device")
        self.populate_audio_devices()
        # Set current audio device from settings
        current_audio = self.settings_manager.get_setting("audio_settings.input_device", "")
        if current_audio:
            index = self.audio_device_selector.findText(current_audio)
            if index >= 0:
                self.audio_device_selector.setCurrentIndex(index)
        self.audio_device_selector.currentTextChanged.connect(self.on_audio_device_changed)
        device_layout.addRow("Audio Input:", self.audio_device_selector)
        
        layout.addWidget(device_group)

        # Rendering section for GPU selection - FIXED
        render_group = QGroupBox("Rendering")
        render_layout = QFormLayout(render_group)

        self.gpu_selector = QComboBox()
        self.gpu_info = []  # Store GPU info tuples (index, name, backend)
        # self.populate_gpu_devices()
        
        # Get current GPU setting and apply it
        current_gpu_index = self.settings_manager.get_setting("visual_settings.gpu_index", 0)
        current_backend = self.settings_manager.get_setting("visual_settings.backend", "OpenGL")
        
        # Find matching GPU in our list
        for i, (gpu_index, gpu_name, backend) in enumerate(self.gpu_info):
            if gpu_index == current_gpu_index and backend == current_backend:
                self.gpu_selector.setCurrentIndex(i)
                break
        
        self.gpu_selector.currentIndexChanged.connect(self.on_gpu_device_changed)
        render_layout.addRow("GPU:", self.gpu_selector)

        # Add backend selector
        self.backend_selector = QComboBox()
        self.backend_selector.addItems(["OpenGL", "ModernGL"])
        self.backend_selector.setCurrentText(current_backend)
        self.backend_selector.currentTextChanged.connect(self.on_backend_changed)
        render_layout.addRow("Backend:", self.backend_selector)

        layout.addWidget(render_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Connect signals for immediate application
        self.control_panel_monitor.currentIndexChanged.connect(self.apply_control_panel_monitor)
        self.main_window_monitor.currentIndexChanged.connect(self.apply_main_window_monitor)
    
    def apply_control_panel_monitor(self, index):
        self.settings_manager.set_setting("control_panel_monitor", index)
        # Signal parent to move control panel
        if hasattr(self.parent(), 'move_control_panel_to_monitor'):
            self.parent().move_control_panel_to_monitor(index)
    
    def apply_main_window_monitor(self, index):
        self.settings_manager.set_setting("main_window_monitor", index)
        # Signal parent to move main window
        if hasattr(self.parent(), 'move_main_window_to_monitor'):
            self.parent().move_main_window_to_monitor(index)

    def populate_midi_devices(self):
        """Populate MIDI device selector"""
        self.midi_device_selector.clear()
        self.midi_device_selector.addItem("No Device")
        
        devices = self.midi_engine.list_input_ports()
        for device in devices:
            self.midi_device_selector.addItem(device)

    def populate_audio_devices(self):
        """Populate audio device selector"""
        self.audio_device_selector.clear()
        self.audio_device_selector.addItem("No Device")
        
        devices = self.audio_analyzer.get_available_devices()
        for device in devices:
            device_text = f"{device['name']} ({device['channels']} ch)"
            self.audio_device_selector.addItem(device_text)

    def on_midi_device_changed(self, device_name):
        """Handle MIDI device selection change"""
        if device_name == "No Device":
            self.midi_engine.close_input_port()
            self.settings_manager.set_setting("last_midi_device", "")
        else:
            self.midi_engine.open_input_port(device_name)
            self.settings_manager.set_setting("last_midi_device", device_name)

    def on_audio_device_changed(self, device_text):
        """Handle audio device selection change"""
        if device_text == "No Device":
            self.audio_analyzer.stop_analysis()
            self.settings_manager.set_setting("audio_settings.input_device", "")
        else:
            # Extract device index from the text
            devices = self.audio_analyzer.get_available_devices()
            for i, device in enumerate(devices):
                if device_text.startswith(device['name']):
                    self.audio_analyzer.set_input_device(device['index'])
                    self.audio_analyzer.start_analysis()
                    self.settings_manager.set_setting("audio_settings.input_device", device_text)
                    break

    def populate_gpu_devices(self):
        """Populate GPU selector with available GPUs using multiple detection methods."""
        self.gpu_selector.clear()
        self.gpu_info.clear()

        logging.info("🔍 Detecting GPU devices...")

        # Method 1: Try PyOpenGL + WGL/GLX for NVIDIA/AMD detection
        try:
            self._detect_opengl_gpus()
        except Exception as e:
            logging.debug(f"OpenGL GPU detection failed: {e}")

        # Method 2: Try moderngl detection
        try:
            self._detect_moderngl_gpus()
        except Exception as e:
            logging.debug(f"ModernGL GPU detection failed: {e}")

        # Method 3: Try GPUtil (NVIDIA focused)
        try:
            self._detect_gputil_gpus()
        except Exception as e:
            logging.debug(f"GPUtil detection failed: {e}")

        # Method 4: Try wmi for Windows GPU detection
        try:
            self._detect_windows_gpus()
        except Exception as e:
            logging.debug(f"Windows GPU detection failed: {e}")

        # Fallback: Add at least one default option
        if not self.gpu_info:
            logging.warning("⚠️ No GPUs detected, adding default option")
            self.gpu_info.append((0, "Default GPU (Automatic)", "OpenGL"))
            self.gpu_selector.addItem("Default GPU (Automatic)")

        # Remove duplicates and populate selector
        self._finalize_gpu_list()

        logging.info(f"✅ GPU detection complete. Found {len(self.gpu_info)} options")
        for i, (idx, name, backend) in enumerate(self.gpu_info):
            logging.info(f"   {i}: GPU {idx} - {name} ({backend})")

    def _detect_opengl_gpus(self):
        """Detect GPUs using OpenGL context creation"""
        try:
            from PyQt6.QtOpenGL import QOpenGLContext
            from PyQt6.QtGui import QOffscreenSurface, QSurfaceFormat
            from PyQt6.QtCore import QCoreApplication
            from OpenGL.GL import glGetString, GL_RENDERER, GL_VENDOR, GL_VERSION

            # Ensure we have a QApplication instance
            if not QCoreApplication.instance():
                return

            # Create offscreen surface for context creation
            surface = QOffscreenSurface()
            surface.create()

            context = QOpenGLContext()
            format = QSurfaceFormat()
            format.setMajorVersion(3)
            format.setMinorVersion(3)
            context.setFormat(format)

            if context.create() and context.makeCurrent(surface):
                try:
                    renderer = glGetString(GL_RENDERER).decode('utf-8')
                    vendor = glGetString(GL_VENDOR).decode('utf-8')
                    version = glGetString(GL_VERSION).decode('utf-8')
                    
                    gpu_name = f"{vendor} {renderer}"
                    self.gpu_info.append((0, gpu_name, "OpenGL"))
                    self.gpu_selector.addItem(f"{gpu_name} (OpenGL)")
                    
                    logging.info(f"🎮 OpenGL GPU detected: {gpu_name}")
                    logging.debug(f"   Version: {version}")
                    
                except Exception as e:
                    logging.error(f"Error querying OpenGL info: {e}")
                finally:
                    context.doneCurrent()

        except Exception as e:
            logging.debug(f"OpenGL detection method failed: {e}")

    def _detect_moderngl_gpus(self):
        """Detect GPUs using moderngl"""
        try:
            import moderngl
            
            # Try different device indices
            for device_index in range(4):  # Try first 4 devices
                try:
                    ctx = moderngl.create_context(
                        standalone=True, 
                        require=330, 
                        device_index=device_index
                    )
                    
                    info = ctx.info
                    renderer = info.get('GL_RENDERER', f'Unknown GPU {device_index}')
                    vendor = info.get('GL_VENDOR', 'Unknown')
                    
                    gpu_name = f"{vendor} {renderer}".strip()
                    if gpu_name and gpu_name != "Unknown Unknown":
                        # Check if we already have this GPU
                        if not any(name == gpu_name for _, name, _ in self.gpu_info):
                            self.gpu_info.append((device_index, gpu_name, "ModernGL"))
                            self.gpu_selector.addItem(f"{gpu_name} (ModernGL)")
                            logging.info(f"🎮 ModernGL GPU {device_index} detected: {gpu_name}")
                    
                    ctx.release()
                    
                except Exception as inner_e:
                    # Expected when no more devices available
                    if device_index == 0:
                        logging.debug(f"ModernGL device {device_index} failed: {inner_e}")
                    break
                    
        except ImportError:
            logging.debug("ModernGL not available for GPU detection")
        except Exception as e:
            logging.debug(f"ModernGL detection failed: {e}")

    def _detect_gputil_gpus(self):
        """Detect NVIDIA GPUs using GPUtil"""
        try:
            import GPUtil
            
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_name = f"NVIDIA {gpu.name}"
                # Check if we already have this GPU
                if not any(gpu_name in name for _, name, _ in self.gpu_info):
                    self.gpu_info.append((gpu.id, gpu_name, "OpenGL"))
                    self.gpu_selector.addItem(f"{gpu_name} (NVIDIA)")
                    logging.info(f"🎮 NVIDIA GPU {gpu.id} detected: {gpu.name}")
                    
        except ImportError:
            logging.debug("GPUtil not available")
        except Exception as e:
            logging.debug(f"GPUtil detection failed: {e}")

    def _detect_windows_gpus(self):
        """Detect GPUs on Windows using WMI"""
        try:
            import platform
            if platform.system() != "Windows":
                return
                
            import wmi
            c = wmi.WMI()
            
            for gpu in c.Win32_VideoController():
                if gpu.Name and "Microsoft" not in gpu.Name:
                    gpu_name = gpu.Name
                    # Check if we already have this GPU
                    if not any(gpu_name in name for _, name, _ in self.gpu_info):
                        self.gpu_info.append((0, gpu_name, "OpenGL"))
                        self.gpu_selector.addItem(f"{gpu_name} (Windows)")
                        logging.info(f"🎮 Windows GPU detected: {gpu_name}")
                        
        except ImportError:
            logging.debug("WMI not available")
        except Exception as e:
            logging.debug(f"Windows GPU detection failed: {e}")

    def _finalize_gpu_list(self):
        """Remove duplicates and ensure we have at least one option"""
        # Remove duplicates based on GPU name
        seen_names = set()
        unique_gpus = []
        
        for gpu_index, gpu_name, backend in self.gpu_info:
            # Normalize name for comparison
            normalized_name = gpu_name.lower().strip()
            if normalized_name not in seen_names and normalized_name != "unknown unknown":
                seen_names.add(normalized_name)
                unique_gpus.append((gpu_index, gpu_name, backend))
        
        # Clear and repopulate
        self.gpu_info = unique_gpus
        self.gpu_selector.clear()
        
        for gpu_index, gpu_name, backend in self.gpu_info:
            display_name = f"{gpu_name} ({backend})"
            self.gpu_selector.addItem(display_name)

    def on_gpu_device_changed(self, row):
        """Handle GPU selection change"""
        if row < len(self.gpu_info):
            device_index, gpu_name, backend = self.gpu_info[row]
            
            # Save both GPU index and backend
            self.settings_manager.set_setting("visual_settings.gpu_index", device_index)
            self.settings_manager.set_setting("visual_settings.backend", backend)
            self.settings_manager.set_setting("visual_settings.gpu_name", gpu_name)
            
            logging.info(f"🎮 GPU selection changed: {gpu_name} (Index: {device_index}, Backend: {backend})")
            
            # Apply changes to application
            if hasattr(self.parent(), 'apply_gpu_selection'):
                self.parent().apply_gpu_selection(device_index, backend)
            
            # Show message to user about restart
            QMessageBox.information(
                self, 
                "GPU Selection", 
                f"GPU cambiada a: {gpu_name}\n\n"
                f"Backend: {backend}\n"
                f"Reinicia la aplicación para que los cambios surtan efecto completamente."
            )

    def on_backend_changed(self, backend_name):
        """Handle backend selection change"""
        self.settings_manager.set_setting("visual_settings.backend", backend_name)
        logging.info(f"🔧 Backend changed to: {backend_name}")
        
        # Re-populate GPU list for the new backend
        self.populate_gpu_devices()

    def on_midi_device_changed(self, device_name):
        """Handle MIDI device selection change"""
        if device_name == "No Device":
            self.midi_engine.close_input_port()
            self.settings_manager.set_setting("last_midi_device", "")
        else:
            self.midi_engine.open_input_port(device_name)
            self.settings_manager.set_setting("last_midi_device", device_name)

    def on_audio_device_changed(self, device_text):
        """Handle audio device selection change"""
        if device_text == "No Device":
            self.audio_analyzer.stop_analysis()
            self.settings_manager.set_setting("audio_settings.input_device", "")
        else:
            # Extract device index from the text
            devices = self.audio_analyzer.get_available_devices()
            for i, device in enumerate(devices):
                if device_text.startswith(device['name']):
                    self.audio_analyzer.set_input_device(device['index'])
                    self.audio_analyzer.start_analysis()
                    self.settings_manager.set_setting("audio_settings.input_device", device_text)
                    break