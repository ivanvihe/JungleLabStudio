# visuals/presets/simple_test.py
import logging
import numpy as np
import ctypes
import time
import math
from OpenGL.GL import *
from ..base_visualizer import BaseVisualizer

# Use safer OpenGL helpers when available
try:
    from opengl_fixes import OpenGLSafety
except ImportError:  # pragma: no cover - fallback for environments without helpers
    class OpenGLSafety:  # type: ignore
        """Minimal fallback if OpenGLSafety isn't available"""

        @staticmethod
        def safe_line_width(width: float) -> None:
            """Attempt to set line width, ignoring any errors"""
            try:
                glLineWidth(width)
            except Exception:
                try:
                    glLineWidth(1.0)
                except Exception:
                    pass

        @staticmethod
        def check_gl_errors(context: str = "") -> None:
            """No-op fallback for error checking"""
            return

class SimpleTestVisualizer(BaseVisualizer):
    visual_name = "Simple Test"
    
    def __init__(self):
        super().__init__()
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.ebo = None
        self.start_time = time.time()
        self.initialized = False
        
        # Control parameters
        self.speed = 1.0
        self.line_count = 10
        self.color_speed = 1.0
        
        logging.info("SimpleTestVisualizer created")

    def initializeGL(self):
        """Initialize OpenGL resources"""
        try:
            logging.debug("SimpleTestVisualizer.initializeGL called")
            
            # Clear any existing GL errors
            while glGetError() != GL_NO_ERROR:
                pass
            
            # Set up OpenGL state
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDisable(GL_DEPTH_TEST)
            
            # Load shaders
            if not self.load_shaders():
                logging.error("Failed to load shaders")
                return
            
            # Setup geometry
            if not self.setup_geometry():
                logging.error("Failed to setup geometry")
                return
            
            self.initialized = True
            logging.info("✅ SimpleTestVisualizer initialized successfully")
            
        except Exception as e:
            logging.error(f"Error in SimpleTestVisualizer.initializeGL: {e}")
            import traceback
            traceback.print_exc()

    def load_shaders(self):
        """Load and compile shaders"""
        try:
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            uniform float time;
            uniform float speed;
            out vec3 vertexColor;
            
            void main()
            {
                // Animate position
                float wave = sin(aPos.x * 3.14159 + time * speed) * 0.2;
                vec2 pos = vec2(aPos.x, aPos.y + wave);
                
                gl_Position = vec4(pos, 0.0, 1.0);
                
                // Create color based on position and time
                vertexColor = vec3(
                    0.5 + 0.5 * sin(time + aPos.x * 3.0),
                    0.5 + 0.5 * cos(time * 0.7 + aPos.y * 2.0),
                    0.5 + 0.5 * sin(time * 1.3)
                );
            }
            """
            
            fragment_shader_source = """
            #version 330 core
            in vec3 vertexColor;
            out vec4 FragColor;
            uniform float alpha;
            
            void main()
            {
                FragColor = vec4(vertexColor, alpha);
            }
            """
            
            # Compile vertex shader
            vertex_shader = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex_shader, vertex_shader_source)
            glCompileShader(vertex_shader)
            
            if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vertex_shader).decode()
                logging.error(f"Vertex shader compilation failed: {error}")
                return False
            
            # Compile fragment shader
            fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment_shader, fragment_shader_source)
            glCompileShader(fragment_shader)
            
            if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fragment_shader).decode()
                logging.error(f"Fragment shader compilation failed: {error}")
                return False
            
            # Link program
            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vertex_shader)
            glAttachShader(self.shader_program, fragment_shader)
            glLinkProgram(self.shader_program)
            
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                logging.error(f"Shader program linking failed: {error}")
                return False
            
            # Clean up shaders
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            
            logging.debug("SimpleTestVisualizer shaders compiled successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error loading shaders: {e}")
            return False

    def setup_geometry(self):
        """Setup vertex data and buffers"""
        try:
            # Create line vertices
            vertices = []
            indices = []
            
            for i in range(self.line_count):
                y = -0.8 + (i / (self.line_count - 1)) * 1.6
                # Add line vertices (left to right)
                vertices.extend([-0.9, y])  # Left point
                vertices.extend([0.9, y])    # Right point
                
                # Add indices for line
                base_idx = i * 2
                indices.extend([base_idx, base_idx + 1])
            
            vertices = np.array(vertices, dtype=np.float32)
            indices = np.array(indices, dtype=np.uint32)
            
            # Create and bind VAO
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)
            
            # Create and bind VBO
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)
            
            # Create and bind EBO
            self.ebo = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
            
            # Set vertex attributes
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * 4, ctypes.c_void_p(0))
            
            # Unbind
            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
            
            logging.debug("SimpleTestVisualizer geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up geometry: {e}")
            return False

    def update_geometry(self):
        """Update geometry based on controls"""
        if not self.vbo:
            return
            
        try:
            # Recreate vertices with new line count
            vertices = []
            for i in range(self.line_count):
                y = -0.8 + (i / max(1, self.line_count - 1)) * 1.6
                vertices.extend([-0.9, y])  # Left point
                vertices.extend([0.9, y])    # Right point
            
            vertices = np.array(vertices, dtype=np.float32)
            
            # Update VBO data
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            # Update indices
            indices = []
            for i in range(self.line_count):
                base_idx = i * 2
                indices.extend([base_idx, base_idx + 1])
            
            indices = np.array(indices, dtype=np.uint32)
            
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
            
        except Exception as e:
            logging.error(f"Error updating geometry: {e}")

    def paintGL(self):
        """Render the visualization"""
        try:
            if not self.initialized or not self.shader_program:
                # Fallback rendering
                glClearColor(0.1, 0.0, 0.2, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return
            
            # Clear the screen
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
            
            # Use shader program
            glUseProgram(self.shader_program)
            
            # Update uniforms
            current_time = time.time() - self.start_time
            glUniform1f(glGetUniformLocation(self.shader_program, "time"), current_time * self.color_speed)
            glUniform1f(glGetUniformLocation(self.shader_program, "speed"), self.speed)
            glUniform1f(glGetUniformLocation(self.shader_program, "alpha"), 1.0)
            
            # Draw lines
            if self.vao:
                glBindVertexArray(self.vao)
                # Use safe line width to avoid GL errors on unsupported values
                OpenGLSafety.safe_line_width(2.0)
                glDrawElements(GL_LINES, self.line_count * 2, GL_UNSIGNED_INT, None)
                glBindVertexArray(0)

            # Check for GL errors in debug builds (no-op in fallback)
            OpenGLSafety.check_gl_errors("SimpleTestVisualizer.paintGL")
            
            # Clean up
            glUseProgram(0)
            
        except Exception as e:
            # Only log errors occasionally to avoid spam
            if not hasattr(self, '_last_error_time') or time.time() - self._last_error_time > 5:
                logging.error(f"SimpleTest paint error: {e}")
                self._last_error_time = time.time()
            
            # Fallback rendering
            glClearColor(0.2, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        """Handle resize"""
        glViewport(0, 0, width, height)

    def cleanup(self):
        """Clean up OpenGL resources"""
        try:
            logging.debug("Cleaning up SimpleTestVisualizer")
            
            # Delete shader program
            if self.shader_program:
                try:
                    # Check if program is valid before deleting
                    if glIsProgram(self.shader_program):
                        glDeleteProgram(self.shader_program)
                except:
                    pass  # Ignore errors during cleanup
                finally:
                    self.shader_program = None
            
            # Delete VAO
            if self.vao:
                try:
                    glDeleteVertexArrays(1, [self.vao])
                except:
                    pass
                finally:
                    self.vao = None
            
            # Delete VBO
            if self.vbo:
                try:
                    glDeleteBuffers(1, [self.vbo])
                except:
                    pass
                finally:
                    self.vbo = None
            
            # Delete EBO
            if self.ebo:
                try:
                    glDeleteBuffers(1, [self.ebo])
                except:
                    pass
                finally:
                    self.ebo = None
            
            self.initialized = False
            logging.debug("SimpleTestVisualizer cleanup complete")
            
        except Exception as e:
            # Don't raise errors during cleanup
            logging.debug(f"Cleanup error (non-critical): {e}")

    def get_controls(self):
        """Return available controls"""
        return {
            "Speed": {
                "type": "slider",
                "min": 0,
                "max": 10,
                "value": int(self.speed * 10),
                "default": 10
            },
            "Lines": {
                "type": "slider",
                "min": 2,
                "max": 50,
                "value": self.line_count,
                "default": 10
            },
            "Color Speed": {
                "type": "slider",
                "min": 0,
                "max": 10,
                "value": int(self.color_speed * 10),
                "default": 10
            }
        }

    def update_control(self, name, value):
        """Update a control value"""
        try:
            if name == "Speed":
                self.speed = value / 10.0
                logging.debug(f"Speed updated to {self.speed}")
            elif name == "Lines":
                old_count = self.line_count
                self.line_count = max(2, min(50, int(value)))
                if old_count != self.line_count:
                    self.update_geometry()
                logging.debug(f"Line count updated to {self.line_count}")
            elif name == "Color Speed":
                self.color_speed = value / 10.0
                logging.debug(f"Color speed updated to {self.color_speed}")
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")