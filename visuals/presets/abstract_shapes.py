# TODO: migrate to RenderBackend (ModernGL)
from OpenGL.GL import *
import numpy as np
import ctypes
import time
import math

from visuals.base_visualizer import BaseVisualizer

class AbstractShapesVisualizer(BaseVisualizer):
    visual_name = "Abstract Shapes"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.EBO = None
        self.num_shapes = 20
        self.shape_data = None
        self.index_data = None
        self.time = 0.0
        self.rotation_speed = 1.0
        self.shape_type = 0
        self.pulsation = 1.0
        self.complexity = 1.0
        self.initialized = False

    def get_controls(self):
        return {
            "Rotation Speed": {
                "type": "slider",
                "min": 0,
                "max": 200,
                "value": int(self.rotation_speed * 100),
            },
            "Shape Type": {
                "type": "dropdown",
                "options": ["Triangle", "Quad", "Pentagon", "Hexagon", "Star"],
                "value": self.shape_type,
            },
            "Number of Shapes": {
                "type": "slider",
                "min": 5,
                "max": 100,
                "value": self.num_shapes,
            },
            "Pulsation": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.pulsation * 100),
            },
            "Complexity": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.complexity * 100),
            }
        }

    def update_control(self, name, value):
        if name == "Rotation Speed":
            self.rotation_speed = float(value) / 100.0
        elif name == "Shape Type":
            if self.shape_type != value:
                self.shape_type = value
                self.setup_shapes()
        elif name == "Number of Shapes":
            if self.num_shapes != int(value):
                self.num_shapes = int(value)
                self.setup_shapes()
        elif name == "Pulsation":
            self.pulsation = float(value) / 100.0
        elif name == "Complexity":
            self.complexity = float(value) / 100.0

    def initializeGL(self):
        print("AbstractShapesVisualizer.initializeGL called")
        # Use working structure like AbstractLines
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)  # Keep it simple like working ones

        if not self.load_shaders():
            print("Failed to load shaders")
            return
        
        if not self.setup_shapes():
            print("Failed to setup shapes")
            return
            
        self.initialized = True
        print("AbstractShapes initialized successfully")

    def load_shaders(self):
        try:
            # Epic 2D shaders with awesome effects
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec4 aColor;
            layout (location = 2) in float aShapeIndex;
            
            uniform float time;
            uniform float rotation_speed;
            uniform float pulsation;
            uniform float complexity;
            
            out vec4 vertexColor;
            
            void main()
            {
                vec2 pos = aPos;
                float t = time * rotation_speed;
                float shapePhase = aShapeIndex * 0.3;
                
                // EPIC PULSATION - shapes grow and shrink dramatically
                float pulse = 0.4 + 1.2 * pulsation * (0.5 + 0.5 * sin(t * 2.0 + shapePhase));
                pos *= pulse;
                
                // ORBITAL MOTION - each shape orbits around center
                float orbitAngle = t + shapePhase;
                float orbitRadius = 0.3 + aShapeIndex * 0.05;
                vec2 orbitCenter = vec2(
                    cos(orbitAngle * 0.7) * orbitRadius,
                    sin(orbitAngle * 0.5) * orbitRadius
                );
                pos += orbitCenter;
                
                // ROTATION - individual shape rotation
                float shapeRotation = t * 3.0 + shapePhase * complexity;
                float cosR = cos(shapeRotation);
                float sinR = sin(shapeRotation);
                vec2 rotatedPos = vec2(
                    pos.x * cosR - pos.y * sinR,
                    pos.x * sinR + pos.y * cosR
                );
                
                // WAVE DISTORTIONS - epic deformations
                rotatedPos.x += sin(rotatedPos.y * complexity * 4.0 + t * 3.0) * 0.1;
                rotatedPos.y += cos(rotatedPos.x * complexity * 3.0 + t * 2.5) * 0.1;
                
                // GLOBAL ROTATION - everything spins together
                float globalRot = t * 0.5;
                float cosG = cos(globalRot);
                float sinG = sin(globalRot);
                vec2 finalPos = vec2(
                    rotatedPos.x * cosG - rotatedPos.y * sinG,
                    rotatedPos.x * sinG + rotatedPos.y * cosG
                );
                
                gl_Position = vec4(finalPos, 0.0, 1.0);
                
                // Epic color effects
                vec4 color = aColor;
                float intensity = 0.5 + 0.5 * pulse;
                color.rgb *= intensity;
                color.a *= (0.7 + 0.3 * sin(t * 4.0 + shapePhase));
                
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

            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vertex_shader)
            glAttachShader(self.shader_program, fragment_shader)
            glLinkProgram(self.shader_program)
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                print(f"Shader Program Error: {error}")
                return False

            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            print("AbstractShapes epic shaders loaded successfully")
            return True
        except Exception as e:
            print(f"AbstractShapes shader loading error: {e}")
            return False

    def create_shape_vertices(self, shape_type, center_x, center_y, size, color, shape_index):
        """Create vertices for different shape types"""
        vertices = []
        indices = []
        base_index = shape_index * 20  # Assume max 20 vertices per shape
        
        if shape_type == 0:  # Triangle
            angles = [0, 2*math.pi/3, 4*math.pi/3]
            for i, angle in enumerate(angles):
                x = center_x + math.cos(angle) * size
                y = center_y + math.sin(angle) * size
                vertices.extend([x, y, color[0], color[1], color[2], color[3], shape_index])
            indices.extend([base_index, base_index + 1, base_index + 2])
            
        elif shape_type == 1:  # Quad
            corners = [(-size, -size), (size, -size), (size, size), (-size, size)]
            for corner in corners:
                x = center_x + corner[0]
                y = center_y + corner[1]
                vertices.extend([x, y, color[0], color[1], color[2], color[3], shape_index])
            indices.extend([base_index, base_index + 1, base_index + 2])
            indices.extend([base_index, base_index + 2, base_index + 3])
            
        elif shape_type == 2:  # Pentagon
            for i in range(5):
                angle = i * 2 * math.pi / 5
                x = center_x + math.cos(angle) * size
                y = center_y + math.sin(angle) * size
                vertices.extend([x, y, color[0], color[1], color[2], color[3], shape_index])
            # Fan triangulation from center
            vertices.extend([center_x, center_y, color[0], color[1], color[2], color[3], shape_index])
            center_idx = base_index + 5
            for i in range(5):
                indices.extend([center_idx, base_index + i, base_index + (i + 1) % 5])
                
        elif shape_type == 3:  # Hexagon
            for i in range(6):
                angle = i * 2 * math.pi / 6
                x = center_x + math.cos(angle) * size
                y = center_y + math.sin(angle) * size
                vertices.extend([x, y, color[0], color[1], color[2], color[3], shape_index])
            # Fan triangulation from center
            vertices.extend([center_x, center_y, color[0], color[1], color[2], color[3], shape_index])
            center_idx = base_index + 6
            for i in range(6):
                indices.extend([center_idx, base_index + i, base_index + (i + 1) % 6])
                
        else:  # Star (5-pointed)
            for i in range(10):  # 5 outer + 5 inner points
                angle = i * math.pi / 5
                radius = size if i % 2 == 0 else size * 0.4  # Alternate outer/inner
                x = center_x + math.cos(angle) * radius
                y = center_y + math.sin(angle) * radius
                vertices.extend([x, y, color[0], color[1], color[2], color[3], shape_index])
            # Fan triangulation from center
            vertices.extend([center_x, center_y, color[0], color[1], color[2], color[3], shape_index])
            center_idx = base_index + 10
            for i in range(10):
                indices.extend([center_idx, base_index + i, base_index + (i + 1) % 10])
        
        return vertices, indices

    def setup_shapes(self):
        try:
            # Clean up old buffers
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])
                self.VBO = None
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
                self.VAO = None
            if self.EBO:
                glDeleteBuffers(1, [self.EBO])
                self.EBO = None

            vertices = []
            indices = []
            
            for i in range(self.num_shapes):
                # Position shapes in different patterns
                if i < 10:  # Circle pattern
                    angle = (i / 10) * 2 * math.pi
                    center_x = math.cos(angle) * 0.6
                    center_y = math.sin(angle) * 0.6
                elif i < 20:  # Grid pattern
                    grid_idx = i - 10
                    center_x = (grid_idx % 3 - 1) * 0.8
                    center_y = (grid_idx // 3 - 1) * 0.8
                else:  # Random pattern
                    center_x = (i * 0.7843) % 2.0 - 1.0  # Pseudo-random
                    center_y = (i * 0.5671) % 2.0 - 1.0
                
                # Size variation
                size = 0.08 + (i % 5) * 0.02
                
                # Epic rainbow colors per shape
                hue = i / self.num_shapes
                r = 0.5 + 0.5 * math.sin(hue * 6.28)
                g = 0.5 + 0.5 * math.sin(hue * 6.28 + 2.094)
                b = 0.5 + 0.5 * math.sin(hue * 6.28 + 4.189)
                color = [r, g, b, 0.8]
                
                shape_verts, shape_indices = self.create_shape_vertices(
                    self.shape_type, center_x, center_y, size, color, float(i)
                )
                
                # Adjust indices for global vertex array
                vertex_offset = len(vertices) // 7  # 7 floats per vertex
                adjusted_indices = [idx + vertex_offset for idx in shape_indices]
                
                vertices.extend(shape_verts)
                indices.extend(adjusted_indices)

            self.shape_data = np.array(vertices, dtype=np.float32)
            self.index_data = np.array(indices, dtype=np.uint32)

            self.VAO = glGenVertexArrays(1)
            glBindVertexArray(self.VAO)

            self.VBO = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
            glBufferData(GL_ARRAY_BUFFER, self.shape_data.nbytes, self.shape_data, GL_STATIC_DRAW)

            # Position attribute (location 0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 7 * 4, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)

            # Color attribute (location 1)
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * 4, ctypes.c_void_p(2 * 4))
            glEnableVertexAttribArray(1)
            
            # Shape index attribute (location 2)
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 7 * 4, ctypes.c_void_p(6 * 4))
            glEnableVertexAttribArray(2)

            self.EBO = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_data.nbytes, self.index_data, GL_STATIC_DRAW)

            glBindVertexArray(0)
            print(f"AbstractShapes setup complete with {self.num_shapes} shapes of type {self.shape_type}")
            return True
        except Exception as e:
            print(f"Error setting up shapes: {e}")
            return False

    def paintGL(self):
        try:
            glClear(GL_COLOR_BUFFER_BIT)
            
            if not self.initialized or not self.shader_program or not self.VAO:
                glClearColor(0.1, 0.0, 0.2, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return
                
            self.time += 0.016
            
            glUseProgram(self.shader_program)

            # Send uniforms
            glUniform1f(glGetUniformLocation(self.shader_program, "time"), self.time)
            glUniform1f(glGetUniformLocation(self.shader_program, "rotation_speed"), self.rotation_speed)
            glUniform1f(glGetUniformLocation(self.shader_program, "pulsation"), self.pulsation)
            glUniform1f(glGetUniformLocation(self.shader_program, "complexity"), self.complexity)

            glBindVertexArray(self.VAO)
            glDrawElements(GL_TRIANGLES, len(self.index_data), GL_UNSIGNED_INT, None)
            glBindVertexArray(0)
            
            glUseProgram(0)
        except Exception as e:
            print(f"Error in paintGL: {e}")
            glClearColor(0.2, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def cleanup(self):
        print("Cleaning up AbstractShapesVisualizer")
        try:
            if self.shader_program:
                if glIsProgram(self.shader_program):
                    glDeleteProgram(self.shader_program)
                self.shader_program = None
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])
                self.VBO = None
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
                self.VAO = None
            if self.EBO:
                glDeleteBuffers(1, [self.EBO])
                self.EBO = None
        except Exception as e:
            print(f"Error during cleanup: {e}")