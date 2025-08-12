import logging
import numpy as np
import ctypes
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *

from visuals.deck import Deck

class MixerWindow(QMainWindow):
    def __init__(self, visualizer_manager):
        super().__init__()
        self.setWindowTitle("Audio Visualizer Pro - Main Output")
        self.setGeometry(100, 100, 800, 600)
        self.visualizer_manager = visualizer_manager

        # Create decks BEFORE creating GL widget
        self.deck_a = Deck(visualizer_manager)
        self.deck_b = Deck(visualizer_manager)
        self.mix_value = 0.5

        self.gl_widget = QOpenGLWidget(self)
        self.setCentralWidget(self.gl_widget)

        self.gl_widget.initializeGL = self.initializeGL
        self.gl_widget.paintGL = self.paintGL
        self.gl_widget.resizeGL = self.resizeGL
        
        # Initialize with first available visualizer - but delay until OpenGL is ready
        self.initial_setup_done = False
        
        # Set up timer for continuous animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)  # ~60 FPS

    def initializeGL(self):
        logging.debug("MixerWindow.initializeGL called")
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        self.load_shaders()
        self.setup_quad()
        
        # Initialize decks with current size - NOW with valid OpenGL context
        current_size = QSize(max(self.gl_widget.width(), 800), max(self.gl_widget.height(), 600))
        logging.debug(f"Initializing decks with size: {current_size.width()}x{current_size.height()}")
        
        # Make sure GL context is current
        self.gl_widget.makeCurrent()
        
        # Resize decks to create FBOs
        self.deck_a.resize(current_size)
        self.deck_b.resize(current_size)
        
        # Setup initial visualizers now that OpenGL is ready
        if not self.initial_setup_done:
            self.setup_initial_visualizers()
            self.initial_setup_done = True
        
        logging.debug(f"MixerWindow OpenGL initialized successfully")

    def setup_initial_visualizers(self):
        """Setup initial visualizers now that OpenGL context is available"""
        visualizer_names = self.visualizer_manager.get_visualizer_names()
        if visualizer_names:
            logging.debug(f"Setting up initial visualizers from: {visualizer_names}")
            
            # Make sure we have current GL context
            self.gl_widget.makeCurrent()
            
            # Set default visualizers for both decks
            self.deck_a.set_visualizer(visualizer_names[0])
            if len(visualizer_names) > 1:
                self.deck_b.set_visualizer(visualizer_names[1])
            else:
                self.deck_b.set_visualizer(visualizer_names[0])
                
            logging.debug("Initial visualizers set up successfully")
            
    def animate(self):
        """Called by timer to trigger repaints"""
        if self.gl_widget:
            self.gl_widget.update()

    def load_shaders(self):
        try:
            # Shader for mixing the two deck textures
            with open("shaders/mix.vert", 'r') as f:
                vs_src = f.read()
            with open("shaders/mix.frag", 'r') as f:
                fs_src = f.read()

            vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vs, vs_src)
            glCompileShader(vs)
            
            # Check vertex shader compilation
            if not glGetShaderiv(vs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vs).decode()
                logging.error(f"Vertex shader compilation failed: {error}")
                raise Exception(f"Vertex shader error: {error}")

            fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fs, fs_src)
            glCompileShader(fs)
            
            # Check fragment shader compilation
            if not glGetShaderiv(fs, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fs).decode()
                logging.error(f"Fragment shader compilation failed: {error}")
                raise Exception(f"Fragment shader error: {error}")

            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vs)
            glAttachShader(self.shader_program, fs)
            glLinkProgram(self.shader_program)
            
            # Check program linking
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                logging.error(f"Shader program linking failed: {error}")
                raise Exception(f"Shader program error: {error}")

            glDeleteShader(vs)
            glDeleteShader(fs)
            logging.debug("Mixer shaders loaded successfully")
            
        except Exception as e:
            logging.error(f"Failed to load mixer shaders: {e}")
            # Create a fallback shader or handle the error appropriately
            raise

    def setup_quad(self):
        quad_vertices = np.array([
            # positions   # texCoords
            -1.0,  1.0,  0.0, 1.0,
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,

            -1.0,  1.0,  0.0, 1.0,
             1.0, -1.0,  1.0, 0.0,
             1.0,  1.0,  1.0, 1.0
        ], dtype=np.float32)

        self.quad_vao = glGenVertexArrays(1)
        self.quad_vbo = glGenBuffers(1)
        glBindVertexArray(self.quad_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.quad_vbo)
        glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
        glBindVertexArray(0)

    def paintGL(self):
        # Make sure we have the current context
        self.gl_widget.makeCurrent()
        
        # Render both decks to their framebuffers
        self.deck_a.paint()
        self.deck_b.paint()

        # Now composite them in the main framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, self.gl_widget.defaultFramebufferObject())
        glViewport(0, 0, self.gl_widget.width(), self.gl_widget.height())
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Use the mixing shader
        glUseProgram(self.shader_program)
        
        # Bind textures
        glActiveTexture(GL_TEXTURE0)
        texture_a = self.deck_a.get_texture()
        if texture_a and texture_a > 0:
            glBindTexture(GL_TEXTURE_2D, texture_a)
        
        glActiveTexture(GL_TEXTURE1)
        texture_b = self.deck_b.get_texture()
        if texture_b and texture_b > 0:
            glBindTexture(GL_TEXTURE_2D, texture_b)
        
        # Set uniforms
        glUniform1i(glGetUniformLocation(self.shader_program, "texture1"), 0)
        glUniform1i(glGetUniformLocation(self.shader_program, "texture2"), 1)
        glUniform1f(glGetUniformLocation(self.shader_program, "mixValue"), self.mix_value)

        # Draw the quad
        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        
        # Clean up
        glUseProgram(0)

    def resizeGL(self, w, h):
        current_size = QSize(w, h)
        logging.debug(f"MixerWindow resized to {w}x{h}")
        
        # Make sure GL context is current
        self.gl_widget.makeCurrent()
        
        # Resize decks
        self.deck_a.resize(current_size)
        self.deck_b.resize(current_size)

    def set_mix_value(self, value):
        self.mix_value = value / 100.0
        logging.debug(f"Mix value set to: {self.mix_value}")
        self.gl_widget.update()  # Trigger a repaint
        
    def set_deck_visualizer(self, deck_id, visualizer_name):
        """Called by control panel to change visualizers"""
        logging.debug(f"Setting deck {deck_id} to visualizer: {visualizer_name}")
        
        # Make sure we have OpenGL context
        self.gl_widget.makeCurrent()
        
        if deck_id == 'A':
            self.deck_a.set_visualizer(visualizer_name)
        elif deck_id == 'B':
            self.deck_b.set_visualizer(visualizer_name)
            
        self.gl_widget.update()  # Trigger a repaint
        
    def get_deck_controls(self, deck_id):
        """Get controls for the specified deck"""
        if deck_id == 'A':
            return self.deck_a.get_controls()
        elif deck_id == 'B':
            return self.deck_b.get_controls()
        return {}
        
    def update_deck_control(self, deck_id, name, value):
        """Update a control for the specified deck"""
        if deck_id == 'A':
            self.deck_a.update_control(name, value)
        elif deck_id == 'B':
            self.deck_b.update_control(name, value)
        self.gl_widget.update()  # Trigger a repaint