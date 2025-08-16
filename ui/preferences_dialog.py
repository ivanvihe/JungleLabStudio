from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QGroupBox, QDialogButtonBox, QApplication, QLabel
)

class PreferencesDialog(QDialog):
    def __init__(self, settings_manager, midi_engine, audio_analyzer, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.midi_engine = midi_engine
        self.audio_analyzer = audio_analyzer
        self.setWindowTitle("Preferences")
        self.setFixedSize(500, 400)
        
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

        # Rendering section for GPU selection
        render_group = QGroupBox("Rendering")
        render_layout = QFormLayout(render_group)

        self.gpu_selector = QComboBox()
        self.populate_gpu_devices()
        current_gpu = self.settings_manager.get_setting("visual_settings.gpu_index", 0)
        if current_gpu < self.gpu_selector.count():
            self.gpu_selector.setCurrentIndex(current_gpu)
        self.gpu_selector.currentIndexChanged.connect(self.on_gpu_device_changed)
        render_layout.addRow("GPU:", self.gpu_selector)

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
        """Populate GPU selector"""
        self.gpu_selector.clear()
        try:
            import moderngl
            # Attempt to detect up to 4 GPUs
            for i in range(4):
                try:
                    ctx = moderngl.create_context(
                        standalone=True, backend="egl", require=330, device_index=i
                    )
                    name = ctx.info.get("GL_RENDERER", f"GPU {i}")
                    ctx.release()
                    self.gpu_selector.addItem(name)
                except Exception:
                    if i == 0 and self.gpu_selector.count() == 0:
                        self.gpu_selector.addItem("Default GPU")
                    break
        except Exception:
            self.gpu_selector.addItem("Default GPU")

    def on_gpu_device_changed(self, index):
        """Handle GPU selection change"""
        self.settings_manager.set_setting("visual_settings.gpu_index", index)
        if hasattr(self.parent(), 'apply_gpu_selection'):
            self.parent().apply_gpu_selection(index)
