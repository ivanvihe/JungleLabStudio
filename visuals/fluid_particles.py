from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import ctypes
import os
import logging
import math

from .base_visualizer import BaseVisualizer

class FluidParticlesVisualizer(BaseVisualizer):
    visual_name = "Fluid Particles"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.background_shader = None
        self.VBO = None
        self.VAO = None
        self.bg_VBO = None
        self.bg_VAO = None
        self.num_particles = 800
        self.particle_data = None
        self.background_data = None
        self.time = 0.0
        self.flow_speed = 1.0
        self.particle_size = 3.0
        self.turbulence = 0.8
        self.gravity_strength = 0.5
        self.color_mode = 0
        self.blend_mode = 0
        self.brightness = 1.0
        self.background_intensity = 0.3
        
        # Particle physics properties
        self.particles = []
        self.attractors = []
        self.background_elements = []
        self.init_particles()
        self.init_background()

    def get_controls(self):
        return {
            "Particle Count": {
                "type": "slider",
                "min": 200,
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
                "min": 10,
                "max": 1000,
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
            "Background": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.background_intensity * 100),
            },
            "Color Mode": {
                "type": "dropdown",
                "options": ["Plasma Storm", "Aurora Dreams", "Deep Void", "Fire Galaxy", "Crystal Nebula", "Neon Pulse", "Rainbow Flow"],
                "value": self.color_mode,
            },
            "Blend Mode": {
                "type": "dropdown",
                "options": ["Additive Glow", "Alpha Blend", "Screen Light", "Color Burn"],
                "value": self.blend_mode,
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
        elif name == "Background":
            self.background_intensity = float(value) / 100.0
        elif name == "Color Mode":
            self.color_mode = int(value)
        elif name == "Blend Mode":
            self.blend_mode = int(value)
            self.set_blend_mode()

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
                'life': np.random.uniform(0.3, 1.0),
                'max_life': np.random.uniform(0.8, 1.0),
                'birth_time': np.random.uniform(0, 2 * np.pi),
                'phase': np.random.uniform(0, 2 * np.pi),
                'size_factor': np.random.uniform(0.3, 2.0),
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

    def init_background(self):
        # Create background cloud/nebula elements
        self.background_elements = []
        num_bg = 200
        for i in range(num_bg):
            element = {
                'pos': np.array([
                    np.random.uniform(-8, 8),
                    np.random.uniform(-8, 8),
                    np.random.uniform(-5, -1)
                ]),
                'size': np.random.uniform(0.5, 3.0),
                'alpha': np.random.uniform(0.1, 0.4),
                'phase': np.random.uniform(0, 2 * np.pi),
                'drift_speed': np.random.uniform(0.001, 0.01)
            }
            self.background_elements.append(element)

    def initializeGL(self):
        print("FluidParticlesVisualizer.initializeGL called")
        glClearColor(0.0, 0.0, 0.05, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glEnable(GL_PROGRAM_POINT_SIZE)
        glDepthMask(GL_FALSE)  # Disable depth writing for better blending
        self.set_blend_mode()

        self.load_shaders()
        self.setup_particle_buffers()
        self.setup_background_buffers()

    def set_blend_mode(self):
        if self.blend_mode == 0:  # Additive Glow
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        elif self.blend_mode == 1:  # Alpha Blend
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        elif self.blend_mode == 2:  # Screen Light
            glBlendFunc(GL_ONE_MINUS_DST_COLOR, GL_ONE)
        else:  # Color Burn
            glBlendFunc(GL_DST_COLOR, GL_ONE_MINUS_SRC_ALPHA)

    def load_shaders(self):
        # Use basic shaders
        script_dir = os.path.dirname(__file__)
        shader_dir = os.path.join(script_dir, '..', 'shaders')

        try:
            with open(os.path.join(shader_dir, 'basic.vert'), 'r') as f:
                vertex_shader_source = f.read()
            with open(os.path.join(shader_dir, 'basic.frag'), 'r') as f:
                fragment_shader_source = f.read()

            # Main particle shader
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

            # Background shader (same shaders, different usage)
            self.background_shader = self.shader_program

            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            print("FluidParticles shaders loaded successfully")
        except Exception as e:
            print(f"FluidParticles shader loading error: {e}")

    def setup_particle_buffers(self):
        if self.VAO:
            glDeleteVertexArrays(1, [self.VAO])
        if self.VBO:
            glDeleteBuffers(1, [self.VBO])

        self.particle_data = np.zeros((self.num_particles, 7), dtype=np.float32)

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.particle_data.nbytes, self.particle_data, GL_DYNAMIC_DRAW)

        # Position attribute
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Color attribute  
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)

    def setup_background_buffers(self):
        if self.bg_VAO:
            glDeleteVertexArrays(1, [self.bg_VAO])
        if self.bg_VBO:
            glDeleteBuffers(1, [self.bg_VBO])

        num_bg = len(self.background_elements)
        self.background_data = np.zeros((num_bg, 7), dtype=np.float32)

        self.bg_VAO = glGenVertexArrays(1)
        glBindVertexArray(self.bg_VAO)

        self.bg_VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.bg_VBO)
        glBufferData(GL_ARRAY_BUFFER, self.background_data.nbytes, self.background_data, GL_DYNAMIC_DRAW)

        # Same attributes as particles
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)

    def update_physics(self):
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

        # Update particles with more complex physics
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
            
            # Apply attractor forces with falloff
            for attractor in self.attractors:
                diff = attractor['pos'] - pos
                dist = np.linalg.norm(diff)
                if dist > 0.1:
                    # Smooth falloff
                    force_magnitude = attractor['strength'] * self.gravity_strength / (1 + dist * dist)
                    force = diff / dist * force_magnitude * dt
                    particle['vel'] += force
            
            # Apply forces
            particle['vel'] += turbulence_force
            particle['vel'] *= 0.985  # Damping
            
            # Update position
            particle['pos'] += particle['vel'] * dt
            
            # Soft boundaries with wrapping
            for i in range(3):
                if particle['pos'][i] > 6:
                    particle['pos'][i] = -6 + (particle['pos'][i] - 6) * 0.1
                elif particle['pos'][i] < -6:
                    particle['pos'][i] = 6 + (particle['pos'][i] + 6) * 0.1
            
            # Update life with breathing effect
            particle['life'] = particle['max_life'] * (0.5 + 0.5 * np.sin(self.time * 0.8 + particle['birth_time']))

    def get_particle_color(self, particle, velocity_mag, dist_to_center):
        # More vibrant and responsive colors
        base_intensity = self.brightness
        time_factor = self.time + particle['color_offset']
        
        if self.color_mode == 0:  # Plasma Storm
            r = base_intensity * (0.9 + 0.1 * np.sin(time_factor * 3))
            g = base_intensity * (0.1 + 0.6 * velocity_mag * 20)
            b = base_intensity * (0.8 + 0.2 * np.sin(dist_to_center * 2 + time_factor))
        elif self.color_mode == 1:  # Aurora Dreams
            r = base_intensity * (0.1 + 0.4 * np.sin(particle['pos'][1] * 2 + time_factor))
            g = base_intensity * (0.7 + 0.3 * np.cos(particle['pos'][0] * 1.5 + time_factor * 0.7))
            b = base_intensity * (0.9 + 0.1 * np.sin(dist_to_center * 3 + time_factor * 0.5))
        elif self.color_mode == 2:  # Deep Void
            r = base_intensity * 0.05
            g = base_intensity * (0.2 + 0.5 * particle['life'])
            b = base_intensity * (0.9 + 0.1 * np.sin(time_factor + particle['phase']))
        elif self.color_mode == 3:  # Fire Galaxy
            r = base_intensity * (0.95 + 0.05 * np.sin(time_factor * 4))
            g = base_intensity * (0.1 + 0.6 * velocity_mag * 15 + 0.2 * particle['life'])
            b = base_intensity * (0.05 + 0.15 * particle['life'])
        elif self.color_mode == 4:  # Crystal Nebula
            intensity = 0.6 + 0.4 * np.sin(dist_to_center * 4 + time_factor * 2)
            r = base_intensity * 0.8 * intensity
            g = base_intensity * 0.9 * intensity
            b = base_intensity * intensity
        elif self.color_mode == 5:  # Neon Pulse
            pulse = 0.7 + 0.3 * np.sin(time_factor * 6)
            r = base_intensity * pulse * particle['life']
            g = base_intensity * 0.1
            b = base_intensity * pulse * (1 - particle['life'] * 0.5)
        else:  # Rainbow Flow
            hue = (time_factor + dist_to_center) % (2 * np.pi)
            r = base_intensity * (0.5 + 0.5 * np.sin(hue))
            g = base_intensity * (0.5 + 0.5 * np.sin(hue + 2*np.pi/3))
            b = base_intensity * (0.5 + 0.5 * np.sin(hue + 4*np.pi/3))
        
        return r, g, b

    def update_particle_data(self):
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
            alpha = particle['life'] * 0.9 * (0.8 + 0.2 * np.sin(self.time * 4 + particle['phase']))
            self.particle_data[i, 3:7] = [r, g, b, alpha]

        # Update buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.particle_data.nbytes, self.particle_data)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def update_background_data(self):
        if not self.background_elements:
            return
            
        for i, element in enumerate(self.background_elements):
            # Slow drift
            element['pos'][0] += element['drift_speed'] * np.cos(self.time * 0.1 + element['phase'])
            element['pos'][1] += element['drift_speed'] * np.sin(self.time * 0.15 + element['phase'])
            
            # Wrap around
            for j in range(2):
                if element['pos'][j] > 8:
                    element['pos'][j] = -8
                elif element['pos'][j] < -8:
                    element['pos'][j] = 8
            
            # Position
            self.background_data[i, 0:3] = element['pos']
            
            # Subtle color based on main color mode
            if self.color_mode == 0:  # Plasma
                r, g, b = 0.3, 0.1, 0.4
            elif self.color_mode == 1:  # Aurora  
                r, g, b = 0.1, 0.3, 0.4
            elif self.color_mode == 2:  # Deep Void
                r, g, b = 0.0, 0.1, 0.3
            elif self.color_mode == 3:  # Fire
                r, g, b = 0.4, 0.2, 0.0
            elif self.color_mode == 4:  # Crystal
                r, g, b = 0.2, 0.2, 0.3
            elif self.color_mode == 5:  # Neon
                r, g, b = 0.3, 0.0, 0.3
            else:  # Rainbow
                r, g, b = 0.2, 0.2, 0.2
            
            alpha = element['alpha'] * self.background_intensity * (0.8 + 0.2 * np.sin(self.time * 0.5 + element['phase']))
            self.background_data[i, 3:7] = [r, g, b, alpha]

        # Update buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.bg_VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.background_data.nbytes, self.background_data)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if not self.shader_program:
            return
        
        self.time += 0.016 * self.flow_speed
        
        # Update physics and data
        self.update_physics()
        self.update_background_data()
        self.update_particle_data()

        # Set matrices
        projection = self.perspective(50, 1.0, 0.1, 100.0)
        
        # More dynamic camera movement
        cam_radius = 8 + 2 * np.sin(self.time * 0.08)
        cam_height = 3 + 2 * np.sin(self.time * 0.12)
        cam_x = np.cos(self.time * 0.05) * cam_radius
        cam_y = cam_height
        cam_z = np.sin(self.time * 0.05) * cam_radius
        
        view = self.lookAt(
            np.array([cam_x, cam_y, cam_z]), 
            np.array([0, 0, 0]), 
            np.array([0, 1, 0])
        )
        
        model = np.identity(4, dtype=np.float32)

        glUseProgram(self.shader_program)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)

        # Set point size for particles
        glPointSize(self.particle_size * 5)

        # Draw background first
        if self.background_intensity > 0.01:
            glBindVertexArray(self.bg_VAO)
            glDrawArrays(GL_POINTS, 0, len(self.background_elements))
            glBindVertexArray(0)

        # Draw particles
        particles_to_draw = min(len(self.particles), self.particle_data.shape[0])
        glBindVertexArray(self.VAO)
        glDrawArrays(GL_POINTS, 0, particles_to_draw)
        glBindVertexArray(0)

    def perspective(self, fov, aspect, near, far):
        f = 1.0 / np.tan(np.radians(fov / 2.0))
        return np.array([
            [f / aspect, 0.0, 0.0, 0.0],
            [0.0, f, 0.0, 0.0],
            [0.0, 0.0, (far + near) / (near - far), -1.0],
            [0.0, 0.0, (2.0 * far * near) / (near - far), 0.0]
        ], dtype=np.float32)

    def lookAt(self, eye, center, up):
        f = (center - eye) / np.linalg.norm(center - eye)
        s = np.cross(f, up) / np.linalg.norm(np.cross(f, up))
        u = np.cross(s, f)

        return np.array([
            [s[0], u[0], -f[0], 0.0],
            [s[1], u[1], -f[1], 0.0],
            [s[2], u[2], -f[2], 0.0],
            [-np.dot(s, eye), -np.dot(u, eye), np.dot(f, eye), 1.0]
        ], dtype=np.float32).T

    def cleanup(self):
        print("Cleaning up FluidParticlesVisualizer")
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
            if self.bg_VBO:
                glDeleteBuffers(1, [self.bg_VBO])
                self.bg_VBO = None
            if self.bg_VAO:
                glDeleteVertexArrays(1, [self.bg_VAO])
                self.bg_VAO = None
        except Exception as e:
            print(f"Error during cleanup: {e}")