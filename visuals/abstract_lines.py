from OpenGL.GL import *
import numpy as np
import ctypes
import os
import logging

from .base_visualizer import BaseVisualizer

# Import OpenGL safety functions
try:
    from opengl_fixes import OpenGLSafety
except ImportError:
    # Fallback if opengl_fixes is not available
    class OpenGLSafety:
        @staticmethod
        def safe_line_width(width):
            try:
                # Clamp to reasonable range for compatibility
                safe_width = max(1.0, min(width, 5.0))
                glLineWidth(safe_width)
            except Exception as e:
                logging.error(f"Error setting line width: {e}")
                try:
                    glLineWidth(1.0)
                except:
                    pass
        
        @staticmethod
        def check_gl_errors(context=""):
            try:
                error = glGetError()
                if error != GL_NO_ERROR:
                    logging.warning(f"OpenGL error in {context}: {error}")
                return error
            except:
                return GL_NO_ERROR

class AbstractLinesVisualizer(BaseVisualizer):
    visual_name = "Abstract Lines"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.num_lines = 1000
        self.line_data = None
        self.time = 0.0
        self.line_width = 2.0
        self.pulsation_speed = 2.0

    def get_controls(self):
        return {
            "Line Width": {
                "type": "slider",
                "min": 1,
                "max": 5,
                "value": int(self.line_width),
            },
            "Number of Lines": {
                "type": "slider",
                "min": 100,
                "max": 2000,
                "value": self.num_lines,
            },
            "Pulsation Speed": {
                "type": "slider",
                "min": 1,
                "max": 100,
                "value": int(self.pulsation_speed * 10),
            }
        }

    def update_control(self, name, value):
        if name == "Line Width":
            self.line_width = float(value)
        elif name == "Number of Lines":
            old_lines = self.num_lines
            self.num_lines = int(value)
            if old_lines != self.num_lines:
                self.setup_lines()
        elif name == "Pulsation Speed":
            self.pulsation_speed = float(value) / 10.0

    def initializeGL(self):
        print("AbstractLinesVisualizer.initializeGL called")
        # CLEAR WITH TRANSPARENT BACKGROUND
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Load shaders and setup
        if self.load_shaders():
            self.setup_lines()
            print("AbstractLines initialized successfully")
        else:
            print("Failed to initialize AbstractLines shaders")

    def load_shaders(self):
        try:
            # Try to load from files first
            script_dir = os.path.dirname(__file__)
            shader_dir = os.path.join(script_dir, '..', 'shaders')
            
            vertex_src = None
            fragment_src = None
            
            try:
                with open(os.path.join(shader_dir, 'basic.vert'), 'r') as f:
                    vertex_src = f.read()
                with open(os.path.join(shader_dir, 'basic.frag'), 'r') as f:
                    fragment_src = f.read()
            except FileNotFoundError:
                print("Shader files not found, using fallback shaders")
            
            # Fallback shaders if files don't exist
            if not vertex_src:
                vertex_src = """
                #version 330 core
                layout (location = 0) in vec3 aPos;
                layout (location = 1) in vec4 aColor;
                
                uniform mat4 projection;
                uniform mat4 view;
                uniform mat4 model;
                
                out vec4 vColor;
                
                void main()
                {
                    gl_Position = projection * view * model * vec4(aPos, 1.0);
                    vColor = aColor;
                }
                """
            
            if not fragment_src:
                fragment_src = """
                #version 330 core
                in vec4 vColor;
                out vec4 FragColor;
                
                void main()
                {
                    FragColor = vColor;
                }
                """

            # Compile vertex shader
            vertex_shader = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex_shader, vertex_src)
            glCompileShader(vertex_shader)
            
            if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vertex_shader).decode()
                print(f"Vertex Shader Error: {error}")
                return False

            # Compile fragment shader
            fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment_shader, fragment_src)
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

            # Clean up shaders
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            
            print("AbstractLines shaders compiled successfully")
            return True
            
        except Exception as e:
            print(f"Error loading shaders: {e}")
            return False

    def setup_lines(self):
        try:
            # Clean up old resources
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])
                self.VBO = None
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
                self.VAO = None
                
            # Create line data (position + color for each vertex)
            self.line_data = np.zeros((self.num_lines * 2, 7), dtype=np.float32)

            # Generate VAO and VBO
            self.VAO = glGenVertexArrays(1)
            self.VBO = glGenBuffers(1)
            
            glBindVertexArray(self.VAO)
            glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
            glBufferData(GL_ARRAY_BUFFER, self.line_data.nbytes, self.line_data, GL_DYNAMIC_DRAW)

            # Position attribute (location 0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)

            # Color attribute (location 1)
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
            glEnableVertexAttribArray(1)

            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            print(f"AbstractLines buffers created with {self.num_lines} lines")
            
        except Exception as e:
            print(f"Error setting up lines: {e}")

    def update_lines(self):
        if self.line_data is None:
            return
            
        try:
            for i in range(self.num_lines):
                # Create circular pattern with pulsation
                angle = i * (2 * np.pi / self.num_lines)
                
                # Pulsating radius
                base_radius = 1.5
                pulsation = 0.3 + 0.7 * np.sin(self.time * self.pulsation_speed + angle * 2)
                
                # First endpoint
                radius1 = base_radius * pulsation
                x1 = np.cos(angle) * radius1
                y1 = np.sin(angle) * radius1
                z1 = np.sin(self.time + angle * 3) * 0.2
                
                # Second endpoint (slightly rotated and different radius)
                angle2 = angle + 0.1 + np.sin(self.time * 0.5) * 0.2
                radius2 = base_radius * 0.7 * pulsation
                x2 = np.cos(angle2) * radius2
                y2 = np.sin(angle2) * radius2
                z2 = np.cos(self.time * 1.2 + angle * 2) * 0.2

                # Store line endpoints
                self.line_data[i * 2, :3] = [x1, y1, z1]
                self.line_data[i * 2 + 1, :3] = [x2, y2, z2]

                # Color cycling based on time and position
                hue_offset = self.time * 0.5 + angle
                r = 0.5 + 0.5 * np.sin(hue_offset)
                g = 0.5 + 0.5 * np.sin(hue_offset + 2.094)  # 120 degrees
                b = 0.5 + 0.5 * np.sin(hue_offset + 4.189)  # 240 degrees
                alpha = 0.8  # Semi-transparent
                
                # Apply colors to both endpoints
                self.line_data[i * 2, 3:7] = [r, g, b, alpha]
                self.line_data[i * 2 + 1, 3:7] = [r, g, b, alpha]

            # Update the GPU buffer
            glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.line_data.nbytes, self.line_data)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
        except Exception as e:
            print(f"Error updating lines: {e}")

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def paintGL(self):
        try:
            # Clear with transparent background
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            if not self.shader_program or not self.VAO:
                return
                
            # Update animation time
            self.time += 0.016  # Assume ~60fps
            
            # Update line positions and colors
            self.update_lines()
            
            # Use shader program
            glUseProgram(self.shader_program)

            # Set up transformation matrices
            projection = self.create_perspective_matrix(45.0, 1.0, 0.1, 100.0)
            view = self.create_view_matrix()
            model = self.create_model_matrix()

            # Send matrices to shader
            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection)
            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)
            glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)

            # Set line width safely
            OpenGLSafety.safe_line_width(self.line_width)
            
            # Draw the lines
            glBindVertexArray(self.VAO)
            glDrawArrays(GL_LINES, 0, self.num_lines * 2)
            glBindVertexArray(0)
            
            # Clean up
            glUseProgram(0)
            
            # Check for errors
            OpenGLSafety.check_gl_errors("AbstractLines paintGL")
            
        except Exception as e:
            print(f"Error in paintGL: {e}")

    def create_perspective_matrix(self, fov, aspect, near, far):
        """Create perspective projection matrix"""
        f = 1.0 / np.tan(np.radians(fov / 2.0))
        return np.array([
            [f / aspect, 0.0, 0.0, 0.0],
            [0.0, f, 0.0, 0.0],
            [0.0, 0.0, (far + near) / (near - far), (2.0 * far * near) / (near - far)],
            [0.0, 0.0, -1.0, 0.0]
        ], dtype=np.float32)

    def create_view_matrix(self):
        """Create view matrix (camera)"""
        eye = np.array([0.0, 0.0, 5.0])
        center = np.array([0.0, 0.0, 0.0])
        up = np.array([0.0, 1.0, 0.0])
        
        f = center - eye
        f = f / np.linalg.norm(f)
        
        s = np.cross(f, up)
        s = s / np.linalg.norm(s)
        
        u = np.cross(s, f)
        
        return np.array([
            [s[0], u[0], -f[0], 0.0],
            [s[1], u[1], -f[1], 0.0],
            [s[2], u[2], -f[2], 0.0],
            [-np.dot(s, eye), -np.dot(u, eye), np.dot(f, eye), 1.0]
        ], dtype=np.float32)

    def create_model_matrix(self):
        """Create model matrix with rotation"""
        # Rotate around Y and X axes
        rot_y = self.time * 20.0  # degrees
        rot_x = self.time * 15.0  # degrees
        
        # Convert to radians
        ry = np.radians(rot_y)
        rx = np.radians(rot_x)
        
        # Y rotation matrix
        cos_ry, sin_ry = np.cos(ry), np.sin(ry)
        rot_y_mat = np.array([
            [cos_ry, 0, sin_ry, 0],
            [0, 1, 0, 0],
            [-sin_ry, 0, cos_ry, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        # X rotation matrix
        cos_rx, sin_rx = np.cos(rx), np.sin(rx)
        rot_x_mat = np.array([
            [1, 0, 0, 0],
            [0, cos_rx, -sin_rx, 0],
            [0, sin_rx, cos_rx, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        # Combine rotations
        return np.dot(rot_y_mat, rot_x_mat)

    def cleanup(self):
        print("Cleaning up AbstractLinesVisualizer")
        try:
            if self.shader_program:
                glDeleteProgram(self.shader_program)
                self.shader_program = None
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])
                self.VBO = None
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
                self.VAO = None
        except Exception as e:
            print(f"Error during cleanup: {e}")