# wire_terrain.py
from PyQt6.QtGui import QSurfaceFormat
from OpenGL.GL import *
import numpy as np
import ctypes
import math
import time

from .base_visualizer import BaseVisualizer

VERT = """
#version 330 core
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aCol;
uniform mat4 projection, view, model;
uniform float u_time;
uniform float u_amp;
uniform float u_freq;
out vec3 vCol;
void main(){
    float h = sin(aPos.x * u_freq + u_time*0.8) * cos(aPos.z * u_freq*1.1 + u_time*0.6) * u_amp;
    vec3 pos = vec3(aPos.x, h, aPos.z);
    vCol = aCol;
    gl_Position = projection * view * model * vec4(pos,1.0);
}
"""

FRAG = """
#version 330 core
in vec3 vCol;
out vec4 FragColor;
uniform float u_brightness;
void main(){
    FragColor = vec4(vCol * u_brightness, 1.0);
}
"""

class WireTerrainVisualizer(BaseVisualizer):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFormat(QSurfaceFormat())
        self.program = None
        self.vao = None
        self.vbo = None
        self.ebo = None
        self.start = time.time()

        self.grid_size = 120
        self.scale = 0.12
        self.amp = 0.9
        self.freq = 0.7
        self.brightness = 1.2
        self.wire = 1

        self.vertices = None
        self.indices = None

    def get_controls(self):
        return {
            "Grid Density": {"type":"slider","min":40,"max":300,"value":self.grid_size},
            "Height Amp": {"type":"slider","min":10,"max":300,"value":int(self.amp*100)},
            "Frequency": {"type":"slider","min":10,"max":300,"value":int(self.freq*100)},
            "Brightness": {"type":"slider","min":50,"max":300,"value":int(self.brightness*100)},
            "Wireframe": {"type":"dropdown","options":["Off","On"],"value":self.wire}
        }

    def update_control(self, name, value):
        if name=="Grid Density":
            self.grid_size = int(value); self._gen_mesh(); self._setup_buffers()
        elif name=="Height Amp":
            self.amp = float(value)/100.0
        elif name=="Frequency":
            self.freq = float(value)/100.0
        elif name=="Brightness":
            self.brightness = float(value)/100.0
        elif name=="Wireframe":
            self.wire = int(value)

    def _gen_mesh(self):
        n = self.grid_size
        xs = np.linspace(-n*self.scale, n*self.scale, n, dtype=np.float32)
        zs = np.linspace(-n*self.scale, n*self.scale, n, dtype=np.float32)
        verts = []
        for i, x in enumerate(xs):
            for j, z in enumerate(zs):
                # color by position
                c = 0.5 + 0.5*np.sin(0.8*x + 1.2*z)
                color = (0.2+0.8*c, 0.4+0.6*c, 0.9)
                verts.extend([x, 0.0, z, *color])
        self.vertices = np.array(verts, dtype=np.float32)

        idx = []
        for i in range(n-1):
            for j in range(n-1):
                a = i*n + j
                b = a + 1
                c = a + n
                d = c + 1
                idx.extend([a,c,b,  b,c,d])  # two triangles
        self.indices = np.array(idx, dtype=np.uint32)

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        vs = glCreateShader(GL_VERTEX_SHADER); glShaderSource(vs, VERT); glCompileShader(vs)
        fs = glCreateShader(GL_FRAGMENT_SHADER); glShaderSource(fs, FRAG); glCompileShader(fs)
        self.program = glCreateProgram()
        glAttachShader(self.program, vs); glAttachShader(self.program, fs); glLinkProgram(self.program)
        glDeleteShader(vs); glDeleteShader(fs)

        self._gen_mesh()
        self._setup_buffers()

    def _setup_buffers(self):
        if self.vao: glDeleteVertexArrays(1,[self.vao])
        if self.vbo: glDeleteBuffers(1,[self.vbo])
        if self.ebo: glDeleteBuffers(1,[self.ebo])

        self.vao = glGenVertexArrays(1); glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1); glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)
        stride = 6*ctypes.sizeof(GLfloat)
        glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(0)); glEnableVertexAttribArray(0)
        glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(3*ctypes.sizeof(GLfloat))); glEnableVertexAttribArray(1)
        self.ebo = glGenBuffers(1); glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        glBindVertexArray(0)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.program)

        t = time.time()-self.start
        glUniform1f(glGetUniformLocation(self.program,"u_time"), t)
        glUniform1f(glGetUniformLocation(self.program,"u_amp"), self.amp)
        glUniform1f(glGetUniformLocation(self.program,"u_freq"), self.freq)
        glUniform1f(glGetUniformLocation(self.program,"u_brightness"), self.brightness)

        # Matrices (usa helpers de tus otros presets)
        projection = self.perspective(55, 1.0, 0.1, 100.0)
        view = self.lookAt(np.array([0, 2.8, 4.6]), np.array([0,0,0]), np.array([0,1,0]))
        model = self.rotate(0, 0,1,0)
        glUniformMatrix4fv(glGetUniformLocation(self.program,"projection"),1,GL_FALSE,projection)
        glUniformMatrix4fv(glGetUniformLocation(self.program,"view"),1,GL_FALSE,view)
        glUniformMatrix4fv(glGetUniformLocation(self.program,"model"),1,GL_FALSE,model)

        if self.wire==1:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.indices.size, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        self.update()

    def resizeGL(self,w,h): glViewport(0,0,w,h)

    def cleanup(self):
        self.makeCurrent()
        if self.program: glDeleteProgram(self.program)
        if self.vbo: glDeleteBuffers(1,[self.vbo])
        if self.ebo: glDeleteBuffers(1,[self.ebo])
        if self.vao: glDeleteVertexArrays(1,[self.vao])
        self.doneCurrent()
