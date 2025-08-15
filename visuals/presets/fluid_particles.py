from OpenGL.GL import *
import numpy as np
import ctypes
import time
import math

from visuals.base_visualizer import BaseVisualizer

class FluidParticlesVisualizer(BaseVisualizer):
    visual_name = "Fluid Particles"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.num_particles = 1500  # Increased count for smaller particles
        self.particle_data = None
        self.time = 0.0
        self.flow_speed = 1.0
        self.particle_size = 0.8  # Smaller default size
        self.turbulence = 0.8
        self.gravity_strength = 0.5
        self.color_mode = 0
        self.brightness = 1.5
        
        # Particle physics properties
        self.particles = []
        self.attractors = []

    def get_controls(self):
        return {
            "Particle Count": {
                "type": "slider",
                "min": 500,
                "max": 3000,
                "value": self.num_particles,
            },
            "Flow Speed": {
                "type": "slider",
                "min": 10,
                "max": 500,
                "value": int(self.flow_speed * 100),
            },
            "Particle Size": {
                "type": "slider",
                "min": 5,  # Much smaller minimum
                "max": 200,  # Reduced maximum
                "value": int(self.particle_size * 100),
            },
            "Turbulence": {
                "type": "slider",
                "min": 0,
                "max": 300,
                "value": int(self.turbulence * 100),
            },
            "Gravity": {
                "type": "slider",
                "min": 0,
                "max": 200,
                "value": int(self.gravity_strength * 100),
            },
            "Brightness": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.brightness * 100),
            },
            "Color Mode": {
                "type": "dropdown",
                "options": ["Plasma Storm", "Aurora Dreams", "Deep Void", "Fire Galaxy", "Crystal Nebula", "Neon Pulse", "Rainbow Flow"],
                "value": self.color_mode,
            }
        }

    def update_control(self, name, value):
        if name == "Particle Count":
            old_count = self.num_particles
            self.num_particles = int(value)
            if old_count != self.num_particles:
                self.init_particles()
                self.setup_particle_buffers()
        elif name == "Flow Speed":
            self.flow_speed = float(value) / 100.0
        elif name == "Particle Size":
            self.particle_size = float(value) / 100.0
        elif name == "Turbulence":
            self.turbulence = float(value) / 100.0
        elif name == "Gravity":
            self.gravity_strength = float(value) / 100.0
        elif name == "Brightness":
            self.brightness = float(value) / 100.0
        elif name == "Color Mode":
            self.color_mode = int(value)

    def init_particles(self):
        self.particles = []
        for i in range(self.num_particles):
            angle = (i / self.num_particles) * 2 * np.pi
            radius = np.random.uniform(0.5, 3.0)
            particle = {
                'pos': np.array([
                    np.cos(angle) * radius + np.random.uniform(-0.5, 0.5),
                    np.sin(angle) * radius + np.random.uniform(-0.5, 0.5),
                    np.random.uniform(-1, 1)
                ]),
                'vel': np.array([
                    np.random.uniform(-0.02, 0.02),
                    np.random.uniform(-0.02, 0.02),
                    np.random.uniform(-0.01, 0.01)
                ]),
                'life': np.random.uniform(0.5, 1.0),
                'max_life': np.random.uniform(0.8, 1.0),
                'birth_time': np.random.uniform(0, 2 * np.pi),
                'phase': np.random.uniform(0, 2 * np.pi),
                'size_factor': np.random.uniform(0.2, 1.5),  # Smaller size range
                'color_offset': np.random.uniform(0, 2 * np.pi)
            }
            self.particles.append(particle)
        
        # Create dynamic attractors
        self.attractors = []
        for i in range(4):
            attractor = {
                'pos': np.array([
                    np.cos(i * 2 * np.pi / 4) * 1.5,
                    np.sin(i * 2 * np.pi / 4) * 1.5,
                    0
                ]),
                'strength': np.random.uniform(0.8, 2.0),
                'phase': i * 2 * np.pi / 4,
                'orbit_speed': np.random.uniform(0.3, 0.8)
            }
            self.attractors.append(attractor)

    def initializeGL(self):
        print("FluidParticlesVisualizer.initializeGL called")
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_PROGRAM_POINT_SIZE)
        glDisable(GL_DEPTH_TEST)  # Like working visualizers
        
        self.load_shaders()
        
        # Initialize particles
        self.init_particles()
        self.setup_particle_buffers()

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
                // Add some subtle movement
                vec3 pos = aPos;
                pos.x += sin(time * 2.0 + aPos.y * 0.5) * 0.05;
                pos.z += cos(time * 1.5 + aPos.x * 0.3) * 0.03;
                
                gl_Position = vec4(pos, 1.0);
                
                // Smaller, more refined point size
                gl_PointSize = max(1.0, aSize * particle_size * 8.0 * aLife);
                
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
                // Create soft circular particles
                vec2 coord = gl_PointCoord - vec2(0.5);
                float dist = length(coord);
                
                // Softer falloff for better visual appeal
                float alpha = 1.0 - smoothstep(0.2, 0.5, dist);
                
                // Add bright center for small particles
                float center = 1.0 - smoothstep(0.0, 0.15, dist);
                alpha = max(alpha * 0.7, center);
                
                // Fade based on life
                alpha *= vLife;
                
                FragColor = vec4(vColor.rgb, vColor.a * alpha);
            }
            """
            
            # Compile shaders
            vertex_shader = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex_shader, vertex_shader_source)
            glCompileShader(vertex_shader)
            
            fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment_shader, fragment_shader_source)
            glCompileShader(fragment_shader)

            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vertex_shader)
            glAttachShader(self.shader_program, fragment_shader)
            glLinkProgram(self.shader_program)

            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            print("FluidParticles shaders loaded successfully")
        except Exception as e:
            print(f"FluidParticles shader loading error: {e}")

    def setup_particle_buffers(self):
        try:
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])

            self.particle_data = np.zeros((self.num_particles, 8), dtype=np.float32)

            self.VAO = glGenVertexArrays(1)
            glBindVertexArray(self.VAO)

            self.VBO = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
            glBufferData(GL_ARRAY_BUFFER, self.particle_data.nbytes, self.particle_data, GL_DYNAMIC_DRAW)

            stride = 8 * ctypes.sizeof(GLfloat)
            
            # Position attribute
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            
            # Color attribute  
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
            glEnableVertexAttribArray(1)
            
            # Size attribute
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(7 * ctypes.sizeof(GLfloat)))
            glEnableVertexAttribArray(2)

            glBindVertexArray(0)
            print(f"FluidParticles particle buffers set up with {self.num_particles} particles")
        except Exception as e:
            print(f"Error setting up particle buffers: {e}")

    def update_physics(self):
        if not self.particles:
            return
            
        dt = 0.016 * self.flow_speed
        
        # Update attractors with more dynamic movement
        for i, attractor in enumerate(self.attractors):
            angle = self.time * attractor['orbit_speed'] + attractor['phase']
            radius = 2.0 + 1.0 * np.sin(self.time * 0.3 + i)
            attractor['pos'][0] = np.cos(angle) * radius
            attractor['pos'][1] = np.sin(angle * 1.2) * radius * 0.8
            attractor['pos'][2] = np.sin(self.time * 0.2 + i) * 0.8
            
            # Pulsating strength
            attractor['strength'] = 1.0 + 0.5 * np.sin(self.time * 2 + i)

        # Update particles with enhanced physics
        for particle in self.particles:
            # Multi-layered turbulence
            pos = particle['pos']
            turbulence_force = np.array([
                np.sin(pos[0] * 2 + self.time * 2) * np.cos(pos[1] * 1.3 + self.time),
                np.cos(pos[1] * 2 + self.time * 1.5) * np.sin(pos[0] * 1.7 + self.time * 0.8),
                np.sin(pos[2] * 4 + self.time * 3) * 0.3
            ]) * self.turbulence * dt * 0.5
            
            # Vortex effect
            dist_to_center = np.linalg.norm(pos[:2])
            if dist_to_center > 0.1:
                vortex_angle = np.arctan2(pos[1], pos[0]) + np.pi/2
                vortex_strength = 0.3 / (1 + dist_to_center)
                vortex_force = np.array([
                    np.cos(vortex_angle) * vortex_strength,
                    np.sin(vortex_angle) * vortex_strength,
                    0
                ]) * dt
                turbulence_force += vortex_force
            
            # Apply attractor forces
            for attractor in self.attractors:
                diff = attractor['pos'] - pos
                dist = np.linalg.norm(diff)
                if dist > 0.1:
                    force_magnitude = attractor['strength'] * self.gravity_strength / (1 + dist * dist)
                    force = diff / dist * force_magnitude * dt
                    particle['vel'] += force
            
            # Apply forces
            particle['vel'] += turbulence_force
            particle['vel'] *= 0.985  # Damping
            
            # Update position
            particle['pos'] += particle['vel'] * dt
            
            # Soft boundaries
            for i in range(3):
                if particle['pos'][i] > 6:
                    particle['pos'][i] = -6 + (particle['pos'][i] - 6) * 0.1
                elif particle['pos'][i] < -6:
                    particle['pos'][i] = 6 + (particle['pos'][i] + 6) * 0.1
            
            # Update life
            particle['life'] = particle['max_life'] * (0.7 + 0.3 * np.sin(self.time * 0.8 + particle['birth_time']))

    def get_particle_color(self, particle, velocity_mag, dist_to_center):
        """Enhanced colors for better visual appeal"""
        base_intensity = self.brightness
        time_factor = self.time + particle['color_offset']
        
        if self.color_mode == 0:  # Plasma Storm
            r = base_intensity * (0.9 + 0.1 * np.sin(time_factor * 3))
            g = base_intensity * (0.3 + 0.6 * velocity_mag * 20)
            b = base_intensity * (0.8 + 0.2 * np.sin(dist_to_center * 2 + time_factor))
        elif self.color_mode == 1:  # Aurora Dreams
            r = base_intensity * (0.3 + 0.4 * np.sin(particle['pos'][1] * 2 + time_factor))
            g = base_intensity * (0.7 + 0.3 * np.cos(particle['pos'][0] * 1.5 + time_factor * 0.7))
            b = base_intensity * (0.9 + 0.1 * np.sin(dist_to_center * 3 + time_factor * 0.5))
        elif self.color_mode == 2:  # Deep Void
            r = base_intensity * 0.15
            g = base_intensity * (0.4 + 0.5 * particle['life'])
            b = base_intensity * (0.9 + 0.1 * np.sin(time_factor + particle['phase']))
        elif self.color_mode == 3:  # Fire Galaxy
            r = base_intensity * (0.95 + 0.05 * np.sin(time_factor * 4))
            g = base_intensity * (0.3 + 0.6 * velocity_mag * 15 + 0.2 * particle['life'])
            b = base_intensity * (0.1 + 0.15 * particle['life'])
        elif self.color_mode == 4:  # Crystal Nebula
            intensity = 0.6 + 0.4 * np.sin(dist_to_center * 4 + time_factor * 2)
            r = base_intensity * 0.8 * intensity
            g = base_intensity * 0.9 * intensity
            b = base_intensity * intensity
        elif self.color_mode == 5:  # Neon Pulse
            pulse = 0.7 + 0.3 * np.sin(time_factor * 6)
            r = base_intensity * pulse * particle['life']
            g = base_intensity * 0.3
            b = base_intensity * pulse * (1 - particle['life'] * 0.5)
        else:  # Rainbow Flow
            hue = (time_factor + dist_to_center) % (2 * np.pi)
            r = base_intensity * (0.5 + 0.5 * np.sin(hue))
            g = base_intensity * (0.5 + 0.5 * np.sin(hue + 2*np.pi/3))
            b = base_intensity * (0.5 + 0.5 * np.sin(hue + 4*np.pi/3))
        
        return r, g, b

    def update_particle_data(self):
        if not self.particles or self.particle_data is None:
            return
            
        particles_to_process = min(len(self.particles), self.particle_data.shape[0])
        
        for i in range(particles_to_process):
            particle = self.particles[i]
            
            # Position
            self.particle_data[i, 0:3] = particle['pos']
            
            # Calculate derived values
            dist_to_center = np.linalg.norm(particle['pos'][:2])
            velocity_mag = np.linalg.norm(particle['vel'])
            
            # Get color
            r, g, b = self.get_particle_color(particle, velocity_mag, dist_to_center)
            
            # Enhanced alpha with more variation
            alpha = particle['life'] * 0.9 * (0.7 + 0.3 * np.sin(self.time * 4 + particle['phase']))
            self.particle_data[i, 3:7] = [r, g, b, alpha]
            
            # Size (smaller particles)
            self.particle_data[i, 7] = particle['size_factor']

        # Update buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.particle_data.nbytes, self.particle_data)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def paintGL(self):
        try:
            glClear(GL_COLOR_BUFFER_BIT)
            
            if not self.shader_program or not self.VAO:
                glClearColor(0.1, 0.0, 0.2, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return
            
            # Update time
            self.time += 0.016 * self.flow_speed
            
            # Update physics and data
            self.update_physics()
            self.update_particle_data()

            # Render particles
            if len(self.particles) > 0:
                glUseProgram(self.shader_program)
                
                # Send uniforms
                glUniform1f(glGetUniformLocation(self.shader_program, "particle_size"), self.particle_size)
                
                # Draw particles
                glBindVertexArray(self.VAO)
                glDrawArrays(GL_POINTS, 0, len(self.particles))
                glBindVertexArray(0)
                
                glUseProgram(0)
            
        except Exception as e:
            print(f"Error in paintGL: {e}")
            glClearColor(0.2, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def cleanup(self):
        print("Cleaning up FluidParticlesVisualizer")
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
        except Exception as e:
            print(f"Error during cleanup: {e}")