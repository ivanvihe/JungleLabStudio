import logging
import numpy as np
import ctypes
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *

class PreviewGLWidget(QOpenGLWidget):
    def __init__(self, deck, parent=None):
        super().__init__(parent)
        self.deck = deck
        self.texture_id = 0
        self.quad_vao = 0
        self.quad_vbo = 0
        self.shader_program = None
        self.initialized = False

    def initializeGL(self):
        logging.debug("PreviewGLWidget.initializeGL called")
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.load_shaders()
        self.setup_quad()
        self.initialized = True

    def load_shaders(self):
        # Simple shader to render a texture
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
        fs_src = """
        #version 330 core
        out vec4 FragColor;
        in vec2 TexCoord;
        uniform sampler2D screenTexture;
        void main()
        {
            FragColor = texture(screenTexture, TexCoord);
        }
        """

        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, vs_src)
        glCompileShader(vs)

        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, fs_src)
        glCompileShader(fs)

        self.shader_program = glCreateProgram()
        glAttachShader(self.shader_program, vs)
        glAttachShader(self.shader_program, fs)
        glLinkProgram(self.shader_program)

        glDeleteShader(vs)
        glDeleteShader(fs)

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
        if not self.initialized:
            return
            
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if not self.shader_program or not self.deck:
            return
            
        # Get texture from deck
        texture_id = self.deck.get_texture()
        
        if texture_id and texture_id > 0:
            glUseProgram(self.shader_program)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glUniform1i(glGetUniformLocation(self.shader_program, "screenTexture"), 0)

            glBindVertexArray(self.quad_vao)
            glDrawArrays(GL_TRIANGLES, 0, 6)
            glBindVertexArray(0)
            glUseProgram(0)
        else:
            # Draw a fallback pattern if no texture
            glClearColor(0.1, 0.1, 0.2, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def update_preview(self):
        self.update()