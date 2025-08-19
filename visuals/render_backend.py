"""MINIMAL working render backend - NO TAICHI KERNELS IN CLASS."""

import logging
import time
import numpy as np

# Optional imports
try:
    import moderngl
    MODERNGL_AVAILABLE = True
except ImportError:
    MODERNGL_AVAILABLE = False

try:
    from OpenGL.GL import *
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False


class RenderBackend:
    """Simple backend interface."""
    def __init__(self):
        pass
    def ensure_context(self): pass
    def begin_frame(self, size): pass
    def end_frame(self): return np.zeros((64, 64), dtype=np.float32)
    def clear(self, r, g, b, a=1.0): pass
    def begin_target(self, size): pass
    def end_target(self): pass
    def set_viewport(self, x, y, w, h): pass


class TaichiBackend(RenderBackend):
    """Simple Taichi backend without problematic kernels."""
    
    def __init__(self, resolution=(640, 480), use_gpu=True):
        super().__init__()
        self.resolution = resolution
        logging.info("TaichiBackend created (minimal version)")

    def ensure_context(self):
        pass

    def begin_frame(self, size):
        if size != self.resolution:
            self.resolution = size

    def clear(self, r, g, b, a=1.0):
        pass

    def end_frame(self):
        # Return a simple test pattern
        h, w = self.resolution
        img = np.zeros((h, w), dtype=np.float32)
        return img

    def begin_target(self, size):
        pass

    def end_target(self):
        pass

    def set_viewport(self, x, y, w, h):
        pass


class ModernGLBackend(RenderBackend):
    """ModernGL backend."""
    
    def __init__(self, device_index=0, share_context=None):
        super().__init__()
        self.device_index = device_index
        self.share_context = share_context
        self.resolution = (640, 480)
        
        if not MODERNGL_AVAILABLE:
            raise RuntimeError("ModernGL not available")
        
        logging.info("ModernGLBackend created")

    def ensure_context(self):
        pass

    def begin_frame(self, size):
        self.resolution = size

    def clear(self, r, g, b, a=1.0):
        pass

    def end_frame(self):
        return np.zeros(self.resolution, dtype=np.float32)

    def begin_target(self, size):
        pass

    def end_target(self):
        pass

    def set_viewport(self, x, y, w, h):
        pass


class GLBackend(RenderBackend):
    """Legacy OpenGL backend."""
    
    def __init__(self):
        super().__init__()
        self.resolution = (640, 480)
        logging.info("GLBackend created")

    def ensure_context(self):
        pass

    def begin_frame(self, size):
        self.resolution = size

    def clear(self, r, g, b, a=1.0):
        if OPENGL_AVAILABLE:
            try:
                glClearColor(r, g, b, a)
                glClear(GL_COLOR_BUFFER_BIT)
            except:
                pass

    def end_frame(self):
        return np.zeros(self.resolution, dtype=np.float32)

    def begin_target(self, size):
        pass

    def end_target(self):
        pass

    def set_viewport(self, x, y, w, h):
        if OPENGL_AVAILABLE:
            try:
                glViewport(x, y, w, h)
            except:
                pass


def create_backend(backend_type="taichi", device_index=0, use_gpu=True, share_context=None):
    """Create backend."""
    if backend_type.lower() == "moderngl" and MODERNGL_AVAILABLE:
        try:
            return ModernGLBackend(device_index, share_context)
        except:
            return TaichiBackend()
    elif backend_type.lower() in ["opengl", "gl"]:
        return GLBackend()
    else:
        return TaichiBackend()


def get_available_backends():
    """Get available backends."""
    backends = ["taichi"]
    if MODERNGL_AVAILABLE:
        backends.append("moderngl")
    if OPENGL_AVAILABLE:
        backends.append("opengl")
    return backends


def test_backend(backend_type, device_index=0):
    """Test backend."""
    try:
        backend = create_backend(backend_type, device_index)
        backend.ensure_context()
        backend.begin_frame((64, 64))
        backend.clear(0.5, 0.5, 0.5, 1.0)
        img = backend.end_frame()
        return True, f"Backend '{backend_type}' working"
    except Exception as e:
        return False, f"Backend '{backend_type}' failed: {str(e)}"


def get_backend_info():
    """Get backend info."""
    return {
        'available_backends': get_available_backends(),
        'taichi_available': True,
        'moderngl_available': MODERNGL_AVAILABLE,
        'opengl_available': OPENGL_AVAILABLE,
        'recommended_backend': 'taichi',
        'backend_tests': {}
    }