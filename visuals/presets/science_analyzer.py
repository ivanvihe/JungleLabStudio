from OpenGL.GL import *
import numpy as np
import ctypes
import time
import math

from visuals.base_visualizer import BaseVisualizer

# Try to import AudioAnalyzer
try:
    from visuals import AudioAnalyzer
except Exception:
    AudioAnalyzer = None

class ScientificAudioAnalyzerVisualizer(BaseVisualizer):
    visual_name = "Scientific Analyzer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # GL handles
        self.shader_program = None
        self.vao = None
        self.vbo = None
        
        # Analyzer & data
        self.analyzer = None
        self.sample_rate = 44100
        self.fft = np.zeros(513, dtype=np.float32)
        
        # Particle system - more aggressive spawning
        self.particles = []
        self.max_particles = 3000  # Increased
        self.spawn_rate = 150  # Much higher spawn rate
        self.particle_lifetime = 2.5  # Shorter lifetime for more turnover
        
        # UI params
        self.sensitivity = 2.0  # Higher sensitivity
        self.frequency_spread = 1.0
        self.amplitude_spread = 1.0
        self.particle_size = 1.5  # Slightly larger for visibility
        self.color_mode = 0
        self.spawn_intensity = 2.0  # Much higher intensity
        
        # Timing
        self.last_spawn_time = 0
        self.time = 0
        self.initialized = False

    def initializeGL(self):
        print("ScientificAudioAnalyzerVisualizer.initializeGL called")
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_PROGRAM_POINT_SIZE)
        glDisable(GL_DEPTH_TEST)  # Like working visualizers
        
        # Load shaders
        if not self.load_shaders():
            print("Failed to load shaders")
            return
        
        # Setup particle buffer
        self.setup_particle_buffer()
        
        # Initialize analyzer
        try:
            if AudioAnalyzer is not None:
                self.analyzer = AudioAnalyzer()
                self.analyzer.set_smoothing(fft_smooth=0.3, level_smooth=0.15)
                self.analyzer.start_analysis()
                self.sample_rate = self.analyzer.sample_rate
                print("AudioAnalyzer initialized successfully")
        except Exception as e:
            print(f"AudioAnalyzer init failed: {e}")
            self.analyzer = None
        
        self.initialized = True
        print("ScientificAnalyzer initialized successfully")

    def load_shaders(self):
        try:
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec3 aPos;
            layout (location = 1) in vec4 aColor;
            layout (location = 2) in float aSize;
            layout (location = 3) in float aLife;
            
            uniform float time;
            uniform float particle_size;
            
            out vec4 vColor;
            out float vLife;
            
            void main()
            {
                vec3 pos = aPos;
                
                // Add floating movement
                pos.x += sin(time * 1.5 + aPos.y * 0.3) * 0.05;
                pos.y += cos(time * 1.2 + aPos.x * 0.4) * 0.03;
                pos.z += sin(time * 2.0 + aPos.x * 0.2) * 0.02;
                
                gl_Position = vec4(pos, 1.0);
                
                // Size based on life and base size
                gl_PointSize = max(2.0, aSize * particle_size * 12.0 * (0.5 + 0.5 * aLife));
                
                vColor = aColor;
                vLife = aLife;
            }
            """
            
            fragment_shader_source = """
            #version 330 core
            in vec4 vColor;
            in float vLife;
            out vec4 FragColor;
            
            void main()
            {
                // Create circular particles with soft edges
                vec2 coord = gl_PointCoord - vec2(0.5);
                float dist = length(coord);
                float alpha = 1.0 - smoothstep(0.2, 0.5, dist);
                
                // Add bright center
                float center = 1.0 - smoothstep(0.0, 0.15, dist);
                alpha = max(alpha * 0.7, center);
                
                // Fade based on life
                alpha *= vLife;
                
                FragColor = vec4(vColor.rgb, vColor.a * alpha);
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
            
            print("ScientificAnalyzer shaders compiled successfully")
            return True
            
        except Exception as e:
            print(f"Error loading shaders: {e}")
            return False

    def setup_particle_buffer(self):
        try:
            # Each particle: pos(3) + color(4) + size(1) + life(1) = 9 floats
            self.particle_data = np.zeros((self.max_particles, 9), dtype=np.float32)
            
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)
            
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, self.particle_data.nbytes, self.particle_data, GL_DYNAMIC_DRAW)
            
            stride = 9 * ctypes.sizeof(GLfloat)
            
            # Position attribute (location 0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            
            # Color attribute (location 1)
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
            glEnableVertexAttribArray(1)
            
            # Size attribute (location 2)
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(7 * ctypes.sizeof(GLfloat)))
            glEnableVertexAttribArray(2)
            
            # Life attribute (location 3)
            glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8 * ctypes.sizeof(GLfloat)))
            glEnableVertexAttribArray(3)
            
            glBindVertexArray(0)
            
            print("ScientificAnalyzer particle buffer setup complete")
            
        except Exception as e:
            print(f"Error setting up particle buffer: {e}")

    def spawn_particles_from_fft(self, fft_data, dt):
        """Spawn particles based on FFT data - much more aggressive"""
        if len(fft_data) == 0:
            return
        
        # Determine how many particles to spawn this frame - much higher rate
        base_particles = int(self.spawn_rate * self.spawn_intensity * dt)
        
        # Add extra particles based on audio energy
        audio_energy = np.sum(fft_data) / len(fft_data)
        energy_particles = int(audio_energy * self.sensitivity * 2.0)  # Double sensitivity
        
        particles_to_spawn = base_particles + energy_particles
        
        # Always spawn at least some particles for demo mode
        if self.analyzer is None:
            particles_to_spawn = max(particles_to_spawn, 5)  # Minimum spawn
        
        # Find the strongest frequencies for better distribution
        fft_normalized = np.clip(fft_data / 100.0, 0.0, 1.0)
        
        for _ in range(particles_to_spawn):
            if len(self.particles) >= self.max_particles:
                # Remove oldest particle to make room
                self.particles.pop(0)
            
            # Pick frequency bin - favor stronger frequencies but allow random ones too
            if np.sum(fft_normalized) > 0.01 and np.random.random() < 0.7:
                # Weighted selection based on amplitude
                weights = fft_normalized + 0.1
                freq_bin = np.random.choice(len(weights), p=weights/np.sum(weights))
            else:
                # Random frequency
                freq_bin = np.random.randint(0, len(fft_normalized))
            
            amplitude = fft_normalized[freq_bin] if freq_bin < len(fft_normalized) else 0.5
            
            # Position based on frequency and amplitude - more spread
            freq_norm = freq_bin / len(fft_data)
            y_pos = (freq_norm - 0.5) * 3.0 * self.frequency_spread  # More spread
            
            # X: amplitude with more variation
            x_pos = (amplitude - 0.5) * 2.0 * self.amplitude_spread
            
            # Z: random depth
            z_pos = np.random.uniform(-0.5, 0.5)
            
            # Add randomness for clustering around center
            x_pos += np.random.normal(0, 0.3)
            y_pos += np.random.normal(0, 0.2)
            z_pos += np.random.normal(0, 0.2)
            
            # Color based on frequency and amplitude
            color = self.get_particle_color(freq_norm, amplitude)
            
            # Size based on amplitude with more variation
            size = (0.3 + amplitude * 1.5) * self.particle_size
            
            # Create particle
            particle = {
                'position': np.array([x_pos, y_pos, z_pos]),
                'color': color,
                'size': size,
                'life': 1.0,
                'max_life': self.particle_lifetime + np.random.uniform(-0.5, 0.5),
                'age': 0.0,
                'frequency': freq_norm,
                'amplitude': amplitude,
                'velocity': np.array([
                    np.random.uniform(-0.1, 0.1),
                    np.random.uniform(-0.1, 0.1),
                    np.random.uniform(-0.05, 0.05)
                ])
            }
            
            self.particles.append(particle)

    def get_particle_color(self, freq_norm, amplitude):
        """Get particle color based on frequency and amplitude"""
        base_intensity = 0.8 + amplitude * 0.5  # Brighter colors
        
        if self.color_mode == 0:  # Frequency spectrum
            if freq_norm < 0.33:  # Low frequencies - red/orange
                r = base_intensity * (0.9 + amplitude * 0.1)
                g = base_intensity * (0.3 + amplitude * 0.4)
                b = base_intensity * (0.1 + amplitude * 0.2)
            elif freq_norm < 0.66:  # Mid frequencies - green/yellow
                r = base_intensity * (0.4 + amplitude * 0.4)
                g = base_intensity * (0.9 + amplitude * 0.1)
                b = base_intensity * (0.2 + amplitude * 0.3)
            else:  # High frequencies - blue/purple
                r = base_intensity * (0.3 + amplitude * 0.3)
                g = base_intensity * (0.2 + amplitude * 0.3)
                b = base_intensity * (0.9 + amplitude * 0.1)
                
        elif self.color_mode == 1:  # Heat map
            r = base_intensity * amplitude
            g = base_intensity * amplitude * 0.7
            b = base_intensity * (1.0 - amplitude * 0.6)
            
        elif self.color_mode == 2:  # Plasma
            phase = freq_norm * 2 * np.pi + self.time
            r = base_intensity * (0.5 + 0.5 * np.sin(phase))
            g = base_intensity * (0.5 + 0.5 * np.sin(phase + 2*np.pi/3))
            b = base_intensity * (0.5 + 0.5 * np.sin(phase + 4*np.pi/3))
            
        else:  # White/Electric
            intensity = base_intensity * (0.7 + amplitude * 0.3)
            r = g = b = intensity
        
        return np.array([r, g, b, 0.9])  # Higher alpha

    def update_particles(self, dt):
        """Update all particles"""
        particles_to_remove = []
        
        for i, particle in enumerate(self.particles):
            particle['age'] += dt
            particle['life'] = 1.0 - (particle['age'] / particle['max_life'])
            
            # Mark for removal if dead
            if particle['life'] <= 0:
                particles_to_remove.append(i)
            else:
                # Update position with velocity
                particle['position'] += particle['velocity'] * dt
                
                # Add floating motion
                particle['position'][0] += np.sin(self.time * 2 + particle['position'][1]) * dt * 0.05
                particle['position'][1] += np.cos(self.time * 1.5 + particle['position'][0]) * dt * 0.03
        
        # Remove dead particles
        for i in reversed(particles_to_remove):
            del self.particles[i]

    def update_particle_buffer(self):
        """Update the OpenGL buffer with current particle data"""
        if not self.particles:
            return
        
        try:
            # Clear the buffer
            self.particle_data.fill(0)
            
            # Fill with current particles
            for i, particle in enumerate(self.particles[:self.max_particles]):
                # Position
                self.particle_data[i, 0:3] = particle['position']
                
                # Color
                self.particle_data[i, 3:7] = particle['color']
                
                # Size
                self.particle_data[i, 7] = particle['size']
                
                # Life
                self.particle_data[i, 8] = particle['life']
            
            # Upload to GPU
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.particle_data.nbytes, self.particle_data)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
        except Exception as e:
            print(f"Error updating particle buffer: {e}")

    def paintGL(self):
        try:
            glClear(GL_COLOR_BUFFER_BIT)
            
            if not self.initialized or not self.shader_program or not self.vao:
                glClearColor(0.1, 0.0, 0.2, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return
            
            # Update time
            dt = 0.016  # Assume 60fps
            self.time += dt
            
            # Get audio data
            if self.analyzer and self.analyzer.is_active():
                self.fft = self.analyzer.get_fft_data().astype(np.float32)
            else:
                # Enhanced demo mode with more activity
                freq_count = 513
                demo_fft = np.zeros(freq_count, dtype=np.float32)
                
                # Multiple frequency bands with different patterns
                for band in range(8):
                    center_freq = 50 + band * 60
                    if center_freq < freq_count:
                        # Different wave patterns for each band
                        strength = 30 + 40 * np.sin(self.time * (1.5 + band * 0.3) + band)
                        strength = max(0, strength)
                        
                        # Add the peak
                        demo_fft[center_freq] = strength
                        
                        # Add harmonics and spread
                        for offset in range(-10, 11):
                            idx = center_freq + offset
                            if 0 <= idx < freq_count:
                                falloff = max(0, 1.0 - abs(offset) / 10.0)
                                demo_fft[idx] += strength * falloff * 0.7
                
                self.fft = demo_fft
            
            # Spawn new particles - much more aggressive
            self.spawn_particles_from_fft(self.fft, dt)
            
            # Update particles
            self.update_particles(dt)
            
            # Update GPU buffer
            self.update_particle_buffer()
            
            # Render particles
            if len(self.particles) > 0:
                glUseProgram(self.shader_program)
                
                # Send uniforms
                glUniform1f(glGetUniformLocation(self.shader_program, "time"), self.time)
                glUniform1f(glGetUniformLocation(self.shader_program, "particle_size"), self.particle_size)
                
                # Draw particles
                glBindVertexArray(self.vao)
                glDrawArrays(GL_POINTS, 0, min(len(self.particles), self.max_particles))
                glBindVertexArray(0)
                
                glUseProgram(0)
            
        except Exception as e:
            print(f"Error in paintGL: {e}")
            glClearColor(0.2, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def get_controls(self):
        return {
            "Sensitivity": {"type": "slider", "min": 10, "max": 500, "value": int(self.sensitivity * 100)},
            "Spawn Rate": {"type": "slider", "min": 50, "max": 500, "value": int(self.spawn_intensity * 100)},
            "Particle Size": {"type": "slider", "min": 20, "max": 300, "value": int(self.particle_size * 100)},
            "Frequency Spread": {"type": "slider", "min": 20, "max": 300, "value": int(self.frequency_spread * 100)},
            "Amplitude Spread": {"type": "slider", "min": 20, "max": 300, "value": int(self.amplitude_spread * 100)},
            "Color Mode": {"type": "dropdown", "options": ["Spectrum", "Heat", "Plasma", "Electric"], "value": self.color_mode},
        }

    def update_control(self, name, value):
        if name == "Sensitivity":
            self.sensitivity = float(value) / 100.0
        elif name == "Spawn Rate":
            self.spawn_intensity = float(value) / 100.0
        elif name == "Particle Size":
            self.particle_size = float(value) / 100.0
        elif name == "Frequency Spread":
            self.frequency_spread = float(value) / 100.0
        elif name == "Amplitude Spread":
            self.amplitude_spread = float(value) / 100.0
        elif name == "Color Mode":
            self.color_mode = int(value)

    def cleanup(self):
        try:
            if self.analyzer:
                self.analyzer.cleanup()
        except Exception:
            pass
        try:
            if self.shader_program:
                if glIsProgram(self.shader_program):
                    glDeleteProgram(self.shader_program)
                self.shader_program = None
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
                self.vao = None
        except Exception as e:
            print(f"Cleanup error: {e}")