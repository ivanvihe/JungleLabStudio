# TODO: migrate to RenderBackend (ModernGL)
from OpenGL.GL import *
import numpy as np
import ctypes
import time
import math

from visuals.base_visualizer import BaseVisualizer

class AbstractLinesVisualizer(BaseVisualizer):
    visual_name = "Abstract Lines"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.num_lines = 150
        self.line_data = None
        self.time = 0.0
        self.line_width = 2.0
        self.pulsation_speed = 2.0
        self.complexity = 1.0
        self.initialized = False

    def get_controls(self):
        controls = super().get_controls()
        controls.update({
            "Line Width": {
                "type": "slider",
                "min": 1,
                "max": 5,
                "value": int(self.line_width),
            },
            "Number of Lines": {
                "type": "slider",
                "min": 50,
                "max": 300,
                "value": self.num_lines,
            },
            "Pulsation Speed": {
                "type": "slider",
                "min": 1,
                "max": 100,
                "value": int(self.pulsation_speed * 10),
            },
            "Complexity": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.complexity * 100),
            }
        })
        return controls

    def update_control(self, name, value):
        if super().update_control(name, value):
            return
        if name == "Line Width":
            self.line_width = float(value)
        elif name == "Number of Lines":
            old_lines = self.num_lines
            self.num_lines = int(value)
            if old_lines != self.num_lines:
                self.setup_lines()
        elif name == "Pulsation Speed":
            self.pulsation_speed = float(value) / 10.0
        elif name == "Complexity":
            self.complexity = float(value) / 100.0

    def initializeGL(self):
        print("AbstractLinesVisualizer.initializeGL called")
        # Use working structure but keep some 3D effects
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)  # Keep it simple like working ones
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        
        if not self.load_shaders():
            print("Failed to load shaders")
            return
        
        if not self.setup_lines():
            print("Failed to setup lines")
            return
            
        self.initialized = True
        print("AbstractLines initialized successfully")

    def load_shaders(self):
        try:
            # Simpler shaders that will definitely work, but with epic effects
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec4 aColor;
            layout (location = 2) in float aLineIndex;
            
            uniform float time;
            uniform float pulsation_speed;
            uniform float complexity;
            
            out vec4 vertexColor;
            
            void main()
            {
                vec2 pos = aPos;
                float t = time * pulsation_speed;
                float linePhase = aLineIndex * 0.2;
                
                // EPIC PULSATION - grow from center
                float pulsation = 0.3 + 1.2 * (0.5 + 0.5 * sin(t + linePhase));
                pos *= pulsation;
                
                // SPIRAL FLOW - rotate and move inward/outward
                float angle = atan(pos.y, pos.x);
                float radius = length(pos);
                
                // Add spiral motion
                angle += t * 0.5 + radius * complexity;
                radius *= (0.8 + 0.4 * sin(t * 0.7 + linePhase));
                
                // Convert back to cartesian with epic movement
                pos.x = cos(angle) * radius;
                pos.y = sin(angle) * radius;
                
                // Add wave distortions
                pos.x += sin(pos.y * complexity * 3.0 + t * 2.0) * 0.2;
                pos.y += cos(pos.x * complexity * 2.5 + t * 1.5) * 0.2;
                
                // Rotation for the whole thing
                float globalRotation = t * 0.3;
                float cosR = cos(globalRotation);
                float sinR = sin(globalRotation);
                vec2 rotatedPos = vec2(
                    pos.x * cosR - pos.y * sinR,
                    pos.x * sinR + pos.y * cosR
                );
                
                gl_Position = vec4(rotatedPos, 0.0, 1.0);
                
                // Epic color cycling
                vec4 color = aColor;
                float intensity = 0.5 + 0.5 * pulsation;
                color.rgb *= intensity;
                color.a *= (0.7 + 0.3 * sin(t * 2.0 + linePhase));
                
                vertexColor = color;
            }
            """
            
            fragment_shader_source = """
            #version 330 core
            in vec4 vertexColor;
            out vec4 FragColor;
            
            void main()
            {
                FragColor = vertexColor;
            }
            """

            # Compile shaders
            vertex_shader = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex_shader, vertex_shader_source)
            glCompileShader(vertex_shader)
            
            if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vertex_shader).decode()
                print(f"Vertex Shader Error: {error}")
                return False

            fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment_shader, fragment_shader_source)
            glCompileShader(fragment_shader)
            
            if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fragment_shader).decode()
                print(f"Fragment Shader Error: {error}")
                return False

            # Link program
            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vertex_shader)
            glAttachShader(self.shader_program, fragment_shader)
            glLinkProgram(self.shader_program)
            
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                print(f"Shader Program Link Error: {error}")
                return False

            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            
            print("AbstractLines epic shaders compiled successfully")
            return True
            
        except Exception as e:
            print(f"Error loading shaders: {e}")
            return False

    def setup_lines(self):
        try:
            # Clean up old resources
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
                self.vao = None
            
            # Create epic line patterns in 2D but with awesome effects
            vertices = []
            
            for i in range(self.num_lines):
                line_index = float(i)
                
                # Different epic patterns
                pattern_type = i % 4
                
                if pattern_type == 0:  # Radial lines from center
                    angle = (i / self.num_lines) * 2 * math.pi
                    
                    # Start point (center)
                    x1 = 0.0
                    y1 = 0.0
                    
                    # End point (outside) - BIG
                    x2 = math.cos(angle) * 1.5
                    y2 = math.sin(angle) * 1.5
                    
                elif pattern_type == 1:  # Circular rings
                    angle = (i / self.num_lines) * 8 * math.pi
                    radius = 0.3 + (i % 8) * 0.15
                    
                    x1 = math.cos(angle) * radius
                    y1 = math.sin(angle) * radius
                    
                    x2 = math.cos(angle + 0.3) * radius
                    y2 = math.sin(angle + 0.3) * radius
                    
                elif pattern_type == 2:  # Spiral lines
                    t = i * 0.15
                    spiral_angle = t * 3
                    spiral_radius = t * 0.5
                    
                    x1 = math.cos(spiral_angle) * spiral_radius
                    y1 = math.sin(spiral_angle) * spiral_radius
                    
                    x2 = math.cos(spiral_angle + 0.5) * (spiral_radius + 0.3)
                    y2 = math.sin(spiral_angle + 0.5) * (spiral_radius + 0.3)
                    
                else:  # Cross/star patterns
                    angle1 = i * 0.4
                    angle2 = angle1 + math.pi
                    radius = 0.5 + (i % 5) * 0.2
                    
                    x1 = math.cos(angle1) * radius
                    y1 = math.sin(angle1) * radius
                    
                    x2 = math.cos(angle2) * radius * 0.7
                    y2 = math.sin(angle2) * radius * 0.7
                
                # Epic rainbow colors
                hue_offset = i / self.num_lines
                r1 = 0.5 + 0.5 * math.sin(hue_offset * 6.28)
                g1 = 0.5 + 0.5 * math.sin(hue_offset * 6.28 + 2.094)
                b1 = 0.5 + 0.5 * math.sin(hue_offset * 6.28 + 4.189)
                
                r2 = 0.5 + 0.5 * math.sin(hue_offset * 6.28 + 1.0)
                g2 = 0.5 + 0.5 * math.sin(hue_offset * 6.28 + 3.094)
                b2 = 0.5 + 0.5 * math.sin(hue_offset * 6.28 + 5.189)
                
                alpha = 0.9
                
                # Add line start point: x, y, r, g, b, a, line_index
                vertices.extend([x1, y1, r1, g1, b1, alpha, line_index])
                # Add line end point
                vertices.extend([x2, y2, r2, g2, b2, alpha, line_index])

            self.line_data = np.array(vertices, dtype=np.float32)

            # Create VAO and VBO like working visualizers
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)
            
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, self.line_data.nbytes, self.line_data, GL_DYNAMIC_DRAW)

            # Position attribute (location 0) - 2D
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 7 * 4, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)

            # Color attribute (location 1)
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * 4, ctypes.c_void_p(2 * 4))
            glEnableVertexAttribArray(1)
            
            # Line index attribute (location 2)
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 7 * 4, ctypes.c_void_p(6 * 4))
            glEnableVertexAttribArray(2)

            glBindVertexArray(0)
            
            print(f"AbstractLines epic setup complete with {self.num_lines} lines")
            return True
            
        except Exception as e:
            print(f"Error setting up lines: {e}")
            return False

    def paintGL(self):
        try:
            glClear(GL_COLOR_BUFFER_BIT)
            
            if not self.initialized or not self.shader_program or not self.vao:
                glClearColor(0.1, 0.0, 0.2, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return
                
            # Update animation time
            self.time += 0.016

            # Fetch audio data (bass, mid, treble)
            bass, mid, treble = self.get_audio_bands()

            # Use shader program
            glUseProgram(self.shader_program)

            # Send uniforms with audio-reactive modulation
            glUniform1f(glGetUniformLocation(self.shader_program, "time"), self.time)
            glUniform1f(
                glGetUniformLocation(self.shader_program, "pulsation_speed"),
                self.pulsation_speed * (0.5 + bass),
            )
            glUniform1f(
                glGetUniformLocation(self.shader_program, "complexity"),
                self.complexity * (0.5 + treble),
            )

            # Set line width reacting to mid frequencies
            try:
                glLineWidth(self.line_width * (0.5 + mid))
            except Exception:
                glLineWidth(1.0)
            
            # Draw the epic lines
            if self.vao:
                glBindVertexArray(self.vao)
                glDrawArrays(GL_LINES, 0, self.num_lines * 2)
                glBindVertexArray(0)
            
            glUseProgram(0)
            
        except Exception as e:
            print(f"Error in paintGL: {e}")
            glClearColor(0.2, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def cleanup(self):
        print("Cleaning up AbstractLinesVisualizer")
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