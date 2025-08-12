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
    visual_name = "Wire Terrain"
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
                # Color gradient from blue to cyan to white based on position
                dist_from_center = np.sqrt(x*x + z*z) / (n*self.scale)
                r = 0.2 + 0.5 * dist_from_center
                g = 0.4 + 0.4 * dist_from_center  
                b = 0.8 + 0.2 * dist_from_center
                verts.extend([x, 0.0, z, r, g, b])
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
        
        print(f"Grid size: {n}x{n}, Scale: {self.scale}, Bounds: [{-n*self.scale:.2f}, {n*self.scale:.2f}]")

    def perspective(self, fovy, aspect, near, far):
        """Create a perspective projection matrix"""
        f = 1.0 / math.tan(math.radians(fovy) / 2.0)
        return np.array([
            [f/aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far+near)/(near-far), (2*far*near)/(near-far)],
            [0, 0, -1, 0]
        ], dtype=np.float32)

    def lookAt(self, eye, center, up):
        """Create a view matrix using lookAt"""
        f = (center - eye)
        f = f / np.linalg.norm(f)
        
        u = up / np.linalg.norm(up)
        s = np.cross(f, u)
        s = s / np.linalg.norm(s)
        u = np.cross(s, f)
        
        return np.array([
            [s[0], u[0], -f[0], 0],
            [s[1], u[1], -f[1], 0],
            [s[2], u[2], -f[2], 0],
            [-np.dot(s, eye), -np.dot(u, eye), np.dot(f, eye), 1]
        ], dtype=np.float32)

    def rotate(self, angle, x, y, z):
        """Create a rotation matrix around axis (x,y,z) by angle degrees"""
        if angle == 0:
            return np.eye(4, dtype=np.float32)
        
        angle = math.radians(angle)
        c = math.cos(angle)
        s = math.sin(angle)
        axis = np.array([x, y, z], dtype=np.float32)
        axis = axis / np.linalg.norm(axis)
        x, y, z = axis
        
        return np.array([
            [c + x*x*(1-c), x*y*(1-c) - z*s, x*z*(1-c) + y*s, 0],
            [y*x*(1-c) + z*s, c + y*y*(1-c), y*z*(1-c) - x*s, 0],
            [z*x*(1-c) - y*s, z*y*(1-c) + x*s, c + z*z*(1-c), 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        
        # Compile vertex shader
        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, VERT)
        glCompileShader(vs)
        
        # Check vertex shader compilation
        if not glGetShaderiv(vs, GL_COMPILE_STATUS):
            print("Vertex shader error:", glGetShaderInfoLog(vs).decode())
        
        # Compile fragment shader  
        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, FRAG)
        glCompileShader(fs)
        
        # Check fragment shader compilation
        if not glGetShaderiv(fs, GL_COMPILE_STATUS):
            print("Fragment shader error:", glGetShaderInfoLog(fs).decode())
        
        # Link program
        self.program = glCreateProgram()
        glAttachShader(self.program, vs)
        glAttachShader(self.program, fs)
        glLinkProgram(self.program)
        
        # Check program linking
        if not glGetProgramiv(self.program, GL_LINK_STATUS):
            print("Program link error:", glGetProgramInfoLog(self.program).decode())
        
        glDeleteShader(vs)
        glDeleteShader(fs)

        self._gen_mesh()
        self._setup_buffers()
        
        print(f"Generated {len(self.vertices)//6} vertices and {len(self.indices)//3} triangles")

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
        glClearColor(0.0, 0.0, 0.0, 1.0)  # Fondo negro
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.program)

        t = time.time()-self.start
        glUniform1f(glGetUniformLocation(self.program,"u_time"), t)
        glUniform1f(glGetUniformLocation(self.program,"u_amp"), self.amp)
        glUniform1f(glGetUniformLocation(self.program,"u_freq"), self.freq)
        glUniform1f(glGetUniformLocation(self.program,"u_brightness"), self.brightness)

        # Get viewport dimensions for proper aspect ratio
        viewport = glGetIntegerv(GL_VIEWPORT)
        width, height = viewport[2], viewport[3]
        aspect = width / height if height > 0 else 1.0

        # Create transformation matrices
        projection = self.perspective(45, aspect, 0.1, 100.0)
        view = self.lookAt(np.array([0, 3.0, 5.0]), np.array([0,0,0]), np.array([0,1,0]))
        model = self.rotate(0, 0,1,0)
        
        # Transpose matrices for OpenGL (row-major to column-major)
        glUniformMatrix4fv(glGetUniformLocation(self.program,"projection"),1,GL_TRUE,projection)
        glUniformMatrix4fv(glGetUniformLocation(self.program,"view"),1,GL_TRUE,view)
        glUniformMatrix4fv(glGetUniformLocation(self.program,"model"),1,GL_TRUE,model)

        # Enable wireframe or fill mode
        if self.wire==1:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glLineWidth(1.0)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.indices.size, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        self.update()

    def resizeGL(self,w,h): glViewport(0,0,w,h)

    def cleanup(self):
        if self.program: glDeleteProgram(self.program)
        if self.vbo: glDeleteBuffers(1,[self.vbo])
        if self.ebo: glDeleteBuffers(1,[self.ebo])
        if self.vao: glDeleteVertexArrays(1,[self.vao])