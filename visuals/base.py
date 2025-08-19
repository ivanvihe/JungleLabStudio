"""Fixed Taichi visual base class with correct syntax and modern OpenGL compatibility."""

from __future__ import annotations

from typing import Tuple
import logging
import numpy as np
import ctypes

# Modern OpenGL imports with fallback
try:
    from OpenGL.GL import *
    from OpenGL.arrays import vbo
    from OpenGL.GL import shaders
    OPENGL_AVAILABLE = True
except Exception:
    OPENGL_AVAILABLE = False
    logging.warning("OpenGL not available, using stubs")

from .base_visualizer import BaseVisualizer


class TaichiVisual(BaseVisualizer):
    """Enhanced Taichi-powered visuals with modern OpenGL compatibility.
    
    Features:
    - Modern OpenGL Core Profile support
    - Enhanced visual effects with post-processing
    - Better performance with VAO/VBO rendering
    - Improved error handling and context management
    - Visual enhancements: bloom, chromatic aberration, film grain
    """

    # Modern vertex shader for texture rendering
    VERTEX_SHADER = """
    #version 330 core
    layout (location = 0) in vec2 aPos;
    layout (location = 1) in vec2 aTexCoord;
    
    out vec2 TexCoord;
    
    void main() {
        gl_Position = vec4(aPos, 0.0, 1.0);
        TexCoord = aTexCoord;
    }
    """

    # Enhanced fragment shader with visual effects
    FRAGMENT_SHADER = """
    #version 330 core
    out vec4 FragColor;
    
    in vec2 TexCoord;
    
    uniform sampler2D ourTexture;
    uniform float time;
    uniform float intensity;
    uniform float brightness;
    uniform float contrast;
    uniform float saturation;
    uniform bool enableBloom;
    uniform bool enableChromAberration;
    uniform bool enableFilmGrain;
    uniform vec2 resolution;
    
    // Visual effect functions
    vec3 bloom(vec3 color, vec2 uv) {
        vec3 bloom = vec3(0.0);
        float weight = 0.0;
        
        // Simple box blur for bloom effect
        for(int x = -2; x <= 2; x++) {
            for(int y = -2; y <= 2; y++) {
                vec2 offset = vec2(x, y) / resolution;
                vec3 sample = texture(ourTexture, uv + offset).rgb;
                float brightness = dot(sample, vec3(0.299, 0.587, 0.114));
                if(brightness > 0.8) {
                    bloom += sample;
                    weight += 1.0;
                }
            }
        }
        
        if(weight > 0.0) {
            bloom /= weight;
            return color + bloom * 0.3;
        }
        return color;
    }
    
    vec3 chromAberration(vec2 uv) {
        float strength = 0.003 * intensity;
        vec2 center = vec2(0.5);
        vec2 dir = (uv - center) * strength;
        
        float r = texture(ourTexture, uv + dir).r;
        float g = texture(ourTexture, uv).g;
        float b = texture(ourTexture, uv - dir).b;
        
        return vec3(r, g, b);
    }
    
    float filmGrain(vec2 uv) {
        float noise = fract(sin(dot(uv * time, vec2(12.9898, 78.233))) * 43758.5453);
        return noise * 0.1 * intensity;
    }
    
    void main() {
        vec2 uv = TexCoord;
        vec3 color;
        
        // Apply chromatic aberration if enabled
        if(enableChromAberration) {
            color = chromAberration(uv);
        } else {
            color = texture(ourTexture, uv).rgb;
        }
        
        // Apply bloom effect if enabled
        if(enableBloom) {
            color = bloom(color, uv);
        }
        
        // Apply brightness, contrast, and saturation
        color = (color - 0.5) * contrast + 0.5 + brightness;
        float luminance = dot(color, vec3(0.299, 0.587, 0.114));
        color = mix(vec3(luminance), color, saturation);
        
        // Apply film grain if enabled
        if(enableFilmGrain) {
            color += filmGrain(uv);
        }
        
        // Ensure color is in valid range
        color = clamp(color, 0.0, 1.0);
        
        FragColor = vec4(color, 1.0);
    }
    """

    def __init__(self, resolution: Tuple[int, int] = (640, 480)):
        super().__init__()
        self.resolution = resolution
        
        # Import TaichiRenderer here to avoid circular imports
        try:
            from render.taichi_renderer import TaichiRenderer
            self.renderer = TaichiRenderer(resolution)
        except ImportError:
            # Fallback to simple renderer
            self.renderer = SimpleRenderer(resolution)
            
        self.setup()
        
        # Modern OpenGL resources
        self._vao = None
        self._vbo = None
        self._ebo = None
        self._texture_id = None
        self._shader_program = None
        self._is_core_profile = False
        self._context_valid = False
        
        # Visual enhancement parameters
        self.visual_effects = {
            'brightness': 0.0,
            'contrast': 1.0,
            'saturation': 1.0,
            'intensity': 1.0,
            'bloom': True,
            'chromatic_aberration': True,
            'film_grain': True
        }
        
        # Performance tracking
        self._frame_count = 0
        self._last_fps_time = 0
        self._fps = 0.0

    def _check_opengl_context(self) -> bool:
        """Check if OpenGL context is valid and determine profile type."""
        if not OPENGL_AVAILABLE:
            return False
            
        try:
            # Check if we have a valid context
            version = glGetString(GL_VERSION)
            if version is None:
                return False
                
            # Check if we're using Core Profile
            try:
                profile = glGetIntegerv(GL_CONTEXT_PROFILE_MASK)
                self._is_core_profile = (profile & GL_CONTEXT_CORE_PROFILE_BIT) != 0
            except:
                # If this fails, we're probably using compatibility profile
                self._is_core_profile = False
                
            self._context_valid = True
            logging.debug(f"OpenGL Context: {version.decode() if isinstance(version, bytes) else version}")
            logging.debug(f"Core Profile: {self._is_core_profile}")
            return True
            
        except Exception as e:
            logging.error(f"OpenGL context check failed: {e}")
            self._context_valid = False
            return False

    def _create_shader_program(self) -> bool:
        """Create modern OpenGL shader program."""
        if not OPENGL_AVAILABLE or not self._context_valid:
            return False
            
        try:
            # Compile vertex shader
            vertex_shader = shaders.compileShader(self.VERTEX_SHADER, GL_VERTEX_SHADER)
            
            # Compile fragment shader
            fragment_shader = shaders.compileShader(self.FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
            
            # Create shader program
            self._shader_program = shaders.compileProgram(vertex_shader, fragment_shader)
            
            # Clean up individual shaders
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            
            logging.debug("Modern OpenGL shaders compiled successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create shader program: {e}")
            return False

    def _create_quad_geometry(self):
        """Create VAO/VBO for fullscreen quad rendering."""
        if not OPENGL_AVAILABLE or not self._context_valid:
            return
            
        try:
            # Fullscreen quad vertices (position + texture coordinates)
            vertices = np.array([
                # positions   # texture coords
                -1.0, -1.0,   0.0, 0.0,   # bottom left
                 1.0, -1.0,   1.0, 0.0,   # bottom right
                 1.0,  1.0,   1.0, 1.0,   # top right
                -1.0,  1.0,   0.0, 1.0    # top left
            ], dtype=np.float32)
            
            indices = np.array([
                0, 1, 2,   # first triangle
                2, 3, 0    # second triangle
            ], dtype=np.uint32)
            
            # Generate VAO
            self._vao = glGenVertexArrays(1)
            glBindVertexArray(self._vao)
            
            # Generate VBO
            self._vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
            
            # Generate EBO
            self._ebo = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
            
            # Configure vertex attributes
            # Position attribute
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            
            # Texture coordinate attribute
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
            glEnableVertexAttribArray(1)
            
            # Unbind
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindVertexArray(0)
            
            logging.debug("VAO/VBO created successfully")
            
        except Exception as e:
            logging.error(f"Failed to create quad geometry: {e}")

    def _render_with_modern_opengl(self, data: np.ndarray, w: int, h: int):
        """Render using modern OpenGL with shaders."""
        try:
            # Create texture if needed
            if self._texture_id is None:
                self._texture_id = glGenTextures(1)
                
            # Bind and configure texture
            glBindTexture(GL_TEXTURE_2D, self._texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            
            # Upload texture data
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, w, h, 0, GL_RED, GL_FLOAT, data)
            
            # Use shader program
            glUseProgram(self._shader_program)
            
            # Set uniforms
            glUniform1i(glGetUniformLocation(self._shader_program, "ourTexture"), 0)
            glUniform1f(glGetUniformLocation(self._shader_program, "time"), self._frame_count * 0.016)
            glUniform1f(glGetUniformLocation(self._shader_program, "brightness"), self.visual_effects['brightness'])
            glUniform1f(glGetUniformLocation(self._shader_program, "contrast"), self.visual_effects['contrast'])
            glUniform1f(glGetUniformLocation(self._shader_program, "saturation"), self.visual_effects['saturation'])
            glUniform1f(glGetUniformLocation(self._shader_program, "intensity"), self.visual_effects['intensity'])
            glUniform1i(glGetUniformLocation(self._shader_program, "enableBloom"), self.visual_effects['bloom'])
            glUniform1i(glGetUniformLocation(self._shader_program, "enableChromAberration"), self.visual_effects['chromatic_aberration'])
            glUniform1i(glGetUniformLocation(self._shader_program, "enableFilmGrain"), self.visual_effects['film_grain'])
            glUniform2f(glGetUniformLocation(self._shader_program, "resolution"), w, h)
            
            # Bind VAO and render
            glBindVertexArray(self._vao)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
            glBindVertexArray(0)
            
            # Cleanup
            glUseProgram(0)
            glBindTexture(GL_TEXTURE_2D, 0)
            
        except Exception as e:
            logging.error(f"Modern OpenGL rendering failed: {e}")
            # Fallback to legacy rendering
            self._render_with_legacy_opengl(data, w, h)

    def _render_with_legacy_opengl(self, data: np.ndarray, w: int, h: int):
        """Fallback legacy OpenGL rendering."""
        try:
            # Try glDrawPixels first (legacy immediate mode)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glDrawPixels(w, h, GL_LUMINANCE, GL_FLOAT, data)
            return
        except:
            pass
            
        # Try texture-based legacy rendering
        try:
            if self._texture_id is None:
                self._texture_id = glGenTextures(1)
                
            glBindTexture(GL_TEXTURE_2D, self._texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, w, h, 0, GL_LUMINANCE, GL_FLOAT, data)
            
            # Render fullscreen quad using immediate mode
            # Skip the problematic glEnable(GL_TEXTURE_2D) in core profile
            if not self._is_core_profile:
                glEnable(GL_TEXTURE_2D)
                
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, -1.0)
            glTexCoord2f(1.0, 0.0); glVertex2f(1.0, -1.0)
            glTexCoord2f(0.0, 1.0); glVertex2f(-1.0, 1.0)
            glTexCoord2f(1.0, 1.0); glVertex2f(1.0, 1.0)
            glEnd()
            
            if not self._is_core_profile:
                glDisable(GL_TEXTURE_2D)
                
            glBindTexture(GL_TEXTURE_2D, 0)
            
        except Exception as e:
            logging.error(f"Legacy OpenGL rendering failed: {e}")

    # ------------------------------------------------------------------
    # Life-cycle hooks --------------------------------------------------
    # ------------------------------------------------------------------
    def setup(self) -> None:
        """Hook for subclasses to register Taichi render passes."""
        return None

    def initializeGL(self, backend=None):
        """Initialize OpenGL resources with modern/legacy detection."""
        if not self._check_opengl_context():
            logging.warning("No valid OpenGL context, rendering will use fallback")
            return
            
        try:
            # Initialize modern OpenGL pipeline if available
            if self._is_core_profile:
                logging.info("Initializing modern OpenGL pipeline")
                if self._create_shader_program():
                    self._create_quad_geometry()
                else:
                    logging.warning("Failed to create shaders, falling back to legacy")
                    self._is_core_profile = False
            else:
                logging.info("Using legacy OpenGL pipeline")
                
        except Exception as e:
            logging.error(f"OpenGL initialization failed: {e}")

    def resizeGL(self, width: int, height: int, backend=None):
        """Recreate the Taichi renderer on resize."""
        if (width, height) != self.resolution:
            self.resolution = (width, height)
            # Recreate renderer to resize canvas
            try:
                from render.taichi_renderer import TaichiRenderer
                self.renderer = TaichiRenderer(self.resolution)
            except ImportError:
                self.renderer = SimpleRenderer(self.resolution)
            self.setup()

    def paintGL(self, time: float = 0.0, size: Tuple[int, int] | None = None, backend=None):
        """Enhanced rendering with visual effects and modern OpenGL support."""
        try:
            # Render Taichi frame
            img = self.render()
            
            # Update frame counter for effects
            self._frame_count += 1
            
            # Handle audio reactivity
            if hasattr(self, 'audio_level') and self.audio_reactive:
                # Adjust visual effects based on audio
                self.visual_effects['intensity'] = 0.5 + self.audio_level * 0.5
                self.visual_effects['brightness'] = self.audio_level * 0.2 - 0.1
                
            # Prepare image data
            h, w = img.shape
            data = np.ascontiguousarray(img.T)
            
            # Choose rendering path based on context
            if self._context_valid and self._is_core_profile and self._shader_program:
                self._render_with_modern_opengl(data, w, h)
            else:
                self._render_with_legacy_opengl(data, w, h)
                
        except Exception as e:
            logging.error(f"TaichiVisual.paintGL error: {e}")
            # Clear to prevent visual artifacts
            if OPENGL_AVAILABLE:
                glClearColor(0.1, 0.0, 0.2, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)

    def cleanup(self):
        """Clean up OpenGL resources."""
        if not OPENGL_AVAILABLE:
            return
            
        try:
            if self._vao:
                glDeleteVertexArrays(1, [self._vao])
            if self._vbo:
                glDeleteBuffers(1, [self._vbo])
            if hasattr(self, '_ebo') and self._ebo:
                glDeleteBuffers(1, [self._ebo])
            if self._texture_id:
                glDeleteTextures(1, [self._texture_id])
            if self._shader_program:
                glDeleteProgram(self._shader_program)
                
        except Exception as e:
            logging.error(f"Cleanup error: {e}")

    def set_visual_effect(self, effect: str, value):
        """Set visual effect parameter."""
        if effect in self.visual_effects:
            self.visual_effects[effect] = value
            logging.debug(f"Set {effect} to {value}")

    def get_visual_effects(self) -> dict:
        """Get current visual effects settings."""
        return self.visual_effects.copy()

    # ------------------------------------------------------------------
    # Rendering ---------------------------------------------------------
    # ------------------------------------------------------------------
    def render(self) -> np.ndarray:
        """Execute registered passes and return the canvas as numpy array."""
        return self.renderer.render()


class SimpleRenderer:
    """Simple fallback renderer when TaichiRenderer is not available."""
    
    def __init__(self, resolution: Tuple[int, int]):
        self.resolution = resolution
        self._passes = []
        
    def add_pass(self, name: str, compute_func):
        """Add a render pass."""
        self._passes.append((name, compute_func))
        
    def render(self) -> np.ndarray:
        """Render a simple pattern."""
        # Create a simple test pattern
        h, w = self.resolution
        img = np.zeros((w, h), dtype=np.float32)
        
        # Simple gradient pattern
        for i in range(w):
            for j in range(h):
                img[i, j] = (i + j) / (w + h) * 0.5
                
        return img