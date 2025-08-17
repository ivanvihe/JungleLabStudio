# TODO: migrate to RenderBackend (ModernGL)
# visuals/presets/grid_snake_wave.py
import logging
import numpy as np
import ctypes
import time
import math
import random
from OpenGL.GL import *
from ..base_visualizer import BaseVisualizer

class GridSnakeWaveVisualizer(BaseVisualizer):
    """TouchDesigner-quality grid snake wave visualization with moving squares"""
    
    visual_name = "Grid Snake Wave"
    
    def __init__(self):
        super().__init__()
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.start_time = time.time()
        self.initialized = False

        # Grid snake state
        self.waves = []
        self.max_waves = 2
        
        # Visual parameters
        self.intensity = 1.0
        self.size_multiplier = 1.0
        self.wave_mode = 0  # 0=left-to-right, 1=right-to-left, 2=top-to-bottom, 3=bottom-to-top
        self.grid_size = 20  # Number of squares per row/column
        self.square_fill_ratio = 0.6  # Probability of filled vs outline squares
        
        # Pre-generate data
        self.vertices = None
        self.vertex_count = 0
        
        logging.info("TouchDesigner-quality Grid Snake Wave created")
        
        # Auto-trigger on creation
        self.create_wave()

    def initializeGL(self):
        """Initialize OpenGL resources"""
        try:
            logging.debug("GridSnakeWaveVisualizer.initializeGL called")
            
            # Clear any existing GL errors
            while glGetError() != GL_NO_ERROR:
                pass
            
            # Set up OpenGL state for high quality
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDisable(GL_DEPTH_TEST)
            
            # Load shaders
            if not self.load_shaders():
                logging.error("Failed to load shaders")
                return
            
            # Setup geometry
            if not self.setup_geometry():
                logging.error("Failed to setup geometry")
                return
            
            self.initialized = True
            logging.info("🔲 TouchDesigner-quality grid snake wave initialized")
            
        except Exception as e:
            logging.error(f"Error in initialization: {e}")
            import traceback
            traceback.print_exc()

    def load_shaders(self):
        """Load TouchDesigner-quality grid shaders"""
        try:
            # High-quality vertex shader for grid squares
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoord;
            layout (location = 2) in float aAge;
            layout (location = 3) in vec2 aGridPos;
            layout (location = 4) in vec3 aColor;
            layout (location = 5) in float aFillType;
            layout (location = 6) in float aWaveProgress;
            
            uniform float time;
            uniform float intensity;
            uniform vec2 resolution;
            uniform int waveMode;
            
            out vec2 texCoord;
            out vec3 color;
            out float alpha;
            out vec2 gridPos;
            out float fillType;
            out float age;
            out float waveProgress;
            
            void main()
            {
                gl_Position = vec4(aPos, 0.0, 1.0);
                texCoord = aTexCoord;
                color = aColor;
                gridPos = aGridPos;
                fillType = aFillType;
                age = aAge;
                waveProgress = aWaveProgress;
                
                // Calculate alpha based on wave progress and position
                float fadeIn = smoothstep(0.0, 0.2, waveProgress);
                float fadeOut = 1.0 - smoothstep(0.8, 1.0, waveProgress);
                
                // Additional fade based on age for wave lifetime
                float ageFade = 1.0 - smoothstep(0.0, 3.0, aAge);
                
                alpha = fadeIn * fadeOut * ageFade * intensity;
            }
            """
            
            # TouchDesigner-quality fragment shader for grid squares
            fragment_shader_source = """
            #version 330 core
            in vec2 texCoord;
            in vec3 color;
            in float alpha;
            in vec2 gridPos;
            in float fillType;
            in float age;
            in float waveProgress;
            
            uniform float time;
            uniform vec2 resolution;
            
            out vec4 FragColor;
            
            // High-quality noise functions
            float hash(vec2 p) {
                return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
            }
            
            float noise(vec2 p) {
                vec2 i = floor(p);
                vec2 f = fract(p);
                vec2 u = f * f * (3.0 - 2.0 * f);
                return mix(mix(hash(i + vec2(0.0, 0.0)), 
                              hash(i + vec2(1.0, 0.0)), u.x),
                          mix(hash(i + vec2(0.0, 1.0)), 
                              hash(i + vec2(1.0, 1.0)), u.x), u.y);
            }
            
            // Square rendering function
            float drawSquare(vec2 uv, float fillType) {
                vec2 absUV = abs(uv);
                float squareSize = 0.8; // Size of the square relative to grid cell
                
                if (fillType > 0.5) {
                    // Filled square
                    float square = step(absUV.x, squareSize) * step(absUV.y, squareSize);
                    return square;
                } else {
                    // Outline square
                    float borderWidth = 0.1;
                    float outerSquare = step(absUV.x, squareSize) * step(absUV.y, squareSize);
                    float innerSquare = step(absUV.x, squareSize - borderWidth) * step(absUV.y, squareSize - borderWidth);
                    return outerSquare - innerSquare;
                }
            }
            
            void main()
            {
                // Convert texture coordinates to grid cell coordinates (-1 to 1)
                vec2 uv = (texCoord - 0.5) * 2.0;
                
                // Calculate square intensity
                float squareIntensity = drawSquare(uv, fillType);
                
                // Add some dynamic effects
                float pulse = sin(time * 8.0 + gridPos.x * 2.0 + gridPos.y * 1.5) * 0.1 + 0.9;
                squareIntensity *= pulse;
                
                // Add subtle noise for texture
                float noiseValue = noise(gridPos * 10.0 + time * 2.0) * 0.2 + 0.8;
                squareIntensity *= noiseValue;
                
                // Enhance color based on wave progress
                vec3 finalColor = color;
                
                // Add energy glow at wave front
                float frontGlow = exp(-pow(abs(waveProgress - 0.1) / 0.1, 2.0)) * 0.5;
                if (frontGlow > 0.1) {
                    finalColor = mix(finalColor, vec3(1.0), frontGlow);
                }
                
                // Add trailing glow
                float trailGlow = exp(-pow(waveProgress / 0.3, 2.0)) * 0.3;
                finalColor = mix(finalColor, finalColor * 1.5, trailGlow);
                
                // Discard fragments with negligible intensity
                if (squareIntensity <= 0.001) {
                    discard;
                }

                FragColor = vec4(finalColor, squareIntensity * alpha);
            }
            """
            
            # Compile shaders
            vertex_shader = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex_shader, vertex_shader_source)
            glCompileShader(vertex_shader)
            
            if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vertex_shader).decode()
                logging.error(f"Vertex shader compilation failed: {error}")
                return False
            
            fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment_shader, fragment_shader_source)
            glCompileShader(fragment_shader)
            
            if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fragment_shader).decode()
                logging.error(f"Fragment shader compilation failed: {error}")
                return False
            
            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vertex_shader)
            glAttachShader(self.shader_program, fragment_shader)
            glLinkProgram(self.shader_program)
            
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                logging.error(f"Shader program linking failed: {error}")
                return False
            
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            
            logging.debug("TouchDesigner-quality grid shaders compiled")
            return True
            
        except Exception as e:
            logging.error(f"Error loading shaders: {e}")
            return False

    def setup_geometry(self):
        """Setup vertex data"""
        try:
            # Start empty
            self.vertices = np.array([0.0], dtype=np.float32)
            
            # Create and bind VAO
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)
            
            # Create and bind VBO
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            
            # Reserve space for grid squares
            max_squares = self.grid_size * self.grid_size * self.max_waves
            vertex_size = 12 * 4  # 12 floats per vertex * 4 bytes
            glBufferData(GL_ARRAY_BUFFER, max_squares * vertex_size * 6, None, GL_DYNAMIC_DRAW)
            
            # Set vertex attributes
            stride = 12 * 4  # 12 floats per vertex
            
            # Position (2 floats)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            # Texture coordinates (2 floats)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * 4))
            # Age (1 float)
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(4 * 4))
            # Grid position (2 floats)
            glEnableVertexAttribArray(3)
            glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(5 * 4))
            # Color (3 floats)
            glEnableVertexAttribArray(4)
            glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(7 * 4))
            # Fill type (1 float)
            glEnableVertexAttribArray(5)
            glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(10 * 4))
            # Wave progress (1 float)
            glEnableVertexAttribArray(6)
            glVertexAttribPointer(6, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(11 * 4))
            
            # Unbind
            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            logging.debug("High-quality grid geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up geometry: {e}")
            return False

    def create_wave(self):
        """Create a TouchDesigner-quality grid snake wave"""
        current_time = time.time() - self.start_time
        
        # Remove old waves
        self.waves = [wave for wave in self.waves 
                     if (current_time - wave['birth_time']) < 4.0]
        
        # Don't create if at max
        if len(self.waves) >= self.max_waves:
            self.waves.pop(0)
        
        # Get colors based on mode
        if self.wave_mode == 0 or self.wave_mode == 1:  # Horizontal movement
            base_color = (0.2, 0.8, 1.0)  # Cyan
        else:  # Vertical movement
            base_color = (1.0, 0.4, 0.8)  # Magenta
        
        # Create grid pattern for this wave
        grid_pattern = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                # Random fill type (filled or outline)
                fill_type = 1.0 if random.random() < self.square_fill_ratio else 0.0
                grid_pattern.append({
                    'x': x,
                    'y': y,
                    'fill_type': fill_type
                })
        
        # Create wave
        wave = {
            'birth_time': current_time,
            'color': base_color,
            'grid_pattern': grid_pattern,
            'speed': 1.0 + random.uniform(-0.2, 0.2)
        }
        
        self.waves.append(wave)
        logging.info(f"🔲 TouchDesigner grid snake wave created (mode: {self.wave_mode})")

    def update_vertex_data(self):
        """Update vertex buffer with grid squares"""
        try:
            current_time = time.time() - self.start_time
            vertices = []
            
            for wave in self.waves:
                age = current_time - wave['birth_time']
                
                # Skip old waves
                if age > 4.0:
                    continue
                
                r, g, b = wave['color']
                speed = wave['speed']
                
                # Calculate wave progress based on mode
                wave_progress = (age * speed) % 2.0  # Cycle every 2 seconds
                
                for square in wave['grid_pattern']:
                    grid_x, grid_y = square['x'], square['y']
                    fill_type = square['fill_type']
                    
                    # Calculate normalized grid position (-1 to 1)
                    norm_x = (grid_x / (self.grid_size - 1)) * 2.0 - 1.0
                    norm_y = (grid_y / (self.grid_size - 1)) * 2.0 - 1.0
                    
                    # Calculate square size based on grid
                    square_size = 1.8 / self.grid_size * self.size_multiplier
                    
                    # Calculate position in world space
                    pos_x = norm_x
                    pos_y = norm_y
                    
                    # Calculate wave progress for this square based on movement direction
                    local_progress = 0.0
                    
                    if self.wave_mode == 0:  # Left to right
                        local_progress = (wave_progress + norm_x + 1.0) * 0.5
                    elif self.wave_mode == 1:  # Right to left
                        local_progress = (wave_progress - norm_x + 1.0) * 0.5
                    elif self.wave_mode == 2:  # Top to bottom
                        local_progress = (wave_progress - norm_y + 1.0) * 0.5
                    else:  # Bottom to top
                        local_progress = (wave_progress + norm_y + 1.0) * 0.5
                    
                    # Normalize progress to 0-1 range
                    local_progress = local_progress % 1.0
                    
                    # Skip squares that are not visible yet or already faded
                    if local_progress < 0.0 or local_progress > 1.0:
                        continue
                    
                    # Create quad for this square
                    vertices.extend([
                        # Triangle 1
                        pos_x - square_size, pos_y - square_size, 0.0, 0.0, age, grid_x, grid_y, r, g, b, fill_type, local_progress,
                        pos_x + square_size, pos_y - square_size, 1.0, 0.0, age, grid_x, grid_y, r, g, b, fill_type, local_progress,
                        pos_x - square_size, pos_y + square_size, 0.0, 1.0, age, grid_x, grid_y, r, g, b, fill_type, local_progress,
                        
                        # Triangle 2
                        pos_x + square_size, pos_y - square_size, 1.0, 0.0, age, grid_x, grid_y, r, g, b, fill_type, local_progress,
                        pos_x + square_size, pos_y + square_size, 1.0, 1.0, age, grid_x, grid_y, r, g, b, fill_type, local_progress,
                        pos_x - square_size, pos_y + square_size, 0.0, 1.0, age, grid_x, grid_y, r, g, b, fill_type, local_progress
                    ])
            
            if vertices:
                self.vertices = np.array(vertices, dtype=np.float32)
                self.vertex_count = len(vertices) // 12
                
                # Upload to GPU
                glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
                glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices.nbytes, self.vertices)
                glBindBuffer(GL_ARRAY_BUFFER, 0)
            else:
                self.vertex_count = 0
            
        except Exception as e:
            logging.error(f"Error updating vertex data: {e}")
            self.vertex_count = 0

    def paintGL(self):
        """Render TouchDesigner-quality grid snake wave"""
        try:
            if not self.initialized or not self.shader_program:
                glClearColor(0.0, 0.0, 0.0, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return

            # Clear with transparent background
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)
            
            # Update vertex data
            self.update_vertex_data()

            if self.vertex_count > 0:
                current_time = time.time() - self.start_time
                
                # Use shader program
                glUseProgram(self.shader_program)
                
                # Update uniforms
                glUniform1f(glGetUniformLocation(self.shader_program, "time"), current_time)
                glUniform1f(glGetUniformLocation(self.shader_program, "intensity"), self.intensity)
                glUniform2f(glGetUniformLocation(self.shader_program, "resolution"), 1920.0, 1080.0)
                glUniform1i(glGetUniformLocation(self.shader_program, "waveMode"), self.wave_mode)
                
                # Draw
                if self.vao:
                    glBindVertexArray(self.vao)
                    glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
                    glBindVertexArray(0)
                
                # Clean up
                glUseProgram(0)
            
        except Exception as e:
            # Only log errors occasionally
            if not hasattr(self, '_last_error_time') or \
               time.time() - self._last_error_time > 5:
                logging.error(f"TouchDesigner grid snake paint error: {e}")
                self._last_error_time = time.time()

            # Fallback rendering
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        """Handle resize"""
        glViewport(0, 0, width, height)

    def cleanup(self):
        """Clean up OpenGL resources"""
        try:
            logging.debug("Cleaning up TouchDesigner-quality grid visualizer")
            
            if self.shader_program:
                try:
                    if glIsProgram(self.shader_program):
                        glDeleteProgram(self.shader_program)
                except:
                    pass
                finally:
                    self.shader_program = None
            
            if self.vao:
                try:
                    glDeleteVertexArrays(1, [self.vao])
                except:
                    pass
                finally:
                    self.vao = None
            
            if self.vbo:
                try:
                    glDeleteBuffers(1, [self.vbo])
                except:
                    pass
                finally:
                    self.vbo = None
            
            self.initialized = False
            self.waves = []
            
        except Exception as e:
            logging.debug(f"Cleanup error (non-critical): {e}")

    def get_controls(self):
        """Return available controls"""
        return {
            "Intensity": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.intensity * 100),
                "default": 100
            },
            "Size": {
                "type": "slider",
                "min": 20,
                "max": 300,
                "value": int(self.size_multiplier * 100),
                "default": 100
            },
            "Direction": {
                "type": "slider",
                "min": 0,
                "max": 3,
                "value": self.wave_mode,
                "default": 0
            },
            "Grid Size": {
                "type": "slider",
                "min": 10,
                "max": 40,
                "value": self.grid_size,
                "default": 20
            },
            "Fill Ratio": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.square_fill_ratio * 100),
                "default": 60
            }
        }

    def update_control(self, name, value):
        """Update control values"""
        try:
            if name == "Intensity":
                self.intensity = value / 100.0
            elif name == "Size":
                self.size_multiplier = value / 100.0
            elif name == "Direction":
                self.wave_mode = int(value)
            elif name == "Grid Size":
                self.grid_size = int(value)
            elif name == "Fill Ratio":
                self.square_fill_ratio = value / 100.0
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")

    def trigger_action(self, action_name):
        """Handle MIDI triggers"""
        if action_name == "wave" or action_name == "snake" or action_name == "grid":
            self.create_wave()
            logging.info("🔲 TouchDesigner GRID SNAKE WAVE! Triggered via MIDI")