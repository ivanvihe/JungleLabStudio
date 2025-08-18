import types
from types import SimpleNamespace
import ui.control_panel_window as cpw

class FakeSignal:
    def __init__(self):
        self._connections = []
    def connect(self, func):
        self._connections.append(func)

class FakeHandle:
    def __init__(self, window):
        self.window = window
        self.screen = None
    def setScreen(self, screen):
        self.screen = screen

class FakeScreen:
    def __init__(self, idx):
        self._geom = SimpleNamespace(topLeft=lambda: f"pt{idx}")
    def geometry(self):
        return self._geom

class FakeWindow:
    def __init__(self):
        self.show_called = False
        self.fullscreen = False
        self.gl_ready = FakeSignal()
        self.gl_initialized = True
        self.exit_fullscreen = FakeSignal()
        self.signal_set_mix_value = FakeSignal()
        self.signal_set_deck_visualizer = FakeSignal()
        self.signal_update_deck_control = FakeSignal()
        self.signal_set_deck_opacity = FakeSignal()
        self.signal_trigger_deck_action = FakeSignal()
        self.mix_value = 0.5
        self.deck_a = SimpleNamespace(current_visualizer_name=None)
        self.deck_b = SimpleNamespace(current_visualizer_name=None)
    def windowHandle(self):
        return FakeHandle(self) if self.show_called else None
    def show(self):
        self.show_called = True
    def showFullScreen(self):
        if not self.show_called:
            raise RuntimeError("showFullScreen without show")
        self.fullscreen = True
    def isFullScreen(self):
        return self.fullscreen
    def showNormal(self):
        self.fullscreen = False
    def close(self):
        self.closed = True
    def setGeometry(self, geom):
        self.geom = geom
    def move(self, pt):
        self.moved = True
    def set_mix_value(self, val):
        self.mix_value_val = val
    def set_deck_visualizer(self, deck, name):
        pass
    def update_deck_control(self, *args):
        pass
    def set_deck_opacity(self, *args):
        pass
    def trigger_deck_action(self, *args):
        pass
    def winId(self):
        raise RuntimeError("winId should not be called")

class SettingsStub:
    def __init__(self, monitors):
        self.monitors = monitors
    def get_fullscreen_monitors(self):
        return self.monitors


def test_activate_fullscreen_multiple_monitors(monkeypatch):
    screens = [FakeScreen(0), FakeScreen(1)]
    monkeypatch.setattr(cpw, "QApplication", SimpleNamespace(screens=lambda: screens))
    monkeypatch.setattr(cpw, "QMessageBox", SimpleNamespace(warning=lambda *a, **k: None))
    monkeypatch.setattr(cpw, "MixerWindow", lambda *a, **k: FakeWindow())

    main_window = FakeWindow()
    main_window.show_called = True  # simulate existing handle

    cp = SimpleNamespace(
        settings_manager=SettingsStub([0, 1]),
        mixer_window=main_window,
        visualizer_manager=None,
        audio_analyzer=None,
        fullscreen_windows=[],
    )

    def exit_fullscreen_mode(self):
        for w in list(self.fullscreen_windows):
            if w.isFullScreen():
                w.showNormal()
            if w is not self.mixer_window:
                w.close()
        self.fullscreen_windows.clear()

    cp.exit_fullscreen_mode = exit_fullscreen_mode.__get__(cp, type(cp))

    cpw.ControlPanelWindow.activate_fullscreen_mode(cp)

    assert len(cp.fullscreen_windows) == 2
    assert cp.fullscreen_windows[1].fullscreen
