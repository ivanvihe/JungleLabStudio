# ui/preview_gl_widget.py
import logging
import numpy as np
import ctypes
import time
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import QTimer
from OpenGL.GL import *

class PreviewGLWidget(QOpenGLWidget):
    def __init__(self, deck, parent=None):
        super().__init__(parent)
        self.deck = deck
        self.quad_vao = 0
        self.quad_vbo = 0
        self.shader_program = None
        self.initialized = False
        self.frame_count = 0
        
        # Update timer for continuous refresh
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.trigger_update)
        self.update_timer.start(16)  # ~60 FPS
        
        logging.info(f"🖼️ PreviewGLWidget created for deck")

    def trigger_update(self):
        """Trigger a repaint"""
        if self.initialized:
            self.update()

    def initializeGL(self):
        """Initialize OpenGL resources"""
        try:
            logging.info("🔧 PreviewGLWidget.initializeGL called")
            
            # Set clear color
            glClearColor(0.05, 0.05, 0.1, 1.0)
            
            # Enable blending
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            # Load shaders
            if self.load_shaders():
                self.setup_quad()
                self.initialized = True
                logging.info("✅ PreviewGLWidget initialized successfully")
            else:
                logging.error("❌ Failed to initialize PreviewGLWidget shaders")
                
        except Exception as e:
            logging.error(f"❌ Error in PreviewGLWidget.initializeGL: {e}")
            import traceback
            traceback.print_exc()

    def load_shaders(self):
        """Load and compile shaders"""
        try:
            # Simple pass-through vertex shader
            vs_src = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoord;
            out vec2 TexCoord;
            void main()
            {
                gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0);
                TexCoord = aTexCoord;
            }
            """
            
            # Simple texture sampling fragment shader
            fs_src = """
            #version 330 core
            out vec4 FragColor;
            in vec2 TexCoord;
            uniform sampler2D screenTexture;
            uniform float hasTexture;
            void main()
            {
                if (hasTexture > 0.5) {
                    // Flip Y coordinate because OpenGL textures are upside down
                    vec2 flippedCoord = vec2(TexCoord.x, 1.0 - TexCoord.y);
                    FragColor = texture(screenTexture, flippedCoord);
                    
                    // If texture is too dark, add a bit of visibility
                    if (FragColor.a < 0.1) {
                        FragColor.a = 1.0;
                    }
                } else {
                    // Fallback gradient if no texture
                    float gradient = TexCoord.y;
                    FragColor = vec4(gradient * 0.2, gradient * 0.1, gradient * 0.3, 1.0);
                }
            }
            """

            # Compile vertex shader
            vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vs, vs_src)
            glCompileShader(vs)
            
            if not glGetShaderiv(vs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vs).decode()
                logging.error(f"❌ Vertex shader error: {error}")
                return False

            # Compile fragment shader
            fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fs, fs_src)
            glCompileShader(fs)
            
            if not glGetShaderiv(fs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fs).decode()
                logging.error(f"❌ Fragment shader error: {error}")
                return False

            # Link program
            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vs)
            glAttachShader(self.shader_program, fs)
            glLinkProgram(self.shader_program)
            
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                logging.error(f"❌ Shader program link error: {error}")
                return False

            # Clean up shaders
            glDeleteShader(vs)
            glDeleteShader(fs)
            
            logging.debug("✅ Preview shaders compiled successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error loading preview shaders: {e}")
            return False

    def setup_quad(self):
        """Setup fullscreen quad geometry"""
        try:
            # Quad vertices with texture coordinates
            quad_vertices = np.array([
                # positions   # texCoords
                -1.0,  1.0,  0.0, 1.0,
                -1.0, -1.0,  0.0, 0.0,
                 1.0, -1.0,  1.0, 0.0,

                -1.0,  1.0,  0.0, 1.0,
                 1.0, -1.0,  1.0, 0.0,
                 1.0,  1.0,  1.0, 1.0
            ], dtype=np.float32)

            # Create VAO and VBO
            self.quad_vao = glGenVertexArrays(1)
            self.quad_vbo = glGenBuffers(1)
            
            glBindVertexArray(self.quad_vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.quad_vbo)
            glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)
            
            # Position attribute
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
            
            # Texture coordinate attribute
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
            
            glBindVertexArray(0)
            
            logging.debug("✅ Preview quad geometry created")
            
        except Exception as e:
            logging.error(f"❌ Error setting up preview quad: {e}")

    def paintGL(self):
        """Render the preview"""
        try:
            # Always clear first
            glClearColor(0.05, 0.05, 0.1, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            if not self.initialized or not self.shader_program:
                self.draw_placeholder()
                return
            
            # First, make sure the deck renders to its FBO
            if self.deck:
                self.deck.paint()
            
            # Get texture from deck
            texture_id = 0
            has_texture = 0.0
            
            if self.deck:
                texture_id = self.deck.get_texture()
                if texture_id and texture_id > 0:
                    has_texture = 1.0
                    
                    # Log occasionally to show it's working
                    self.frame_count += 1
                    if self.frame_count % 120 == 0:  # Every ~2 seconds
                        current_vis = self.deck.get_current_visualizer_name() if hasattr(self.deck, 'get_current_visualizer_name') else "Unknown"
                        logging.info(f"🖼️ Preview rendering - Visualizer: {current_vis}, Texture ID: {texture_id}, Frame: {self.frame_count}")

            # Use shader program
            glUseProgram(self.shader_program)
            
            # Set uniforms
            glUniform1f(glGetUniformLocation(self.shader_program, "hasTexture"), has_texture)
            
            if has_texture > 0.5:
                # Bind the deck's texture
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(GL_TEXTURE_2D, texture_id)
                
                # Set texture parameters for better quality
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                
                glUniform1i(glGetUniformLocation(self.shader_program, "screenTexture"), 0)
            
            # Draw the quad
            glBindVertexArray(self.quad_vao)
            glDrawArrays(GL_TRIANGLES, 0, 6)
            glBindVertexArray(0)
            
            # Clean up
            glUseProgram(0)
            
            if has_texture > 0.5:
                glBindTexture(GL_TEXTURE_2D, 0)
                
        except Exception as e:
            logging.error(f"❌ Error in PreviewGLWidget.paintGL: {e}")
            import traceback
            traceback.print_exc()
            self.draw_error_pattern()

    def draw_placeholder(self):
        """Draw a placeholder pattern when not initialized"""
        try:
            # Simple gradient pattern
            glBegin(GL_QUADS)
            
            # Top - lighter
            glColor3f(0.2, 0.2, 0.3)
            glVertex2f(-1, 1)
            glVertex2f(1, 1)
            
            # Bottom - darker
            glColor3f(0.05, 0.05, 0.1)
            glVertex2f(1, -1)
            glVertex2f(-1, -1)
            
            glEnd()
            
            # Draw some animated dots
            t = time.time()
            num_dots = 5
            for i in range(num_dots):
                x = (i - num_dots/2) * 0.2
                y = 0.3 * np.sin(t * 2 + i)
                
                glPointSize(10)
                glBegin(GL_POINTS)
                glColor3f(0.5, 0.5, 0.6)
                glVertex2f(x, y)
                glEnd()
                
        except:
            pass

    def draw_error_pattern(self):
        """Draw an error pattern"""
        try:
            glClearColor(0.3, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
        except:
            pass

    def resizeGL(self, width, height):
        """Handle resize"""
        glViewport(0, 0, width, height)
        logging.debug(f"📐 Preview resized to {width}x{height}")

    def update_preview(self):
        """Update the preview (called from outside)"""
        if self.initialized:
            self.update()

    def cleanup(self):
        """Clean up OpenGL resources"""
        try:
            self.update_timer.stop()
            
            if self.shader_program:
                glDeleteProgram(self.shader_program)
                self.shader_program = None
                
            if self.quad_vao:
                glDeleteVertexArrays(1, [self.quad_vao])
                self.quad_vao = 0
                
            if self.quad_vbo:
                glDeleteBuffers(1, [self.quad_vbo])
                self.quad_vbo = 0
                
            logging.debug("✅ Preview GL resources cleaned up")
            
        except Exception as e:
            logging.error(f"❌ Error cleaning up preview: {e}")