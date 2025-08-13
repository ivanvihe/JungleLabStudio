# UI module initialization
import logging

try:
    from .main_application import MainApplication
    from .mixer_window import MixerWindow
    from .control_panel_window import ControlPanelWindow
    from .preferences_dialog import PreferencesDialog
    from .preview_gl_widget import PreviewGLWidget
    from .midi_mapping_dialog import MidiMappingDialog
    
    __all__ = [
        'MainApplication',
        'MixerWindow', 
        'ControlPanelWindow',
        'PreferencesDialog',
        'PreviewGLWidget',
        'MidiMappingDialog'
    ]
    
    logging.info("UI modules loaded successfully")
    
except ImportError as e:
    logging.error(f"Error importing UI modules: {e}")
    # Create dummy classes to prevent import errors
    
    class DummyClass:
        def __init__(self, *args, **kwargs):
            logging.error(f"Attempted to create instance of dummy class")
            raise ImportError("UI module not properly loaded")
    
    MainApplication = DummyClass
    MixerWindow = DummyClass
    ControlPanelWindow = DummyClass
    PreferencesDialog = DummyClass
    PreviewGLWidget = DummyClass
    MidiMappingDialog = DummyClass
    
    __all__ = []