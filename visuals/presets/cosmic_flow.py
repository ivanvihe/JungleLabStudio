from OpenGL.GL import *
import numpy as np
import ctypes
import time
import random

from visuals.base_visualizer import BaseVisualizer

class CosmicFlowVisualizer(BaseVisualizer):
    visual_name = "Cosmic Flow"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.start_time = time.time()
        
        # Starfield parameters
        self.num_stars = 2000
        self.speed = 1.0
        self.star_size = 1.0
        self.color_mode = 0
        self.trail_length = 1.0
        
        self.stars = []
        self.initialized = False

    def get_controls(self):
        return {
            "Speed": {
                "type": "slider",
                "min": 0,
                "max": 500,
                "value": int(self.speed * 100),
            },
            "Star Count": {
                "type": "slider",
                "min": 500,
                "max": 5000,
                "value": self.num_stars,
            },
            "Star Size": {
                "type": "slider",
                "min": 20,
                "max": 300,
                "value": int(self.star_size * 100),
            },
            "Trail Length": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.trail_length * 100),
            },
            "Color Mode": {
                "type": "dropdown",
                "options": ["White Stars", "Rainbow", "Blue Shift", "Fire Nebula", "Crystal Galaxy"],
                "value": self.color_mode,
            }
        }

    def update_control(self, name, value):
        if name == "Speed":
            self.speed = float(value) / 100.0
        elif name == "Star Count":
            old_count = self.num_stars
            self.num_stars = int(value)
            if old_count != self.num_stars:
                self.init_stars()
        elif name == "Star Size":
            self.star_size = float(value) / 100.0
        elif name == "Trail Length":
            self.trail_length = float(value) / 100.0
        elif name == "Color Mode":
            self.color_mode = int(value)

    def initializeGL(self):
        print("CosmicFlowVisualizer.initializeGL called")
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_PROGRAM_POINT_SIZE)
        glDisable(GL_DEPTH_TEST)  # Like working visualizers

        if not self.load_shaders():
            print("Failed to load shaders")
            return
        
        self.init_stars()
        self.setup_buffers()
        self.initialized = True
        print("CosmicFlow initialized successfully")

    def load_shaders(self):
        try:
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec3 aPos;
            layout (location = 1) in vec4 aColor;
            layout (location = 2) in float aSize;
            
            uniform float time;
            uniform float speed;
            uniform float star_size;
            
            out vec4 vertexColor;
            
            void main()
            {
                vec3 pos = aPos;
                
                // Move stars towards viewer (z approaches 0)
                pos.z += time * speed * 2.0;
                
                // Reset stars that pass the camera
                if (pos.z > 1.0) {
                    pos.z = -10.0;
                }
                
                // Create perspective effect
                float perspective = 1.0 / (1.0 - pos.z * 0.1);
                vec2 screen_pos = pos.xy * perspective;
                
                gl_Position = vec4(screen_pos, 0.0, 1.0);
                
                // Size based on distance (closer = bigger)
                float size_factor = perspective * star_size * aSize;
                gl_PointSize = max(1.0, size_factor * 5.0);
                
                // Brightness based on distance
                vec4 color = aColor;
                color.a *= min(1.0, perspective * 0.5);
                
                vertexColor = color;
            }
            """
            
            fragment_shader_source = """
            #version 330 core
            in vec4 vertexColor;
            out vec4 FragColor;
            
            void main()
            {
                // Create circular star shape
                vec2 coord = gl_PointCoord - vec2(0.5);
                float dist = length(coord);
                float alpha = 1.0 - smoothstep(0.1, 0.5, dist);
                
                // Add bright center
                float center = 1.0 - smoothstep(0.0, 0.2, dist);
                alpha = max(alpha * 0.6, center);
                
                FragColor = vec4(vertexColor.rgb, vertexColor.a * alpha);
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
            
            print("CosmicFlow shaders compiled successfully")
            return True
            
        except Exception as e:
            print(f"Error loading shaders: {e}")
            return False

    def init_stars(self):
        """Initialize starfield"""
        self.stars = []
        
        for i in range(self.num_stars):
            star = {
                'x': random.uniform(-2.0, 2.0),
                'y': random.uniform(-2.0, 2.0),
                'z': random.uniform(-10.0, 1.0),
                'size': random.uniform(0.5, 2.0),
                'brightness': random.uniform(0.3, 1.0),
                'color_offset': random.uniform(0, 6.28)
            }
            self.stars.append(star)

    def get_star_color(self, star, time_offset):
        """Get star color based on mode"""
        brightness = star['brightness']
        
        if self.color_mode == 0:  # White Stars
            return [brightness, brightness, brightness, 0.9]
        elif self.color_mode == 1:  # Rainbow
            hue = (star['color_offset'] + time_offset) % 6.28
            r = brightness * (0.5 + 0.5 * np.sin(hue))
            g = brightness * (0.5 + 0.5 * np.sin(hue + 2.09))
            b = brightness * (0.5 + 0.5 * np.sin(hue + 4.18))
            return [r, g, b, 0.9]
        elif self.color_mode == 2:  # Blue Shift
            return [brightness * 0.3, brightness * 0.6, brightness, 0.9]
        elif self.color_mode == 3:  # Fire Nebula
            return [brightness, brightness * 0.5, brightness * 0.1, 0.9]
        else:  # Crystal Galaxy
            crystal = 0.7 + 0.3 * np.sin(time_offset + star['color_offset'])
            return [brightness * 0.8 * crystal, brightness * 0.9 * crystal, brightness * crystal, 0.9]

    def setup_buffers(self):
        try:
            # Clean up old buffers
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
            
            # Create VAO
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)
            
            # Create VBO
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            
            # Each star: pos(3) + color(4) + size(1) = 8 floats
            buffer_size = self.num_stars * 8 * 4
            glBufferData(GL_ARRAY_BUFFER, buffer_size, None, GL_DYNAMIC_DRAW)
            
            # Position attribute
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * 4, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            
            # Color attribute
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 8 * 4, ctypes.c_void_p(3 * 4))
            glEnableVertexAttribArray(1)
            
            # Size attribute
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 8 * 4, ctypes.c_void_p(7 * 4))
            glEnableVertexAttribArray(2)
            
            glBindVertexArray(0)
            
            print("CosmicFlow buffers setup complete")
            return True
            
        except Exception as e:
            print(f"Error setting up buffers: {e}")
            return False

    def update_stars(self, dt):
        """Update star positions"""
        for star in self.stars:
            # Move star towards camera
            star['z'] += dt * self.speed * 2.0
            
            # Reset star if it passes the camera
            if star['z'] > 1.0:
                star['z'] = -10.0
                star['x'] = random.uniform(-2.0, 2.0)
                star['y'] = random.uniform(-2.0, 2.0)

    def paintGL(self):
        try:
            glClear(GL_COLOR_BUFFER_BIT)
            
            if not self.initialized or not self.shader_program:
                glClearColor(0.1, 0.0, 0.2, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return
            
            # Update time
            current_time = time.time() - self.start_time
            dt = 0.016  # Assume 60fps
            
            # Update stars
            self.update_stars(dt)
            
            # Prepare vertex data
            vertex_data = []
            
            for star in self.stars:
                # Position
                vertex_data.extend([star['x'], star['y'], star['z']])
                
                # Color
                color = self.get_star_color(star, current_time)
                vertex_data.extend(color)
                
                # Size
                vertex_data.append(star['size'])
            
            # Update buffer
            vertex_array = np.array(vertex_data, dtype=np.float32)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferSubData(GL_ARRAY_BUFFER, 0, vertex_array.nbytes, vertex_array)
            
            # Render
            glUseProgram(self.shader_program)
            
            # Set uniforms
            glUniform1f(glGetUniformLocation(self.shader_program, "time"), current_time)
            glUniform1f(glGetUniformLocation(self.shader_program, "speed"), self.speed)
            glUniform1f(glGetUniformLocation(self.shader_program, "star_size"), self.star_size)
            
            # Draw stars
            glBindVertexArray(self.vao)
            glDrawArrays(GL_POINTS, 0, len(self.stars))
            glBindVertexArray(0)
            
            glUseProgram(0)
            
        except Exception as e:
            print(f"Error in paintGL: {e}")
            glClearColor(0.2, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def cleanup(self):
        print("Cleaning up CosmicFlowVisualizer")
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
        except Exception as e:
            print(f"Error during cleanup: {e}")