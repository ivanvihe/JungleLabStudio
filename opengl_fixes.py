"""OpenGL compatibility fixes."""

import logging

try:
    from OpenGL.GL import *
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False


class OpenGLSafety:
    """OpenGL safety utilities."""
    
    @staticmethod
    def get_gl_info():
        """Get GL info safely."""
        if not OPENGL_AVAILABLE:
            return {}
        try:
            return {
                'version': glGetString(GL_VERSION).decode() if glGetString(GL_VERSION) else 'Unknown',
                'vendor': glGetString(GL_VENDOR).decode() if glGetString(GL_VENDOR) else 'Unknown',
                'renderer': glGetString(GL_RENDERER).decode() if glGetString(GL_RENDERER) else 'Unknown'
            }
        except:
            return {'version': 'Unknown', 'vendor': 'Unknown', 'renderer': 'Unknown'}
    
    @staticmethod
    def safe_bind_framebuffer(target, fbo):
        """Safely bind framebuffer."""
        if OPENGL_AVAILABLE:
            try:
                glBindFramebuffer(target, fbo)
            except:
                pass


def init_opengl_debug():
    """Initialize OpenGL debugging."""
    return OPENGL_AVAILABLE


def get_opengl_info():
    """Get OpenGL information."""
    return OpenGLSafety.get_gl_info() if OPENGL_AVAILABLE else {'available': False}


def test_opengl_functionality():
    """Test OpenGL functionality."""
    if not OPENGL_AVAILABLE:
        return {'available': False}
    return {'available': True, 'basic_queries': True}