# kaleido_tunnel.py
from PyQt6.QtGui import QSurfaceFormat
from OpenGL.GL import *
import numpy as np
import ctypes
import time

from .base_visualizer import BaseVisualizer

VERT_SRC = """
#version 330 core
layout(location = 0) in vec2 aPos;
out vec2 vUV;
void main(){
    vUV = (aPos * 0.5) + 0.5;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
"""

FRAG_SRC = """
#version 330 core
in vec2 vUV;
out vec4 FragColor;

uniform float u_time;
uniform int   u_slices;
uniform float u_twist;
uniform float u_speed;
uniform int   u_palette;

float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453123); }
vec3 palette(float t, int mode){
    if(mode==0){ // neon
        return vec3(0.5+0.5*sin(6.2831*(t)+0.0),
                    0.5+0.5*sin(6.2831*(t)+2.0),
                    0.5+0.5*sin(6.2831*(t)+4.0));
    }else if(mode==1){ // ocean
        return vec3(0.1, 0.4+0.3*sin(6.2831*t), 0.7+0.3*sin(6.2831*t*1.3));
    }else{ // fire
        return vec3(0.9, 0.3+0.4*sin(6.2831*t*1.7), 0.1);
    }
}

void main(){
    // Kaleidoscope UV warp
    vec2 uv = vUV * 2.0 - 1.0;          // [-1,1]
    float a = atan(uv.y, uv.x);
    float r = length(uv);
    float slices = float(u_slices);
    a = mod(a, 6.2831853/slices);
    a = abs(a - 3.14159265/slices);
    // Twist + motion
    float t = u_time * u_speed;
    float z = 1.0/(r*0.7 + 0.2);
    float w = a + t*0.2 + r*u_twist;
    // Ring pattern
    float ring = sin(10.0*r - t*3.0 + sin(w*3.0))*0.5+0.5;
    float bands = smoothstep(0.35, 0.9, sin(w*20.0+z*2.0));
    float mixv = clamp(ring*0.7 + bands*0.3, 0.0, 1.0);
    vec3 col = palette(mixv + 0.1*z, u_palette);
    // Vignette
    float vig = smoothstep(1.1, 0.2, r);
    FragColor = vec4(col * vig, 1.0);
}
"""

class KaleidoTunnelVisualizer(BaseVisualizer):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFormat(QSurfaceFormat())
        self.program = None
        self.vao = None
        self.vbo = None
        self.start = time.time()
        self.slices = 8
        self.twist = 0.6
        self.speed = 1.0
        self.palette = 0

    def get_controls(self):
        return {
            "Slices": {"type":"slider","min":3,"max":24,"value":self.slices},
            "Twist": {"type":"slider","min":0,"max":200,"value":int(self.twist*100)},
            "Speed": {"type":"slider","min":10,"max":300,"value":int(self.speed*100)},
            "Palette": {"type":"dropdown","options":["Neon","Ocean","Fire"],"value":self.palette}
        }

    def update_control(self, name, value):
        if name=="Slices": self.slices = int(value)
        elif name=="Twist": self.twist = float(value)/100.0
        elif name=="Speed": self.speed = float(value)/100.0
        elif name=="Palette": self.palette = int(value)

    def initializeGL(self):
        glDisable(GL_DEPTH_TEST)
        # compile shaders
        vs = glCreateShader(GL_VERTEX_SHADER); glShaderSource(vs, VERT_SRC); glCompileShader(vs)
        fs = glCreateShader(GL_FRAGMENT_SHADER); glShaderSource(fs, FRAG_SRC); glCompileShader(fs)
        self.program = glCreateProgram()
        glAttachShader(self.program, vs); glAttachShader(self.program, fs); glLinkProgram(self.program)
        glDeleteShader(vs); glDeleteShader(fs)
        # fullscreen triangle (two tris quad)
        quad = np.array([
            -1.0,-1.0,  1.0,-1.0,  1.0, 1.0,
            -1.0,-1.0,  1.0, 1.0, -1.0, 1.0
        ], dtype=np.float32)
        self.vao = glGenVertexArrays(1); glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1); glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, quad.nbytes, quad, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2*ctypes.sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glBindVertexArray(0)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.program)
        t = (time.time()-self.start)
        glUniform1f(glGetUniformLocation(self.program,"u_time"), t)
        glUniform1i(glGetUniformLocation(self.program,"u_slices"), self.slices)
        glUniform1f(glGetUniformLocation(self.program,"u_twist"), self.twist)
        glUniform1f(glGetUniformLocation(self.program,"u_speed"), self.speed)
        glUniform1i(glGetUniformLocation(self.program,"u_palette"), self.palette)
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        self.update()

    def resizeGL(self,w,h):
        glViewport(0,0,w,h)

    def cleanup(self):
        self.makeCurrent()
        if self.program: glDeleteProgram(self.program)
        if self.vbo: glDeleteBuffers(1, [self.vbo])
        if self.vao: glDeleteVertexArrays(1, [self.vao])
        self.doneCurrent()
