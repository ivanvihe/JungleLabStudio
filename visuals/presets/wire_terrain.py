# TODO: migrate to RenderBackend (ModernGL)
from OpenGL.GL import *
import numpy as np
import ctypes
import time
import math

from visuals.base_visualizer import BaseVisualizer

class WireTerrainVisualizer(BaseVisualizer):
    visual_name = "Wire Terrain"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.ebo = None
        self.start_time = time.time()

        self.grid_size = 60
        self.amplitude = 0.5
        self.frequency = 1.0
        self.speed = 1.0
        self.wireframe = True

        self.vertices = None
        self.indices = None
        self.initialized = False

    def get_controls(self):
        return {
            "Grid Size": {"type": "slider", "min": 20, "max": 100, "value": self.grid_size},
            "Amplitude": {"type": "slider", "min": 10, "max": 200, "value": int(self.amplitude * 100)},
            "Frequency": {"type": "slider", "min": 10, "max": 300, "value": int(self.frequency * 100)},
            "Speed": {"type": "slider", "min": 0, "max": 300, "value": int(self.speed * 100)},
            "Wireframe": {"type": "dropdown", "options": ["Off", "On"], "value": int(self.wireframe)}
        }

    def update_control(self, name, value):
        if name == "Grid Size":
            old_size = self.grid_size
            self.grid_size = int(value)
            if old_size != self.grid_size:
                self.generate_terrain()
        elif name == "Amplitude":
            self.amplitude = float(value) / 100.0
        elif name == "Frequency":
            self.frequency = float(value) / 100.0
        elif name == "Speed":
            self.speed = float(value) / 100.0
        elif name == "Wireframe":
            self.wireframe = bool(value)

    def initializeGL(self):
        print("WireTerrainVisualizer.initializeGL called")
        # Setup like working visualizers
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)

        if not self.load_shaders():
            print("Failed to load shaders")
            return
        
        if not self.generate_terrain():
            print("Failed to generate terrain")
            return
            
        self.initialized = True
        print("WireTerrain initialized successfully")

    def load_shaders(self):
        try:
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
                
                // Add wave animation
                float wave = sin(pos.x * frequency + time) * cos(pos.z * frequency * 1.1 + time * 0.8);
                pos.y += wave * amplitude;
                
                gl_Position = projection * view * model * vec4(pos, 1.0);
                
                // Color based on height
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
            
            print("WireTerrain shaders compiled successfully")
            return True
            
        except Exception as e:
            print(f"Error loading shaders: {e}")
            return False

    def generate_terrain(self):
        try:
            vertices = []
            indices = []
            
            scale = 4.0 / self.grid_size
            
            # Generate grid vertices
            for z in range(self.grid_size):
                for x in range(self.grid_size):
                    pos_x = (x - self.grid_size/2) * scale
                    pos_z = (z - self.grid_size/2) * scale
                    pos_y = 0.0
                    
                    # Color gradient
                    r = 0.2 + 0.6 * (x / self.grid_size)
                    g = 0.4 + 0.4 * (z / self.grid_size)
                    b = 0.8
                    
                    vertices.extend([pos_x, pos_y, pos_z, r, g, b])
            
            # Generate indices for triangles
            for z in range(self.grid_size - 1):
                for x in range(self.grid_size - 1):
                    # Get the four corners of the current quad
                    top_left = z * self.grid_size + x
                    top_right = top_left + 1
                    bottom_left = (z + 1) * self.grid_size + x
                    bottom_right = bottom_left + 1
                    
                    # Two triangles per quad
                    indices.extend([top_left, bottom_left, top_right])
                    indices.extend([top_right, bottom_left, bottom_right])
            
            self.vertices = np.array(vertices, dtype=np.float32)
            self.indices = np.array(indices, dtype=np.uint32)
            
            return self.setup_buffers()
            
        except Exception as e:
            print(f"Error generating terrain: {e}")
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
            
            # Set vertex attributes
            # Position
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * 4, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            # Color
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * 4, ctypes.c_void_p(3 * 4))
            glEnableVertexAttribArray(1)
            
            glBindVertexArray(0)
            
            print("WireTerrain buffers setup complete")
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
            
            # Set uniforms
            glUniform1f(glGetUniformLocation(self.shader_program, "time"), current_time * self.speed)
            glUniform1f(glGetUniformLocation(self.shader_program, "amplitude"), self.amplitude)
            glUniform1f(glGetUniformLocation(self.shader_program, "frequency"), self.frequency)
            
            # Set up matrices
            projection = self.perspective(45, 1.0, 0.1, 100.0)
            view = self.lookAt([0, 2, 5], [0, 0, 0], [0, 1, 0])
            model = self.rotateY(current_time * 10)
            
            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection)
            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)
            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)
            
            # Set wireframe mode
            if self.wireframe:
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                try:
                    glLineWidth(1.0)
                except:
                    pass
            else:
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            
            # Draw terrain
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
        print("Cleaning up WireTerrainVisualizer")
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