# TODO: migrate to RenderBackend (ModernGL)
from OpenGL.GL import *
import numpy as np
import ctypes
import time
import math

from visuals.base_visualizer import BaseVisualizer

class MobiusBandVisualizer(BaseVisualizer):
    # Use ASCII-only name to match configuration files and avoid lookup mismatches
    visual_name = "Mobius Band"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.ebo = None
        self.start_time = time.time()

        # Simple parameters
        self.u_segments = 50  # Around the band
        self.v_segments = 12  # Across the band
        self.amplitude = 0.2
        self.frequency = 1.0
        self.speed = 1.0
        self.wireframe = True

        self.vertices = None
        self.indices = None
        self.initialized = False

    def get_controls(self):
        return {
            "U Segments": {"type": "slider", "min": 20, "max": 80, "value": self.u_segments},
            "V Segments": {"type": "slider", "min": 8, "max": 24, "value": self.v_segments},
            "Amplitude": {"type": "slider", "min": 10, "max": 200, "value": int(self.amplitude * 100)},
            "Frequency": {"type": "slider", "min": 10, "max": 300, "value": int(self.frequency * 100)},
            "Speed": {"type": "slider", "min": 0, "max": 300, "value": int(self.speed * 100)},
            "Wireframe": {"type": "dropdown", "options": ["Off", "On"], "value": int(self.wireframe)}
        }

    def update_control(self, name, value):
        if name == "U Segments":
            old_u = self.u_segments
            self.u_segments = int(value)
            if old_u != self.u_segments:
                self.generate_mobius()
        elif name == "V Segments":
            old_v = self.v_segments
            self.v_segments = int(value)
            if old_v != self.v_segments:
                self.generate_mobius()
        elif name == "Amplitude":
            self.amplitude = float(value) / 100.0
        elif name == "Frequency":
            self.frequency = float(value) / 100.0
        elif name == "Speed":
            self.speed = float(value) / 100.0
        elif name == "Wireframe":
            self.wireframe = bool(value)

    def initializeGL(self):
        print("MobiusBandVisualizer.initializeGL called")
        # Setup exactly like wire_terrain
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)

        if not self.load_shaders():
            print("Failed to load shaders")
            return
        
        if not self.generate_mobius():
            print("Failed to generate Mobius band")
            return
            
        self.initialized = True
        print("MobiusBand initialized successfully")

    def load_shaders(self):
        try:
            # EXACT same shaders as wire_terrain
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec3 aPos;
            layout (location = 1) in vec3 aColor;
            
            uniform mat4 projection;
            uniform mat4 view;
            uniform mat4 model;
            uniform float time;
            uniform float amplitude;
            uniform float frequency;
            
            out vec3 vertexColor;
            
            void main()
            {
                vec3 pos = aPos;
                
                // Conveyor belt flowing waves
                float wave = sin(pos.x * frequency + time) * cos(pos.z * frequency * 1.1 + time * 0.8);
                pos.y += wave * amplitude;
                
                gl_Position = projection * view * model * vec4(pos, 1.0);
                
                // Color flows like a conveyor belt
                float height_factor = (wave * amplitude + amplitude) / (2.0 * amplitude);
                vertexColor = aColor * (0.5 + 0.5 * height_factor);
            }
            """
            
            fragment_shader_source = """
            #version 330 core
            in vec3 vertexColor;
            out vec4 FragColor;
            
            void main()
            {
                FragColor = vec4(vertexColor, 0.8);
            }
            """
            
            # Compile vertex shader
            vertex_shader = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex_shader, vertex_shader_source)
            glCompileShader(vertex_shader)
            
            if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vertex_shader).decode()
                print(f"Vertex shader error: {error}")
                return False
            
            # Compile fragment shader
            fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment_shader, fragment_shader_source)
            glCompileShader(fragment_shader)
            
            if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fragment_shader).decode()
                print(f"Fragment shader error: {error}")
                return False
            
            # Link program
            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vertex_shader)
            glAttachShader(self.shader_program, fragment_shader)
            glLinkProgram(self.shader_program)
            
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                print(f"Shader program error: {error}")
                return False
            
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            
            print("MobiusBand shaders compiled successfully")
            return True
            
        except Exception as e:
            print(f"Error loading shaders: {e}")
            return False

    def generate_mobius(self):
        try:
            vertices = []
            indices = []
            
            print(f"Generating Mobius band with {self.u_segments}x{self.v_segments} segments")

            # Generate Mobius band vertices - MUCH BIGGER for visibility
            for i in range(self.u_segments + 1):
                u = (i / self.u_segments) * 2 * math.pi  # 0 to 2π
                
                for j in range(self.v_segments + 1):
                    v = ((j / self.v_segments) - 0.5) * 2.0  # -1.0 to 1.0 (width)
                    
                    # Mobius band parametric equations - VISIBLE SIZE
                    radius = 2.0 + v * math.cos(u / 2.0) * 0.5  # Normal size
                    x = radius * math.cos(u)  # Full size X
                    y = radius * math.sin(u)  # Full size Y  
                    z = v * math.sin(u / 2.0) * 0.5  # Full size Z
                    
                    # Color gradient like wire_terrain
                    r = 0.2 + 0.6 * (i / self.u_segments)
                    g = 0.4 + 0.4 * (j / self.v_segments)
                    b = 0.8
                    
                    # EXACT same format as wire_terrain: x, y, z, r, g, b (6 floats)
                    vertices.extend([x, y, z, r, g, b])
            
            # Generate indices EXACTLY like wire_terrain
            for i in range(self.u_segments):
                for j in range(self.v_segments):
                    # Get the four corners of the current quad
                    top_left = i * (self.v_segments + 1) + j
                    top_right = top_left + 1
                    bottom_left = (i + 1) * (self.v_segments + 1) + j
                    bottom_right = bottom_left + 1
                    
                    # Handle Mobius wrapping for last segment
                    if i == self.u_segments - 1:
                        # Connect to first segment with flipped v for Mobius topology
                        bottom_left = (self.v_segments - j)
                        bottom_right = bottom_left + 1
                        if j == 0:  # Special case for edge
                            bottom_right = self.v_segments
                    
                    # Two triangles per quad
                    indices.extend([top_left, bottom_left, top_right])
                    indices.extend([top_right, bottom_left, bottom_right])
            
            self.vertices = np.array(vertices, dtype=np.float32)
            self.indices = np.array(indices, dtype=np.uint32)
            
            print(f"Generated Mobius: {len(vertices)//6} vertices, {len(indices)//3} triangles")
            print(f"Vertex range X: {self.vertices[::6].min():.2f} to {self.vertices[::6].max():.2f}")
            print(f"Vertex range Y: {self.vertices[1::6].min():.2f} to {self.vertices[1::6].max():.2f}")
            print(f"Vertex range Z: {self.vertices[2::6].min():.2f} to {self.vertices[2::6].max():.2f}")
            
            return self.setup_buffers()
            
        except Exception as e:
            print(f"Error generating Mobius band: {e}")
            return False

    def setup_buffers(self):
        try:
            # Clean up old buffers
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
            if self.ebo:
                glDeleteBuffers(1, [self.ebo])
            
            # Create VAO
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)
            
            # Create VBO
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
            
            # Create EBO
            self.ebo = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
            
            # Set vertex attributes EXACTLY like wire_terrain
            # Position
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * 4, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            # Color
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * 4, ctypes.c_void_p(3 * 4))
            glEnableVertexAttribArray(1)
            
            glBindVertexArray(0)
            
            print("MobiusBand buffers setup complete")
            return True
            
        except Exception as e:
            print(f"Error setting up buffers: {e}")
            return False

    def paintGL(self):
        try:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            if not self.initialized or not self.shader_program:
                glClearColor(0.1, 0.0, 0.2, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return
            
            glUseProgram(self.shader_program)
            
            # Update time
            current_time = time.time() - self.start_time
            
            # Set uniforms EXACTLY like wire_terrain
            glUniform1f(glGetUniformLocation(self.shader_program, "time"), current_time * self.speed)
            glUniform1f(glGetUniformLocation(self.shader_program, "amplitude"), self.amplitude)
            glUniform1f(glGetUniformLocation(self.shader_program, "frequency"), self.frequency)
            
            # Set up matrices - SIMPLE AND WORKING
            projection = self.perspective(45, 1.0, 0.1, 100.0)
            view = self.lookAt([0, 3, 8], [0, 0, 0], [0, 1, 0])  # Back to known working position
            model = self.rotateY(current_time * 10)  # Simple rotation like wire_terrain
            
            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection)
            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)
            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)
            
            # Set wireframe mode EXACTLY like wire_terrain
            if self.wireframe:
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                try:
                    glLineWidth(1.0)
                except:
                    pass
            else:
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            
            # Draw Mobius band
            if self.vao:
                glBindVertexArray(self.vao)
                glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
                glBindVertexArray(0)
            
            # Reset polygon mode
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glUseProgram(0)
            
        except Exception as e:
            print(f"Error in paintGL: {e}")
            glClearColor(0.2, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def perspective(self, fov, aspect, near, far):
        f = 1.0 / math.tan(math.radians(fov / 2.0))
        return np.array([
            [f / aspect, 0.0, 0.0, 0.0],
            [0.0, f, 0.0, 0.0],
            [0.0, 0.0, (far + near) / (near - far), -1.0],
            [0.0, 0.0, (2.0 * far * near) / (near - far), 0.0]
        ], dtype=np.float32)

    def lookAt(self, eye, center, up):
        eye = np.array(eye, dtype=np.float32)
        center = np.array(center, dtype=np.float32)
        up = np.array(up, dtype=np.float32)
        
        f = (center - eye) / np.linalg.norm(center - eye)
        s = np.cross(f, up) / np.linalg.norm(np.cross(f, up))
        u = np.cross(s, f)

        return np.array([
            [s[0], u[0], -f[0], 0.0],
            [s[1], u[1], -f[1], 0.0],
            [s[2], u[2], -f[2], 0.0],
            [-np.dot(s, eye), -np.dot(u, eye), np.dot(f, eye), 1.0]
        ], dtype=np.float32).T

    def rotateY(self, angle):
        angle = math.radians(angle)
        c, s = math.cos(angle), math.sin(angle)
        return np.array([
            [c, 0, s, 0],
            [0, 1, 0, 0],
            [-s, 0, c, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def cleanup(self):
        print("Cleaning up MobiusBandVisualizer")
        try:
            if self.shader_program:
                if glIsProgram(self.shader_program):
                    glDeleteProgram(self.shader_program)
                self.shader_program = None
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
                self.vao = None
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.ebo:
                glDeleteBuffers(1, [self.ebo])
                self.ebo = None
        except Exception as e:
            print(f"Error during cleanup: {e}")