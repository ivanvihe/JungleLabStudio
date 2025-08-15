from OpenGL.GL import *
import numpy as np
import ctypes
import time
import random

from visuals.base_visualizer import BaseVisualizer

class EvolutiveParticlesVisualizer(BaseVisualizer):
    visual_name = "Evolutive Particles"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.num_particles = 800
        self.particle_data = None
        self.time = 0.0
        self.evolution_speed = 1.0
        self.mutation_rate = 0.5
        self.complexity = 1.0
        self.energy_level = 1.0
        
        # Evolution system
        self.particles = []
        self.generations = 0
        self.evolution_timer = 0
        self.evolution_interval = 3.0  # Evolve every 3 seconds
        
        self.initialized = False

    def get_controls(self):
        return {
            "Evolution Speed": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.evolution_speed * 100),
            },
            "Mutation Rate": {
                "type": "slider",
                "min": 10,
                "max": 200,
                "value": int(self.mutation_rate * 100),
            },
            "Complexity": {
                "type": "slider",
                "min": 20,
                "max": 300,
                "value": int(self.complexity * 100),
            },
            "Energy Level": {
                "type": "slider",
                "min": 20,
                "max": 300,
                "value": int(self.energy_level * 100),
            },
            "Particle Count": {
                "type": "slider",
                "min": 200,
                "max": 2000,
                "value": self.num_particles,
            }
        }

    def update_control(self, name, value):
        if name == "Evolution Speed":
            self.evolution_speed = float(value) / 100.0
        elif name == "Mutation Rate":
            self.mutation_rate = float(value) / 100.0
        elif name == "Complexity":
            self.complexity = float(value) / 100.0
        elif name == "Energy Level":
            self.energy_level = float(value) / 100.0
        elif name == "Particle Count":
            old_count = self.num_particles
            self.num_particles = int(value)
            if old_count != self.num_particles:
                self.evolve_new_generation()

    def initializeGL(self):
        print("EvolutiveParticlesVisualizer.initializeGL called")
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_PROGRAM_POINT_SIZE)
        glDisable(GL_DEPTH_TEST)

        self.load_shaders()
        self.evolve_new_generation()  # Start with first generation
        self.setup_particles()
        self.initialized = True
        print("EvolutiveParticles initialized successfully")

    def load_shaders(self):
        try:
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec3 aPos;
            layout (location = 1) in vec4 aColor;
            layout (location = 2) in float aSize;
            layout (location = 3) in vec3 aVelocity;
            
            uniform float time;
            uniform float evolution_speed;
            uniform float energy_level;
            
            out vec4 vertexColor;
            
            void main()
            {
                vec3 pos = aPos;
                
                // Apply evolutionary movement patterns
                pos += aVelocity * time * evolution_speed;
                
                // Add energy-based oscillations
                pos.x += sin(time * 2.0 + aPos.y * 3.0) * energy_level * 0.1;
                pos.y += cos(time * 1.5 + aPos.x * 2.5) * energy_level * 0.1;
                pos.z += sin(time * 3.0 + aPos.x + aPos.y) * energy_level * 0.05;
                
                // Wrap around screen boundaries
                pos.x = mod(pos.x + 2.0, 4.0) - 2.0;
                pos.y = mod(pos.y + 2.0, 4.0) - 2.0;
                
                gl_Position = vec4(pos, 1.0);
                gl_PointSize = aSize * (1.0 + sin(time * 3.0 + aPos.x) * 0.5);
                
                // Color evolution based on time
                vec4 color = aColor;
                color.rgb *= (0.8 + 0.2 * sin(time + aPos.x + aPos.y));
                vertexColor = color;
            }
            """
            
            fragment_shader_source = """
            #version 330 core
            in vec4 vertexColor;
            out vec4 FragColor;
            
            void main()
            {
                // Create organic, evolving particle shapes
                vec2 coord = gl_PointCoord - vec2(0.5);
                float dist = length(coord);
                
                // Multiple layers for complex shapes
                float alpha1 = 1.0 - smoothstep(0.1, 0.5, dist);
                float alpha2 = 1.0 - smoothstep(0.0, 0.3, dist);
                float alpha3 = 1.0 - smoothstep(0.2, 0.4, dist);
                
                float alpha = max(alpha1 * 0.6, max(alpha2, alpha3 * 0.4));
                
                FragColor = vec4(vertexColor.rgb, vertexColor.a * alpha);
            }
            """

            # Compile vertex shader
            vertex_shader = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex_shader, vertex_shader_source)
            glCompileShader(vertex_shader)
            if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
                print("Vertex Shader Compile Error:", glGetShaderInfoLog(vertex_shader).decode())

            # Compile fragment shader
            fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment_shader, fragment_shader_source)
            glCompileShader(fragment_shader)
            if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
                print("Fragment Shader Compile Error:", glGetShaderInfoLog(fragment_shader).decode())

            self.shader_program = glCreateProgram()
            glAttachShader(self.shader_program, vertex_shader)
            glAttachShader(self.shader_program, fragment_shader)
            glLinkProgram(self.shader_program)
            if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
                print("Shader Program Link Error:", glGetProgramInfoLog(self.shader_program).decode())

            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            print("EvolutiveParticles shaders loaded successfully")
        except Exception as e:
            print(f"EvolutiveParticles shader loading error: {e}")

    def evolve_new_generation(self):
        """Create a new generation of particles with evolutionary traits"""
        print(f"Evolving generation {self.generations}...")
        
        # If we have existing particles, evolve from the "fittest"
        if self.particles and len(self.particles) > 10:
            # Select the "fittest" particles (those that survived longest or have certain traits)
            fitness_scores = []
            for particle in self.particles:
                # Fitness based on position stability, color intensity, and survival time
                stability = 1.0 / (1.0 + np.linalg.norm(particle['velocity']))
                color_intensity = np.sum(particle['color'][:3])
                age_factor = particle.get('age', 1.0)
                fitness = stability * color_intensity * age_factor
                fitness_scores.append(fitness)
            
            # Select top performers for breeding
            sorted_indices = np.argsort(fitness_scores)
            elite_count = min(20, len(self.particles) // 4)
            elite_particles = [self.particles[i] for i in sorted_indices[-elite_count:]]
        else:
            elite_particles = []
        
        # Create new generation
        new_particles = []
        
        for i in range(self.num_particles):
            if elite_particles and random.random() < 0.3:  # 30% inherit from elite
                # Breed from elite particles
                parent1 = random.choice(elite_particles)
                parent2 = random.choice(elite_particles)
                particle = self.breed_particles(parent1, parent2)
            else:
                # Create random new particle
                particle = self.create_random_particle()
            
            # Apply mutations
            if random.random() < self.mutation_rate:
                particle = self.mutate_particle(particle)
            
            # Add evolutionary traits
            particle['generation'] = self.generations
            particle['age'] = 0.0
            particle['fitness'] = 0.0
            particle['behavior_type'] = random.choice(['wanderer', 'orbiter', 'spiral', 'chaotic', 'flocking'])
            
            new_particles.append(particle)
        
        self.particles = new_particles
        self.generations += 1

    def breed_particles(self, parent1, parent2):
        """Breed two particles to create offspring"""
        # Blend positions
        pos = (parent1['position'] + parent2['position']) / 2.0
        pos += np.random.normal(0, 0.1, 3)  # Add some noise
        
        # Blend velocities
        vel = (parent1['velocity'] + parent2['velocity']) / 2.0
        vel += np.random.normal(0, 0.02, 3)
        
        # Blend colors
        color = (parent1['color'] + parent2['color']) / 2.0
        color += np.random.normal(0, 0.1, 4)
        color = np.clip(color, 0, 1)
        
        # Blend size
        size = (parent1['size'] + parent2['size']) / 2.0
        size += random.uniform(-0.2, 0.2)
        size = max(0.5, min(3.0, size))
        
        return {
            'position': pos,
            'velocity': vel,
            'color': color,
            'size': size,
            'energy': random.uniform(0.5, 1.5)
        }

    def create_random_particle(self):
        """Create a completely random particle"""
        # Random behaviors based on complexity
        if self.complexity > 1.5:
            # High complexity - more exotic behaviors
            pos = np.random.uniform(-2, 2, 3)
            vel = np.random.uniform(-0.1, 0.1, 3) * self.complexity
        else:
            # Lower complexity - simpler behaviors
            pos = np.random.uniform(-1.5, 1.5, 3)
            vel = np.random.uniform(-0.05, 0.05, 3)
        
        # Evolving color palettes
        color_mode = random.choice(['warm', 'cool', 'rainbow', 'monochrome', 'electric'])
        if color_mode == 'warm':
            color = np.array([random.uniform(0.6, 1.0), random.uniform(0.2, 0.8), random.uniform(0.1, 0.4), 0.8])
        elif color_mode == 'cool':
            color = np.array([random.uniform(0.1, 0.4), random.uniform(0.4, 0.9), random.uniform(0.6, 1.0), 0.8])
        elif color_mode == 'rainbow':
            hue = random.uniform(0, 2 * np.pi)
            color = np.array([
                0.5 + 0.5 * np.sin(hue),
                0.5 + 0.5 * np.sin(hue + 2.09),
                0.5 + 0.5 * np.sin(hue + 4.18),
                0.8
            ])
        elif color_mode == 'monochrome':
            intensity = random.uniform(0.3, 1.0)
            color = np.array([intensity, intensity, intensity, 0.8])
        else:  # electric
            color = np.array([random.uniform(0.8, 1.0), random.uniform(0.9, 1.0), random.uniform(0.4, 1.0), 0.9])
        
        return {
            'position': pos,
            'velocity': vel,
            'color': color,
            'size': random.uniform(0.5, 2.5),
            'energy': random.uniform(0.3, 1.8)
        }

    def mutate_particle(self, particle):
        """Apply random mutations to a particle"""
        mutation_strength = self.mutation_rate * 0.5
        
        # Mutate position
        particle['position'] += np.random.normal(0, mutation_strength * 0.5, 3)
        
        # Mutate velocity
        particle['velocity'] += np.random.normal(0, mutation_strength * 0.1, 3)
        particle['velocity'] = np.clip(particle['velocity'], -0.2, 0.2)
        
        # Mutate color
        particle['color'][:3] += np.random.normal(0, mutation_strength * 0.3, 3)
        particle['color'] = np.clip(particle['color'], 0, 1)
        
        # Mutate size
        particle['size'] += random.uniform(-mutation_strength, mutation_strength)
        particle['size'] = max(0.3, min(3.0, particle['size']))
        
        # Mutate energy
        particle['energy'] += random.uniform(-mutation_strength, mutation_strength)
        particle['energy'] = max(0.1, min(2.0, particle['energy']))
        
        return particle

    def update_particle_behaviors(self, dt):
        """Update particles based on their evolutionary behaviors"""
        for particle in self.particles:
            behavior = particle.get('behavior_type', 'wanderer')
            particle['age'] += dt
            
            # Apply behavior-specific movement
            if behavior == 'wanderer':
                # Random walk with momentum
                particle['velocity'] += np.random.normal(0, 0.01, 3) * self.energy_level
                particle['velocity'] *= 0.995  # Slight damping
                
            elif behavior == 'orbiter':
                # Orbital motion around center
                center = np.array([0, 0, 0])
                to_center = center - particle['position']
                dist = np.linalg.norm(to_center)
                if dist > 0.1:
                    # Perpendicular force for orbiting
                    orbital_force = np.array([-to_center[1], to_center[0], to_center[2] * 0.5])
                    orbital_force = orbital_force / (dist + 0.1) * particle['energy'] * 0.05
                    particle['velocity'] += orbital_force * dt
                    
            elif behavior == 'spiral':
                # Spiral motion
                angle = self.time + particle['age']
                spiral_force = np.array([
                    np.cos(angle) * 0.02,
                    np.sin(angle) * 0.02,
                    np.sin(angle * 0.5) * 0.01
                ]) * particle['energy']
                particle['velocity'] += spiral_force * dt
                
            elif behavior == 'chaotic':
                # Chaotic attractor-like behavior
                pos = particle['position']
                chaotic_force = np.array([
                    np.sin(pos[1] * 3 + self.time) * 0.03,
                    np.cos(pos[0] * 2.5 + self.time) * 0.03,
                    np.sin(pos[0] + pos[1] + self.time) * 0.02
                ]) * particle['energy']
                particle['velocity'] += chaotic_force * dt
                
            elif behavior == 'flocking':
                # Simple flocking behavior
                nearby_particles = [p for p in self.particles if np.linalg.norm(p['position'] - particle['position']) < 0.5]
                if len(nearby_particles) > 1:
                    # Average position of nearby particles
                    avg_pos = np.mean([p['position'] for p in nearby_particles], axis=0)
                    avg_vel = np.mean([p['velocity'] for p in nearby_particles], axis=0)
                    
                    # Cohesion + alignment
                    cohesion = (avg_pos - particle['position']) * 0.01
                    alignment = (avg_vel - particle['velocity']) * 0.02
                    
                    particle['velocity'] += (cohesion + alignment) * dt * particle['energy']
            
            # Update position
            particle['position'] += particle['velocity'] * dt * self.evolution_speed
            
            # Boundary wrapping
            for i in range(3):
                if particle['position'][i] > 2.0:
                    particle['position'][i] = -2.0
                elif particle['position'][i] < -2.0:
                    particle['position'][i] = 2.0
            
            # Update fitness (survival + activity)
            particle['fitness'] = particle['age'] * (1.0 + np.linalg.norm(particle['velocity']) * 10)

    def setup_particles(self):
        try:
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])

            # position (3) + color (4) + size (1) + velocity (3) = 11 floats per particle
            self.particle_data = np.zeros((self.num_particles, 11), dtype=np.float32)

            self.VAO = glGenVertexArrays(1)
            glBindVertexArray(self.VAO)

            self.VBO = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
            glBufferData(GL_ARRAY_BUFFER, self.particle_data.nbytes, self.particle_data, GL_DYNAMIC_DRAW)

            stride = 11 * ctypes.sizeof(GLfloat)
            
            # Position
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            # Color
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
            glEnableVertexAttribArray(1)
            # Size
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(7 * ctypes.sizeof(GLfloat)))
            glEnableVertexAttribArray(2)
            # Velocity
            glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8 * ctypes.sizeof(GLfloat)))
            glEnableVertexAttribArray(3)

            glBindVertexArray(0)
            print(f"EvolutiveParticles setup complete with {self.num_particles} particles")
        except Exception as e:
            print(f"Error setting up particles: {e}")

    def update_particle_data(self):
        """Update GPU buffer with current particle data"""
        if not self.particles:
            return
            
        for i, particle in enumerate(self.particles):
            if i >= self.num_particles:
                break
                
            # Position
            self.particle_data[i, 0:3] = particle['position']
            # Color
            self.particle_data[i, 3:7] = particle['color']
            # Size
            self.particle_data[i, 7] = particle['size']
            # Velocity
            self.particle_data[i, 8:11] = particle['velocity']

        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.particle_data.nbytes, self.particle_data)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def paintGL(self):
        try:
            glClear(GL_COLOR_BUFFER_BIT)

            if not self.initialized or not self.shader_program:
                glClearColor(0.1, 0.0, 0.2, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                return

            dt = 0.016  # Assume 60fps
            self.time += dt

            # Evolution timer
            self.evolution_timer += dt
            if self.evolution_timer >= self.evolution_interval:
                self.evolution_timer = 0
                self.evolve_new_generation()
                self.setup_particles()  # Recreate buffers for new generation

            # Update particle behaviors
            self.update_particle_behaviors(dt)
            self.update_particle_data()

            # Render
            glUseProgram(self.shader_program)
            
            glUniform1f(glGetUniformLocation(self.shader_program, "time"), self.time)
            glUniform1f(glGetUniformLocation(self.shader_program, "evolution_speed"), self.evolution_speed)
            glUniform1f(glGetUniformLocation(self.shader_program, "energy_level"), self.energy_level)

            glBindVertexArray(self.VAO)
            glDrawArrays(GL_POINTS, 0, min(len(self.particles), self.num_particles))
            glBindVertexArray(0)
            
            glUseProgram(0)

        except Exception as e:
            print(f"Error in paintGL: {e}")
            glClearColor(0.2, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def cleanup(self):
        print("Cleaning up EvolutiveParticlesVisualizer")
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