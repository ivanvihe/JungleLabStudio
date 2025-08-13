from OpenGL.GL import *
import numpy as np
import ctypes
import os
import time

from .base_visualizer import BaseVisualizer

# Inline shaders similar to wire_terrain
VERT_SHADER = """
#version 330 core
layout(location=0) in vec3 aPos;
layout(location=1) in vec4 aColor;
uniform mat4 projection, view, model;
uniform float u_time;
uniform float u_flow_speed;
uniform float u_swirl_strength;
out vec4 vColor;

void main(){
    vec3 pos = aPos;
    
    // Add flow movement
    float flow_time = u_time * u_flow_speed;
    
    // Radial flow from left-center
    vec2 flow_center = vec2(-3.0, 0.0);
    vec2 to_center = flow_center - pos.xy;
    float distance = length(to_center);
    
    if (distance > 0.1) {
        vec2 radial_dir = -to_center / distance;
        // Add swirl
        vec2 perpendicular = vec2(-radial_dir.y, radial_dir.x);
        vec2 flow_force = radial_dir + perpendicular * u_swirl_strength * 0.5;
        pos.xy += flow_force * sin(flow_time + pos.x * 0.5) * 0.3;
    }
    
    // Add turbulence
    pos.x += sin(pos.y * 0.5 + flow_time * 2.0) * 0.2;
    pos.y += cos(pos.x * 0.7 + flow_time * 1.5) * 0.2;
    pos.z += sin(pos.x * 1.2 + flow_time * 1.8) * 0.1;
    
    vColor = aColor;
    gl_Position = projection * view * model * vec4(pos, 1.0);
    gl_PointSize = 8.0 + sin(flow_time + pos.x) * 3.0;
}
"""

FRAG_SHADER = """
#version 330 core
in vec4 vColor;
out vec4 FragColor;
uniform float u_brightness;

void main(){
    // Create circular points for cosmic effect
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
    
    FragColor = vec4(vColor.rgb * u_brightness, vColor.a * alpha * 0.8);
}
"""

