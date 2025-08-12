# vortex_particles.py
from PyQt6.QtGui import QSurfaceFormat
from OpenGL.GL import *
import numpy as np
import ctypes
import time

from .base_visualizer import BaseVisualizer

VERT = """
#version 330 core
layout(location=0) in vec3 aPos;
layout(location=1) in float aSize;
layout(location=2) in float aPhase;

uniform mat4 projection, view, model;
uniform float u_time;
uniform float u_spin;
uniform float u_spread;

out float vPhase;
void main(){
    // spin around Y
    float ang = u_time*0.5*u_spin + aPhase;
    mat2 R = mat2(cos(ang), -sin(ang), sin(ang), cos(ang));
    vec2 xy = R * aPos.xz;
    vec3 p = vec3(xy.x, aPos.y, xy.y);
    p.xy *= (1.0 + u_spread*0.5*sin(u_time*0.7 + aPhase));
    gl_Position = projection * view * model * vec4(p,1.0);
    gl_PointSize = aSize;
    vPhase = aPhase;
}
"""

FRAG = """
#version 330 core
in float vPhase;
out vec4 FragColor;
uniform float u_time;
uniform int   u_palette;

vec3 pal(float t, int m){
    if(m==0) return vec3(0.6+0.4*sin(t), 0.4+0.6*sin(t+2.1), 1.0);
    if(m==1) return vec3(0.9, 0.5+0.5*sin(t*1.7), 0.2);
    return vec3(0.2, 0.9, 0.6+0.4*sin(t*2.0));
}
void main(){
    // soft circular falloff
    vec2 uv = gl_PointCoord*2.0 - 1.0;
    float d = dot(uv,uv);
    float alpha = smoothstep(1.0, 0.0, d);
    vec3 col = pal(u_time + vPhase, u_palette);
    FragColor = vec4(col, alpha);
}
"""

class VortexParticlesVisualizer(BaseVisualizer):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFormat(QSurfaceFormat())
        self.program = None
        self.vao = None
        self.vbo = None
        self.count = 2000
        self.spin = 1.0
        self.spread = 0.6
        self.palette = 0
        self.start = time.time()

    def get_controls(self):
        return {
            "Count": {"type":"slider","min":300,"max":8000,"value":self.count},
            "Spin": {"type":"slider","min":10,"max":300,"value":int(self.spin*100)},
            "Spread": {"type":"slider","min":0,"max":200,"value":int(self.spread*100)},
            "Palette": {"type":"dropdown","options":["Neon","Fire","Mint"],"value":self.palette},
        }

    def update_control(self, name, value):
        if name=="Count": self.count = int(value); self._spawn(); self._setup()
        elif name=="Spin": self.spin = float(value)/100.0
        elif name=="Spread": self.spread = float(value)/100.0
        elif name=="Palette": self.palette = int(value)

    def _spawn(self):
        # pos (3) + size (1) + phase (1)
        r = np.random.rand(self.count).astype(np.float32)
        theta = np.random.rand(self.count).astype(np.float32)*np.pi*2
        y = (np.random.rand(self.count).astype(np.float32)-0.5)*1.6
        rad = 0.2 + 2.8*r
        x = rad*np.cos(theta); z = rad*np.sin(theta)
        pos = np.stack([x, y, z], axis=1).astype(np.float32)
        size = (2.0 + 3.0*(1.0-r)).astype(np.float32)
        phase = (np.random.rand(self.count).astype(np.float32)*6.2831853)
        self.data = np.zeros((self.count, 5), dtype=np.float32)
        self.data[:,0:3] = pos
        self.data[:,3] = size
        self.data[:,4] = phase

    def initializeGL(self):
        glEnable(GL_PROGRAM_POINT_SIZE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        self._spawn()
        # compile
        vs = glCreateShader(GL_VERTEX_SHADER); glShaderSource(vs, VERT); glCompileShader(vs)
        fs = glCreateShader(GL_FRAGMENT_SHADER); glShaderSource(fs, FRAG); glCompileShader(fs)
        self.program = glCreateProgram()
        glAttachShader(self.program, vs); glAttachShader(self.program, fs); glLinkProgram(self.program)
        glDeleteShader(vs); glDeleteShader(fs)
        self._setup()

    def _setup(self):
        if self.vao: glDeleteVertexArrays(1,[self.vao])
        if self.vbo: glDeleteBuffers(1,[self.vbo])
        self.vao = glGenVertexArrays(1); glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1); glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.data.nbytes, self.data, GL_DYNAMIC_DRAW)
        stride = 5*ctypes.sizeof(GLfloat)
        glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(0)); glEnableVertexAttribArray(0)
        glVertexAttribPointer(1,1,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(3*ctypes.sizeof(GLfloat))); glEnableVertexAttribArray(1)
        glVertexAttribPointer(2,1,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(4*ctypes.sizeof(GLfloat))); glEnableVertexAttribArray(2)
        glBindVertexArray(0)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.program)
        t = time.time()-self.start
        glUniform1f(glGetUniformLocation(self.program,"u_time"), t)
        glUniform1f(glGetUniformLocation(self.program,"u_spin"), self.spin)
        glUniform1f(glGetUniformLocation(self.program,"u_spread"), self.spread)
        glUniform1i(glGetUniformLocation(self.program,"u_palette"), self.palette)

        projection = self.perspective(60, 1.0, 0.1, 100.0)
        view = self.lookAt(np.array([0, 0.6, 6.0]), np.array([0,0,0]), np.array([0,1,0]))
        model = np.identity(4, dtype=np.float32)
        glUniformMatrix4fv(glGetUniformLocation(self.program,"projection"),1,GL_FALSE,projection)
        glUniformMatrix4fv(glGetUniformLocation(self.program,"view"),1,GL_FALSE,view)
        glUniformMatrix4fv(glGetUniformLocation(self.program,"model"),1,GL_FALSE,model)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_POINTS, 0, self.count)
        glBindVertexArray(0)
        self.update()

    def resizeGL(self,w,h): glViewport(0,0,w,h)

    def cleanup(self):
        self.makeCurrent()
        if self.program: glDeleteProgram(self.program)
        if self.vbo: glDeleteBuffers(1,[self.vbo])
        if self.vao: glDeleteVertexArrays(1,[self.vao])
        self.doneCurrent()
