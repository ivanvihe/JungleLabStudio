# visuals/presets/character_train.py
import logging
import numpy as np
import ctypes
import time
import math
import random
import string
from OpenGL.GL import *
from ..base_visualizer import BaseVisualizer

class CharacterTrainVisualizer(BaseVisualizer):
    """One-shot character train visual - lines of characters crossing the screen"""
    
    visual_name = "Character Train"
    
    def __init__(self):
        super().__init__()
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.initialized = False
        
        # Train state
        self.active_trains = []  # List of active character trains
        self.max_trains = 8     # Maximum simultaneous trains
        
        # Train settings
        self.train_length = 25        # Characters per train
        self.train_duration = 4.0     # How long train takes to cross screen
        self.character_spacing = 0.08 # Space between characters
        
        # Visual parameters
        self.speed_multiplier = 1.0
        self.trail_intensity = 1.0
        self.color_mode = 0  # 0=matrix, 1=rainbow, 2=fire
        self.trail_length = 5  # How many characters fade behind
        
        # Character set (same as intro_background)
        self.charset = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        logging.info("CharacterTrainVisualizer created")

    def initializeGL(self):
        """Initialize OpenGL resources"""
        try:
            logging.debug("CharacterTrainVisualizer.initializeGL called")
            
            # Clear GL errors
            while glGetError() != GL_NO_ERROR:
                pass
            
            # Set up OpenGL state
            glClearColor(0.0, 0.0, 0.0, 0.0)  # Transparent background
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDisable(GL_DEPTH_TEST)
            
            # Load shaders
            if not self.load_shaders():
                logging.error("Failed to load shaders")
                return
            
            # Setup geometry
            if not self.setup_character_geometry():
                logging.error("Failed to setup character geometry")
                return
            
            self.initialized = True
            logging.info("✅ CharacterTrainVisualizer initialized successfully")
            
        except Exception as e:
            logging.error(f"Error in CharacterTrainVisualizer.initializeGL: {e}")
            import traceback
            traceback.print_exc()

    def load_shaders(self):
        """Load and compile shaders for character rendering"""
        try:
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;           // Character quad position
            layout (location = 1) in vec2 aTexCoord;      // Texture coordinates
            layout (location = 2) in float aCharCode;     // Character code
            layout (location = 3) in float aCharIndex;    // Index in train
            layout (location = 4) in float aTrainId;      // Train ID
            
            uniform float time;
            uniform float speedMultiplier;
            uniform float trailIntensity;
            uniform int colorMode;
            
            // Train data (up to 8 trains)
            uniform float trainStartTimes[8];
            uniform vec2 trainStartPos[8];
            uniform vec2 trainDirection[8];
            uniform float trainSpeeds[8];
            uniform int trainActive[8];
            
            out vec2 texCoord;
            out float charCode;
            out vec3 charColor;
            out float charAlpha;
            
            void main()
            {
                int trainId = int(aTrainId);
                
                // Check if train is active
                if (trainId >= 8 || trainActive[trainId] == 0) {
                    gl_Position = vec4(10.0, 10.0, 10.0, 1.0); // Move offscreen
                    charAlpha = 0.0;
                    return;
                }
                
                float trainTime = time - trainStartTimes[trainId];
                
                // Calculate character position along train path
                vec2 direction = trainDirection[trainId];
                float trainSpeed = trainSpeeds[trainId] * speedMultiplier;
                
                // Position of train head
                vec2 trainHead = trainStartPos[trainId] + direction * trainSpeed * trainTime;
                
                // Position of this character (behind the head)
                float charOffset = aCharIndex * 0.08; // Character spacing
                vec2 charPos = trainHead - direction * charOffset;
                
                // Add character quad offset
                vec2 finalPos = charPos + aPos * 0.03; // Character size
                
                gl_Position = vec4(finalPos, 0.0, 1.0);
                
                texCoord = aTexCoord;
                charCode = aCharCode;
                
                // Calculate trail effect (characters fade based on distance from head)
                float distanceFromHead = aCharIndex;
                float trailFade = 1.0 - smoothstep(0.0, float(5), distanceFromHead); // Trail length of 5
                trailFade = pow(trailFade, 2.0); // More dramatic falloff
                
                // Color based on mode
                vec3 baseColor;
                if (colorMode == 0) {
                    // Matrix green
                    baseColor = vec3(0.0, 1.0, 0.2);
                } else if (colorMode == 1) {
                    // Rainbow based on character and time
                    float hue = fract(aCharCode * 0.1 + trainTime * 0.5);
                    baseColor = vec3(
                        0.5 + 0.5 * sin(hue * 6.28318),
                        0.5 + 0.5 * sin(hue * 6.28318 + 2.094),
                        0.5 + 0.5 * sin(hue * 6.28318 + 4.189)
                    );
                } else {
                    // Fire colors
                    float heat = 1.0 - distanceFromHead / 5.0;
                    baseColor = vec3(1.0, heat * 0.8, heat * 0.3);
                }
                
                charColor = baseColor;
                charAlpha = trailFade * trailIntensity;
                
                // Add brightness variation
                float brightness = 0.8 + 0.4 * sin(time * 3.0 + aCharCode);
                charColor *= brightness;
            }
            """
            
            fragment_shader_source = """
            #version 330 core
            in vec2 texCoord;
            in float charCode;
            in vec3 charColor;
            in float charAlpha;
            
            out vec4 FragColor;
            
            // Simple character rendering function
            float drawChar(vec2 uv, float c) {
                vec2 p = uv * 2.0 - 1.0; // Convert to -1,1 range
                
                float char_alpha = 0.0;
                
                // Different patterns for different character codes
                float char_mod = mod(c, 12.0);
                
                if (char_mod < 2.0) {
                    // Rectangle pattern
                    char_alpha = step(abs(p.x), 0.6) * step(abs(p.y), 0.8);
                } else if (char_mod < 4.0) {
                    // Circle pattern
                    char_alpha = 1.0 - smoothstep(0.4, 0.6, length(p));
                } else if (char_mod < 6.0) {
                    // Cross pattern
                    char_alpha = step(abs(p.x), 0.2) + step(abs(p.y), 0.2);
                } else if (char_mod < 8.0) {
                    // Diagonal lines
                    float d1 = abs(p.x - p.y);
                    float d2 = abs(p.x + p.y);
                    char_alpha = step(d1, 0.2) + step(d2, 0.2);
                } else if (char_mod < 10.0) {
                    // Dots pattern
                    vec2 grid = floor(p * 3.0);
                    char_alpha = step(mod(grid.x + grid.y, 2.0), 0.5);
                } else {
                    // Complex pattern
                    float r = length(p);
                    float a = atan(p.y, p.x);
                    char_alpha = step(abs(sin(a * 4.0 + r * 8.0)), 0.3);
                }
                
                return clamp(char_alpha, 0.0, 1.0);
            }
            
            void main()
            {
                float char_alpha = drawChar(texCoord, charCode);
                
                vec3 finalColor = charColor;
                float finalAlpha = char_alpha * charAlpha;
                
                // Add glow effect
                float glow = 1.0 + 0.5 * (1.0 - length(texCoord - vec2(0.5)));
                finalColor *= glow;
                
                FragColor = vec4(finalColor, finalAlpha);
            }
            """
            
            # Compile vertex shader
            vertex_shader = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex_shader, vertex_shader_source)
            glCompileShader(vertex_shader)
            
            if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(vertex_shader).decode()
                logging.error(f"Vertex shader compilation failed: {error}")
                return False
            
            # Compile fragment shader
            fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment_shader, fragment_shader_source)
            glCompileShader(fragment_shader)
            
            if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(fragment_shader).decode()
                logging.error(f"Fragment shader compilation failed: {error}")
                return False
            
            # Link program
            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vertex_shader)
            glAttachShader(self.shader_program, fragment_shader)
            glLinkProgram(self.shader_program)
            
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(self.shader_program).decode()
                logging.error(f"Shader program linking failed: {error}")
                return False
            
            # Clean up shaders
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            
            logging.debug("CharacterTrainVisualizer shaders compiled successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error loading shaders: {e}")
            return False

    def setup_character_geometry(self):
        """Setup vertex data for character quads"""
        try:
            # Create VAO and VBO (we'll update VBO data per frame)
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)
            
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            
            # Reserve space for maximum characters across all trains
            max_chars = self.max_trains * self.train_length * 6  # 6 vertices per character quad
            vertex_size = 7 * 4  # 7 floats per vertex * 4 bytes
            glBufferData(GL_ARRAY_BUFFER, max_chars * vertex_size, None, GL_DYNAMIC_DRAW)
            
            # Set vertex attributes
            stride = 7 * 4  # 7 floats per vertex
            
            # Position (2 floats)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            
            # Texture coordinates (2 floats)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * 4))
            
            # Character code (1 float)
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(4 * 4))
            
            # Character index (1 float)
            glEnableVertexAttribArray(3)
            glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(5 * 4))
            
            # Train ID (1 float)
            glEnableVertexAttribArray(4)
            glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * 4))
            
            # Unbind
            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            logging.debug("Character geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up character geometry: {e}")
            return False

    def create_train(self, start_x=None, start_y=None, direction=None):
        """Create a new character train"""
        current_time = time.time()
        
        # Remove old trains
        self.active_trains = [train for train in self.active_trains 
                             if (current_time - train['start_time']) < train['duration']]
        
        # Don't create new train if we're at max
        if len(self.active_trains) >= self.max_trains:
            self.active_trains.pop(0)  # Remove oldest
        
        # Determine train path (random if not specified)
        if direction is None:
            # Choose random direction: horizontal or vertical
            if random.choice([True, False]):
                # Horizontal movement
                if random.choice([True, False]):
                    # Left to right
                    start_x = -1.2
                    start_y = random.uniform(-0.8, 0.8)
                    direction = (1.0, 0.0)
                else:
                    # Right to left
                    start_x = 1.2
                    start_y = random.uniform(-0.8, 0.8)
                    direction = (-1.0, 0.0)
            else:
                # Vertical movement
                if random.choice([True, False]):
                    # Top to bottom
                    start_x = random.uniform(-0.8, 0.8)
                    start_y = 1.2
                    direction = (0.0, -1.0)
                else:
                    # Bottom to top
                    start_x = random.uniform(-0.8, 0.8)
                    start_y = -1.2
                    direction = (0.0, 1.0)
        
        # Use provided values if given
        if start_x is None:
            start_x = random.uniform(-1.0, 1.0)
        if start_y is None:
            start_y = random.uniform(-1.0, 1.0)
        
        # Generate random characters for this train
        characters = [random.choice(self.charset) for _ in range(self.train_length)]
        
        # Create train data
        train = {
            'start_pos': (start_x, start_y),
            'direction': direction,
            'start_time': current_time,
            'duration': self.train_duration,
            'speed': random.uniform(0.4, 0.8),  # Base speed
            'characters': characters,
            'train_id': len(self.active_trains)  # Use current length as ID
        }
        
        self.active_trains.append(train)
        direction_str = "horizontal" if abs(direction[0]) > abs(direction[1]) else "vertical"
        logging.info(f"🚂 Created {direction_str} character train at ({start_x:.2f}, {start_y:.2f})")

    def update_character_buffer(self):
        """Update the character buffer with current train data"""
        try:
            vertices = []
            
            for train_idx, train in enumerate(self.active_trains):
                for char_idx, char in enumerate(train['characters']):
                    char_code = ord(char)
                    
                    # Create quad for this character (2 triangles = 6 vertices)
                    # Each vertex: pos(2) + texcoord(2) + charcode(1) + charidx(1) + trainid(1)
                    
                    # Triangle 1
                    vertices.extend([
                        -0.5, -0.5, 0.0, 0.0, float(char_code), float(char_idx), float(train_idx),  # Bottom-left
                         0.5, -0.5, 1.0, 0.0, float(char_code), float(char_idx), float(train_idx),  # Bottom-right
                        -0.5,  0.5, 0.0, 1.0, float(char_code), float(char_idx), float(train_idx)   # Top-left
                    ])
                    
                    # Triangle 2
                    vertices.extend([
                         0.5, -0.5, 1.0, 0.0, float(char_code), float(char_idx), float(train_idx),  # Bottom-right
                         0.5,  0.5, 1.0, 1.0, float(char_code), float(char_idx), float(train_idx),  # Top-right
                        -0.5,  0.5, 0.0, 1.0, float(char_code), float(char_idx), float(train_idx)   # Top-left
                    ])
            
            if vertices:
                vertex_data = np.array(vertices, dtype=np.float32)
                
                glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
                glBufferSubData(GL_ARRAY_BUFFER, 0, vertex_data.nbytes, vertex_data)
                glBindBuffer(GL_ARRAY_BUFFER, 0)
                
                return len(vertices) // 7  # Number of vertices
            
            return 0
            
        except Exception as e:
            logging.error(f"Error updating character buffer: {e}")
            return 0

    def paintGL(self):
        """Render the character trains"""
        try:
            if not self.initialized or not self.shader_program or not self.vao:
                glClearColor(0.0, 0.0, 0.0, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return

            # Clear with transparent background
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)
            
            # Update character data
            vertex_count = self.update_character_buffer()
            
            if vertex_count > 0 and self.active_trains:
                current_time = time.time()
                
                # Use shader program
                glUseProgram(self.shader_program)
                
                # Set uniforms
                glUniform1f(glGetUniformLocation(self.shader_program, "time"), current_time)
                glUniform1f(glGetUniformLocation(self.shader_program, "speedMultiplier"), self.speed_multiplier)
                glUniform1f(glGetUniformLocation(self.shader_program, "trailIntensity"), self.trail_intensity)
                glUniform1i(glGetUniformLocation(self.shader_program, "colorMode"), self.color_mode)
                
                # Prepare train data arrays
                start_times = [0.0] * 8
                start_positions = [0.0] * 16  # 8 trains * 2 components
                directions = [0.0] * 16       # 8 trains * 2 components
                speeds = [0.0] * 8
                active_flags = [0] * 8
                
                for i, train in enumerate(self.active_trains[:8]):  # Max 8 trains
                    start_times[i] = train['start_time']
                    start_positions[i*2] = train['start_pos'][0]
                    start_positions[i*2+1] = train['start_pos'][1]
                    directions[i*2] = train['direction'][0]
                    directions[i*2+1] = train['direction'][1]
                    speeds[i] = train['speed']
                    active_flags[i] = 1
                
                # Set uniform arrays
                glUniform1fv(glGetUniformLocation(self.shader_program, "trainStartTimes"), 8, start_times)
                glUniform2fv(glGetUniformLocation(self.shader_program, "trainStartPos"), 8, start_positions)
                glUniform2fv(glGetUniformLocation(self.shader_program, "trainDirection"), 8, directions)
                glUniform1fv(glGetUniformLocation(self.shader_program, "trainSpeeds"), 8, speeds)
                glUniform1iv(glGetUniformLocation(self.shader_program, "trainActive"), 8, active_flags)
                
                # Draw all characters
                glBindVertexArray(self.vao)
                glDrawArrays(GL_TRIANGLES, 0, vertex_count)
                glBindVertexArray(0)
                
                glUseProgram(0)
            
        except Exception as e:
            if not hasattr(self, '_last_error_time') or time.time() - self._last_error_time > 5:
                logging.error(f"CharacterTrain paint error: {e}")
                self._last_error_time = time.time()
            
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        """Handle resize"""
        glViewport(0, 0, width, height)

    def cleanup(self):
        """Clean up OpenGL resources"""
        try:
            logging.debug("Cleaning up CharacterTrainVisualizer")
            
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
            self.active_trains = []
            
        except Exception as e:
            logging.debug(f"Cleanup error (non-critical): {e}")

    def get_controls(self):
        """Return available controls"""
        return {
            "Speed": {
                "type": "slider",
                "min": 20,
                "max": 300,
                "value": int(self.speed_multiplier * 100),
                "default": 100
            },
            "Trail Intensity": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.trail_intensity * 100),
                "default": 100
            },
            "Train Length": {
                "type": "slider",
                "min": 10,
                "max": 50,
                "value": self.train_length,
                "default": 25
            },
            "Duration": {
                "type": "slider",
                "min": 20,
                "max": 100,
                "value": int(self.train_duration * 10),
                "default": 40
            },
            "Color Mode": {
                "type": "slider",
                "min": 0,
                "max": 2,
                "value": self.color_mode,
                "default": 0
            }
        }

    def update_control(self, name, value):
        """Update control values"""
        try:
            if name == "Speed":
                self.speed_multiplier = value / 100.0
            elif name == "Trail Intensity":
                self.trail_intensity = value / 100.0
            elif name == "Train Length":
                self.train_length = int(value)
            elif name == "Duration":
                self.train_duration = value / 10.0
            elif name == "Color Mode":
                self.color_mode = int(value)
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")

    def trigger_action(self, action_name):
        """Handle MIDI triggers"""
        if action_name == "train" or action_name == "character_train":
            self.create_train()
            logging.info("🚂 Character train triggered via MIDI")