class CosmicFlowVisualizer(BaseVisualizer):
    visual_name = "Cosmic Flow"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.program = None
        self.vao = None
        self.vbo = None
        self.start_time = time.time()
        
        # Flow elements
        self.num_elements = 800
        self.flow_speed = 1.0
        self.element_size = 1.0
        self.flow_intensity = 1.0
        self.color_palette = 0
        self.element_density = 1.0
        self.swirl_strength = 0.5
        self.brightness = 1.2
        
        self.vertices = None

    def get_controls(self):
        return {
            "Flow Speed": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.flow_speed * 100),
            },
            "Element Size": {
                "type": "slider",
                "min": 50,
                "max": 200,
                "value": int(self.element_size * 100),
            },
            "Flow Intensity": {
                "type": "slider",
                "min": 20,
                "max": 200,
                "value": int(self.flow_intensity * 100),
            },
            "Element Density": {
                "type": "slider",
                "min": 50,
                "max": 200,
                "value": int(self.element_density * 100),
            },
            "Swirl Strength": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.swirl_strength * 100),
            },
            "Brightness": {
                "type": "slider",
                "min": 50,
                "max": 300,
                "value": int(self.brightness * 100),
            },
            "Color Palette": {
                "type": "dropdown",
                "options": ["Cosmic Magenta", "Deep Space", "Aurora Flow", "Fire Nebula", "Crystal Galaxy"],
                "value": self.color_palette,
            }
        }

    def update_control(self, name, value):
        if name == "Flow Speed":
            self.flow_speed = float(value) / 100.0
        elif name == "Element Size":
            self.element_size = float(value) / 100.0
        elif name == "Flow Intensity":
            self.flow_intensity = float(value) / 100.0
        elif name == "Element Density":
            old_density = self.element_density
            self.element_density = float(value) / 100.0
            if abs(old_density - self.element_density) > 0.1:
                self.num_elements = int(800 * self.element_density)
                self._generate_elements()
                self._setup_buffers()
        elif name == "Swirl Strength":
            self.swirl_strength = float(value) / 100.0
        elif name == "Brightness":
            self.brightness = float(value) / 100.0
        elif name == "Color Palette":
            self.color_palette = int(value)
            self._generate_elements()
            self._setup_buffers()

    def _generate_elements(self):
        """Generate flowing cosmic elements as points"""
        elements = []
        
        for i in range(self.num_elements):
            # Create flow path from left-center radiating outward
            angle = np.random.uniform(-np.pi/3, np.pi/3)
            
            # Initial position along the flow
            x = -6.0 + np.random.uniform(-2, 1)
            y = np.random.uniform(-3, 3)
            z = np.random.uniform(-2, 2)
            
            # Color based on palette and position
            r, g, b, a = self._get_element_color(x, y, i)
            
            elements.extend([x, y, z, r, g, b, a])
        
        self.vertices = np.array(elements, dtype=np.float32)

    def _get_element_color(self, x, y, index):
        """Get color based on palette and element properties"""
        brightness = np.random.uniform(0.5, 1.0)
        
        if self.color_palette == 0:  # Cosmic Magenta
            # Magenta to blue gradient based on position
            x_factor = (x + 6) / 12  # normalize to 0-1
            
            r = brightness * (0.9 - x_factor * 0.6)  # More magenta on left
            g = brightness * (0.2 + brightness * 0.3)
            b = brightness * (0.7 + x_factor * 0.3)  # More blue on right
            
            # Golden elements occasionally
            if brightness > 0.8 and index % 7 == 0:
                r, g, b = brightness * 1.0, brightness * 0.7, brightness * 0.1
                
        elif self.color_palette == 1:  # Deep Space
            r = brightness * 0.1
            g = brightness * (0.3 + np.random.uniform(0, 0.4))
            b = brightness * (0.8 + np.random.uniform(0, 0.2))
            
        elif self.color_palette == 2:  # Aurora Flow
            wave = np.sin(index * 0.1)
            r = brightness * (0.2 + wave * 0.3)
            g = brightness * (0.8 + wave * 0.2)
            b = brightness * (0.6 + wave * 0.4)
            
        elif self.color_palette == 3:  # Fire Nebula
            r = brightness * 0.9
            g = brightness * np.random.uniform(0.3, 0.8)
            b = brightness * np.random.uniform(0.1, 0.3)
            
        else:  # Crystal Galaxy
            crystal_glow = 0.7 + 0.3 * np.sin(index * 0.05)
            r = brightness * 0.8 * crystal_glow
            g = brightness * 0.9 * crystal_glow
            b = brightness * crystal_glow
        
        alpha = 0.8 * brightness
        return r, g, b, alpha

    def perspective(self, fovy, aspect, near, far):
        """Create a perspective projection matrix"""
        f = 1.0 / np.tan(np.radians(fovy) / 2.0)
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

    def initializeGL(self):
        print("CosmicFlowVisualizer.initializeGL called")
        # TRANSPARENT BACKGROUND FOR MIXING
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_PROGRAM_POINT_SIZE)  # Enable point size in shader
        
        # Compile vertex shader
        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, VERT_SHADER)
        glCompileShader(vs)
        
        # Check vertex shader compilation
        if not glGetShaderiv(vs, GL_COMPILE_STATUS):
            print("Vertex shader error:", glGetShaderInfoLog(vs).decode())
        
        # Compile fragment shader  
        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, FRAG_SHADER)
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

        self._generate_elements()
        self._setup_buffers()
        
        print(f"Generated {len(self.vertices)//7} cosmic flow elements")

    def _setup_buffers(self):
        if self.vao: 
            glDeleteVertexArrays(1, [self.vao])
        if self.vbo: 
            glDeleteBuffers(1, [self.vbo])

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)
        
        stride = 7 * ctypes.sizeof(GLfloat)
        
        # Position attribute
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # Color attribute
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(1)
        
        glBindVertexArray(0)

    def paintGL(self):
        # CLEAR WITH TRANSPARENT BACKGROUND
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if not self.program:
            return
            
        glUseProgram(self.program)

        # Update time and uniforms
        current_time = time.time() - self.start_time
        glUniform1f(glGetUniformLocation(self.program, "u_time"), current_time)
        glUniform1f(glGetUniformLocation(self.program, "u_flow_speed"), self.flow_speed)
        glUniform1f(glGetUniformLocation(self.program, "u_swirl_strength"), self.swirl_strength)
        glUniform1f(glGetUniformLocation(self.program, "u_brightness"), self.brightness)

        # Create transformation matrices - fixed view like the reference
        projection = self.perspective(45, 1.0, 0.1, 100.0)
        view = self.lookAt(np.array([0, 0, 10]), np.array([0, 0, 0]), np.array([0, 1, 0]))
        model = np.eye(4, dtype=np.float32)
        
        # Transpose matrices for OpenGL (row-major to column-major)
        glUniformMatrix4fv(glGetUniformLocation(self.program, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(self.program, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(self.program, "model"), 1, GL_TRUE, model)

        # Draw points
        glBindVertexArray(self.vao)
        glDrawArrays(GL_POINTS, 0, self.num_elements)
        glBindVertexArray(0)

    def resizeGL(self, width, height): 
        glViewport(0, 0, width, height)

    def cleanup(self):
        print("Cleaning up CosmicFlowVisualizer")
        try:
            if self.program: 
                glDeleteProgram(self.program)
                self.program = None
            if self.vbo: 
                glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.vao: 
                glDeleteVertexArrays(1, [self.vao])
                self.vao = None
        except Exception as e:
            print(f"Error during cleanup: {e}")