# visuals/presets/oneshot_boomexplosion.py
import logging
import numpy as np
import ctypes
import time
import math
import random
from OpenGL.GL import *
from ..base_visualizer import BaseVisualizer

class OneshotBoomExplosionVisualizer(BaseVisualizer):
    """One-shot explosion visual for dramatic booms and bass drops"""
    
    visual_name = "Oneshot Boom Explosion"
    
    def __init__(self):
        super().__init__()
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.initialized = False

        # Explosion state
        self.explosions = []  # List of active explosions
        self.max_explosions = 5  # Maximum simultaneous explosions
        
        # Particle settings
        self.particles_per_explosion = 200
        self.explosion_duration = 3.0  # How long explosion lasts
        self.fade_duration = 1.5       # How long fade-out takes
        
        # Visual parameters
        self.intensity = 1.0
        self.size_multiplier = 1.0
        self.color_mode = 0  # 0=fire, 1=electric, 2=rainbow

        # Use relative timing to avoid float precision issues in shaders
        self.start_time = time.time()
        
        logging.info("OneshotBoomExplosionVisualizer created")

    def initializeGL(self):
        """Initialize OpenGL resources"""
        try:
            logging.debug("OneshotBoomExplosionVisualizer.initializeGL called")
            
            # Clear GL errors
            while glGetError() != GL_NO_ERROR:
                pass
            
            # Set up OpenGL state
            glClearColor(0.0, 0.0, 0.0, 0.0)  # Transparent background
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending for glow effect
            glDisable(GL_DEPTH_TEST)
            glEnable(GL_PROGRAM_POINT_SIZE)  # Allow shader to control point size
            
            # Load shaders
            if not self.load_shaders():
                logging.error("Failed to load shaders")
                return
            
            # Setup geometry
            if not self.setup_particle_geometry():
                logging.error("Failed to setup particle geometry")
                return

            # Reset start time when GL is ready
            self.start_time = time.time()
            self.initialized = True
            logging.info("✅ OneshotBoomExplosionVisualizer initialized successfully")
            
        except Exception as e:
            logging.error(f"Error in OneshotBoomExplosionVisualizer.initializeGL: {e}")
            import traceback
            traceback.print_exc()

    def load_shaders(self):
        """Load and compile shaders for particle explosion"""
        try:
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec3 aInitialPos;     // Initial position
            layout (location = 1) in vec3 aVelocity;       // Initial velocity
            layout (location = 2) in float aLifetime;      // Total lifetime
            layout (location = 3) in float aBirthTime;     // When particle was born
            layout (location = 4) in vec3 aColor;          // Particle color
            layout (location = 5) in float aSize;          // Initial size
            
            uniform float time;
            uniform float intensity;
            uniform float sizeMultiplier;
            uniform vec2 explosionCenter;
            uniform float explosionTime;
            uniform float explosionDuration;
            
            out vec3 particleColor;
            out float particleAlpha;
            
            void main()
            {
                float age = time - aBirthTime;
                float normalizedAge = age / aLifetime;
                
                // Only render if particle is alive and explosion is active
                if (age < 0.0 || normalizedAge > 1.0 || (time - explosionTime) > explosionDuration) {
                    gl_Position = vec4(10.0, 10.0, 10.0, 1.0); // Move offscreen
                    particleAlpha = 0.0;
                    return;
                }
                
                // Calculate position with physics
                vec3 pos = aInitialPos;
                
                // Add velocity over time with gravity
                pos += aVelocity * age;
                pos.y -= 0.5 * 9.81 * 0.1 * age * age; // Gravity effect
                
                // Add some turbulence
                float turbulence = sin(age * 10.0 + aInitialPos.x * 5.0) * 0.1 * normalizedAge;
                pos.x += turbulence;
                
                // Scale from explosion center
                vec2 offset = pos.xy - explosionCenter;
                pos.xy = explosionCenter + offset * (1.0 + normalizedAge * 2.0);
                
                gl_Position = vec4(pos.xy, 0.0, 1.0);
                
                // Calculate size with expansion and fade
                float sizeProgress = 1.0 + normalizedAge * 3.0; // Expand over time
                float sizeFade = 1.0 - smoothstep(0.7, 1.0, normalizedAge); // Fade out at end
                gl_PointSize = aSize * sizeMultiplier * sizeProgress * sizeFade * intensity;
                
                // Calculate color and alpha
                particleColor = aColor;
                
                // Bright at start, fade out over time
                float alphaFade = 1.0 - smoothstep(0.3, 1.0, normalizedAge);
                float intensityBoost = intensity * (1.0 + 2.0 * (1.0 - normalizedAge));
                
                particleAlpha = alphaFade * intensityBoost;
            }
            """
            
            fragment_shader_source = """
            #version 330 core
            in vec3 particleColor;
            in float particleAlpha;
            
            out vec4 FragColor;
            
            void main()
            {
                // Create circular particle with soft edges
                vec2 center = gl_PointCoord - vec2(0.5);
                float dist = length(center);
                
                // Soft circular falloff
                float alpha = 1.0 - smoothstep(0.0, 0.5, dist);
                alpha *= alpha; // Make edges softer
                
                // Add bright core
                float core = 1.0 - smoothstep(0.0, 0.2, dist);
                vec3 finalColor = particleColor * (1.0 + core * 2.0);
                
                FragColor = vec4(finalColor, alpha * particleAlpha);
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
            
            logging.debug("OneshotBoomExplosionVisualizer shaders compiled successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error loading shaders: {e}")
            return False

    def setup_particle_geometry(self):
        """Setup vertex data for particles"""
        try:
            # Create VAO and VBO (we'll update VBO data per explosion)
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)
            
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            
            # Reserve space for maximum particles across all explosions
            max_particles = self.max_explosions * self.particles_per_explosion
            vertex_size = 15 * 4  # 15 floats per vertex * 4 bytes
            glBufferData(GL_ARRAY_BUFFER, max_particles * vertex_size, None, GL_DYNAMIC_DRAW)
            
            # Set vertex attributes
            stride = 15 * 4  # 15 floats per vertex
            
            # Initial position (3 floats)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            
            # Velocity (3 floats)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))
            
            # Lifetime (1 float)
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * 4))
            
            # Birth time (1 float)
            glEnableVertexAttribArray(3)
            glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(7 * 4))
            
            # Color (3 floats)
            glEnableVertexAttribArray(4)
            glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8 * 4))
            
            # Size (1 float)
            glEnableVertexAttribArray(5)
            glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(11 * 4))
            
            # Unbind
            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            logging.debug("Particle geometry setup complete")
            return True
            
        except Exception as e:
            logging.error(f"Error setting up particle geometry: {e}")
            return False

    def create_explosion(self, center_x=None, center_y=None):
        """Create a new explosion at specified position (or random if None)"""
        current_time = time.time() - self.start_time
        
        # Remove old explosions
        self.explosions = [exp for exp in self.explosions 
                          if (current_time - exp['birth_time']) < exp['duration']]
        
        # Don't create new explosion if we're at max
        if len(self.explosions) >= self.max_explosions:
            self.explosions.pop(0)  # Remove oldest
        
        # Random position if not specified
        if center_x is None:
            center_x = random.uniform(-0.8, 0.8)
        if center_y is None:
            center_y = random.uniform(-0.8, 0.8)
        
        # Create explosion data
        explosion = {
            'center': (center_x, center_y),
            'birth_time': current_time,
            'duration': self.explosion_duration,
            'particles': []
        }
        
        # Generate particles for this explosion
        for i in range(self.particles_per_explosion):
            # Random direction and speed
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.5, 2.5)
            
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed
            velocity_z = random.uniform(-0.1, 0.1)
            
            # Particle properties
            lifetime = random.uniform(1.0, 3.0)
            size = random.uniform(8.0, 25.0)
            
            # Color based on mode
            if self.color_mode == 0:  # Fire
                r = random.uniform(0.8, 1.0)
                g = random.uniform(0.2, 0.8)
                b = random.uniform(0.0, 0.3)
            elif self.color_mode == 1:  # Electric
                r = random.uniform(0.5, 1.0)
                g = random.uniform(0.5, 1.0)
                b = 1.0
            else:  # Rainbow
                hue = random.uniform(0, 1)
                r = 0.5 + 0.5 * math.sin(hue * 6.28)
                g = 0.5 + 0.5 * math.sin(hue * 6.28 + 2.094)
                b = 0.5 + 0.5 * math.sin(hue * 6.28 + 4.189)
            
            particle = {
                'initial_pos': (center_x, center_y, 0.0),
                'velocity': (velocity_x, velocity_y, velocity_z),
                'lifetime': lifetime,
                'birth_time': current_time,
                'color': (r, g, b),
                'size': size
            }
            
            explosion['particles'].append(particle)
        
        self.explosions.append(explosion)
        logging.info(f"💥 Created explosion at ({center_x:.2f}, {center_y:.2f}) with {self.particles_per_explosion} particles")

    def update_particle_buffer(self):
        """Update the particle buffer with current explosion data"""
        try:
            vertices = []
            
            for explosion in self.explosions:
                for particle in explosion['particles']:
                    # Add particle data: pos(3) + vel(3) + lifetime(1) + birth(1) + color(3) + size(1) + padding(3)
                    vertices.extend([
                        # Initial position
                        particle['initial_pos'][0], particle['initial_pos'][1], particle['initial_pos'][2],
                        # Velocity
                        particle['velocity'][0], particle['velocity'][1], particle['velocity'][2],
                        # Lifetime
                        particle['lifetime'],
                        # Birth time
                        particle['birth_time'],
                        # Color
                        particle['color'][0], particle['color'][1], particle['color'][2],
                        # Size
                        particle['size'],
                        # Padding to reach 15 floats
                        0.0, 0.0, 0.0
                    ])
            
            if vertices:
                vertex_data = np.array(vertices, dtype=np.float32)
                
                glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
                glBufferSubData(GL_ARRAY_BUFFER, 0, vertex_data.nbytes, vertex_data)
                glBindBuffer(GL_ARRAY_BUFFER, 0)
                
                return len(vertices) // 15  # Number of particles
            
            return 0
            
        except Exception as e:
            logging.error(f"Error updating particle buffer: {e}")
            return 0

    def paintGL(self):
        """Render the explosions"""
        try:
            if not self.initialized or not self.shader_program or not self.vao:
                glClearColor(0.0, 0.0, 0.0, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return

            # Clear with transparent background
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)
            
            # Update particle data
            particle_count = self.update_particle_buffer()
            
            if particle_count > 0:
                current_time = time.time() - self.start_time
                
                # Use shader program
                glUseProgram(self.shader_program)
                
                # Set uniforms
                glUniform1f(glGetUniformLocation(self.shader_program, "time"), current_time)
                glUniform1f(glGetUniformLocation(self.shader_program, "intensity"), self.intensity)
                glUniform1f(glGetUniformLocation(self.shader_program, "sizeMultiplier"), self.size_multiplier)
                
                # Render each explosion
                particle_offset = 0
                for explosion in self.explosions:
                    explosion_particles = len(explosion['particles'])
                    
                    # Set explosion-specific uniforms
                    glUniform2f(glGetUniformLocation(self.shader_program, "explosionCenter"), 
                               explosion['center'][0], explosion['center'][1])
                    glUniform1f(glGetUniformLocation(self.shader_program, "explosionTime"),
                               explosion['birth_time'])
                    glUniform1f(glGetUniformLocation(self.shader_program, "explosionDuration"), 
                               explosion['duration'])
                    
                    # Draw particles for this explosion
                    glBindVertexArray(self.vao)
                    glDrawArrays(GL_POINTS, particle_offset, explosion_particles)
                    glBindVertexArray(0)
                    
                    particle_offset += explosion_particles
                
                glUseProgram(0)
            
        except Exception as e:
            if not hasattr(self, '_last_error_time') or time.time() - self._last_error_time > 5:
                logging.error(f"BoomExplosion paint error: {e}")
                self._last_error_time = time.time()
            
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        """Handle resize"""
        glViewport(0, 0, width, height)

    def cleanup(self):
        """Clean up OpenGL resources"""
        try:
            logging.debug("Cleaning up OneshotBoomExplosionVisualizer")
            
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
            self.explosions = []
            
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
            "Particle Count": {
                "type": "slider",
                "min": 50,
                "max": 500,
                "value": self.particles_per_explosion,
                "default": 200
            },
            "Duration": {
                "type": "slider",
                "min": 10,
                "max": 100,
                "value": int(self.explosion_duration * 10),
                "default": 30
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
            if name == "Intensity":
                self.intensity = value / 100.0
            elif name == "Size":
                self.size_multiplier = value / 100.0
            elif name == "Particle Count":
                self.particles_per_explosion = int(value)
            elif name == "Duration":
                self.explosion_duration = value / 10.0
            elif name == "Color Mode":
                self.color_mode = int(value)
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")

    def trigger_action(self, action_name):
        """Handle MIDI triggers"""
        if action_name == "boom" or action_name == "explosion":
            self.create_explosion()
            logging.info("💥 BOOM! Explosion triggered via MIDI")
