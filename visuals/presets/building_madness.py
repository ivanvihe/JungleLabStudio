from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import ctypes
import os
import logging

from visuals.base_visualizer import BaseVisualizer

class BuildingMadnessVisualizer(BaseVisualizer):
    visual_name = "Building Madness"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.VBO = None
        self.VAO = None
        self.EBO = None
        self.vertices = None
        self.indices = None
        self.original_vertices = None
        self.time = 0.0
        self.room_type = 0
        self.speed = 1.0
        self.intensity = 1.0
        self.complexity = 1.0
        self.effect_mode = 0

    def get_controls(self):
        return {
            "Room Type": {
                "type": "dropdown",
                "options": ["Cube Room", "Sphere Room", "Tunnel Room", "Pyramid Room", "Crystal Room"],
                "value": self.room_type,
            },
            "Speed": {
                "type": "slider",
                "min": 1,
                "max": 100,
                "value": int(self.speed * 20),
            },
            "Intensity": {
                "type": "slider",
                "min": 1,
                "max": 100,
                "value": int(self.intensity * 50),
            },
            "Complexity": {
                "type": "slider",
                "min": 1,
                "max": 100,
                "value": int(self.complexity * 50),
            },
            "Effect Mode": {
                "type": "dropdown",
                "options": ["Wave Patterns", "Fractal Growth", "Mirror Kaleidoscope", "Digital Rain", "Plasma Flow"],
                "value": self.effect_mode,
            }
        }

    def update_control(self, name, value):
        if name == "Room Type":
            if self.room_type != int(value):
                self.room_type = int(value)
                self.create_room()
        elif name == "Speed":
            self.speed = float(value) / 20.0
        elif name == "Intensity":
            self.intensity = float(value) / 50.0
        elif name == "Complexity":
            if abs(self.complexity - float(value) / 50.0) > 0.1:
                self.complexity = float(value) / 50.0
                self.create_room()
        elif name == "Effect Mode":
            self.effect_mode = int(value)

    def initializeGL(self):
        print("BuildingMadnessVisualizer.initializeGL called")
        # TRANSPARENT BACKGROUND FOR MIXING
        glClearColor(0.0, 0.0, 0.0, 0.0)  # Alpha = 0 for transparency
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_CULL_FACE)  # Important to see inside faces

        self.load_shaders()
        self.create_room()

    def load_shaders(self):
        script_dir = os.path.dirname(__file__)
        shader_dir = os.path.join(script_dir, '..', '..', 'shaders')

        try:
            with open(os.path.join(shader_dir, 'basic.vert'), 'r') as f:
                vertex_shader_source = f.read()
            with open(os.path.join(shader_dir, 'basic.frag'), 'r') as f:
                fragment_shader_source = f.read()

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
            print("BuildingMadness shaders loaded successfully")
        except Exception as e:
            print(f"BuildingMadness shader loading error: {e}")

    def create_cube_room(self):
        """Create a cube room with subdivided walls for effects"""
        vertices = []
        indices = []
        
        size = 10.0
        subdivisions = max(10, int(20 * self.complexity))
        
        # Define the 6 walls of the cube (inside faces)
        walls = [
            # Floor (looking up at it)
            {'vertices': [[-size, -size, -size], [size, -size, -size], [size, -size, size], [-size, -size, size]], 'normal': [0, 1, 0]},
            # Ceiling (looking down at it) 
            {'vertices': [[-size, size, -size], [-size, size, size], [size, size, size], [size, size, -size]], 'normal': [0, -1, 0]},
            # Front wall
            {'vertices': [[-size, -size, size], [size, -size, size], [size, size, size], [-size, size, size]], 'normal': [0, 0, -1]},
            # Back wall
            {'vertices': [[size, -size, -size], [-size, -size, -size], [-size, size, -size], [size, size, -size]], 'normal': [0, 0, 1]},
            # Left wall
            {'vertices': [[-size, -size, -size], [-size, -size, size], [-size, size, size], [-size, size, -size]], 'normal': [1, 0, 0]},
            # Right wall
            {'vertices': [[size, -size, size], [size, -size, -size], [size, size, -size], [size, size, size]], 'normal': [-1, 0, 0]}
        ]
        
        for wall in walls:
            start_vertex = len(vertices) // 7
            wall_verts = wall['vertices']
            
            # Create subdivided grid for this wall
            for i in range(subdivisions + 1):
                for j in range(subdivisions + 1):
                    u = i / subdivisions
                    v = j / subdivisions
                    
                    # Bilinear interpolation
                    p1 = np.array(wall_verts[0]) * (1-u) * (1-v)
                    p2 = np.array(wall_verts[1]) * u * (1-v)
                    p3 = np.array(wall_verts[2]) * u * v
                    p4 = np.array(wall_verts[3]) * (1-u) * v
                    
                    pos = p1 + p2 + p3 + p4
                    
                    # Initial color based on position and wall with transparency
                    r = 0.5 + 0.3 * np.sin(u * np.pi)
                    g = 0.5 + 0.3 * np.cos(v * np.pi)
                    b = 0.7
                    alpha = 0.8  # Semi-transparent for mixing
                    
                    vertices.extend([pos[0], pos[1], pos[2], r, g, b, alpha])
            
            # Create triangles for this wall
            for i in range(subdivisions):
                for j in range(subdivisions):
                    base = start_vertex + i * (subdivisions + 1) + j
                    
                    # Two triangles per quad
                    indices.extend([base, base + 1, base + subdivisions + 1])
                    indices.extend([base + 1, base + subdivisions + 2, base + subdivisions + 1])
        
        return vertices, indices

    def create_sphere_room(self):
        """Create a spherical room"""
        vertices = []
        indices = []
        
        radius = 8.0
        lat_segments = max(20, int(30 * self.complexity))
        lon_segments = max(30, int(40 * self.complexity))
        
        # Create sphere vertices (inside view)
        for lat in range(lat_segments + 1):
            theta = lat * np.pi / lat_segments
            for lon in range(lon_segments + 1):
                phi = lon * 2 * np.pi / lon_segments
                
                x = radius * np.sin(theta) * np.cos(phi)
                y = radius * np.cos(theta)
                z = radius * np.sin(theta) * np.sin(phi)
                
                # Color based on spherical coordinates
                r = 0.5 + 0.5 * np.sin(theta * 2)
                g = 0.5 + 0.5 * np.cos(phi)
                b = 0.5 + 0.5 * np.sin(phi * 2)
                alpha = 0.8  # Semi-transparent
                
                vertices.extend([x, y, z, r, g, b, alpha])
        
        # Create triangles (note reversed winding for inside view)
        for lat in range(lat_segments):
            for lon in range(lon_segments):
                first = lat * (lon_segments + 1) + lon
                second = first + lon_segments + 1
                
                # Reverse winding for inside view
                indices.extend([first, second, first + 1])
                indices.extend([second, second + 1, first + 1])
        
        return vertices, indices

    def create_tunnel_room(self):
        """Create a cylindrical tunnel"""
        vertices = []
        indices = []
        
        radius = 6.0
        length = 20.0
        segments = max(30, int(50 * self.complexity))
        rings = max(20, int(30 * self.complexity))
        
        # Create tunnel
        for ring in range(rings + 1):
            z = -length/2 + (ring / rings) * length
            
            for seg in range(segments + 1):
                angle = seg * 2 * np.pi / segments
                
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                
                # Color based on position
                r = 0.5 + 0.5 * np.sin(angle * 3)
                g = 0.5 + 0.5 * np.cos(z * 0.2)
                b = 0.8
                alpha = 0.7  # Semi-transparent
                
                vertices.extend([x, y, z, r, g, b, alpha])
        
        # Create triangles (inside view)
        for ring in range(rings):
            for seg in range(segments):
                current = ring * (segments + 1) + seg
                next_ring = (ring + 1) * (segments + 1) + seg
                next_seg = ring * (segments + 1) + ((seg + 1) % (segments + 1))
                next_both = (ring + 1) * (segments + 1) + ((seg + 1) % (segments + 1))
                
                # Reverse winding for inside view
                indices.extend([current, next_seg, next_ring])
                indices.extend([next_seg, next_both, next_ring])
        
        return vertices, indices

    def create_pyramid_room(self):
        """Create a pyramid room"""
        vertices = []
        indices = []
        
        size = 8.0
        height = 10.0
        subdivisions = max(15, int(25 * self.complexity))
        
        # Base of pyramid (square)
        base_verts = [[-size, -height, -size], [size, -height, -size], [size, -height, size], [-size, -height, size]]
        apex = [0, height, 0]
        
        # Create base with subdivisions
        start_vertex = len(vertices) // 7
        for i in range(subdivisions + 1):
            for j in range(subdivisions + 1):
                u = i / subdivisions
                v = j / subdivisions
                
                # Base position
                p1 = np.array(base_verts[0]) * (1-u) * (1-v)
                p2 = np.array(base_verts[1]) * u * (1-v)
                p3 = np.array(base_verts[2]) * u * v
                p4 = np.array(base_verts[3]) * (1-u) * v
                
                pos = p1 + p2 + p3 + p4
                
                r = 0.8 * (1 - u * 0.3)
                g = 0.6 * (1 - v * 0.3)
                b = 0.9
                alpha = 0.75  # Semi-transparent
                
                vertices.extend([pos[0], pos[1], pos[2], r, g, b, alpha])
        
        # Base triangles
        for i in range(subdivisions):
            for j in range(subdivisions):
                base = start_vertex + i * (subdivisions + 1) + j
                indices.extend([base, base + subdivisions + 1, base + 1])
                indices.extend([base + 1, base + subdivisions + 1, base + subdivisions + 2])
        
        return vertices, indices

    def create_crystal_room(self):
        """Create a crystalline room"""
        vertices = []
        indices = []
        
        # Create multiple crystal faces
        num_faces = max(8, int(12 * self.complexity))
        radius = 8.0
        
        for face in range(num_faces):
            angle = face * 2 * np.pi / num_faces
            height_variation = np.sin(face * 1.5) * 2
            
            # Create crystal face
            subdivisions = max(8, int(15 * self.complexity))
            face_start = len(vertices) // 7
            
            for i in range(subdivisions + 1):
                for j in range(subdivisions + 1):
                    u = i / subdivisions
                    v = j / subdivisions
                    
                    # Create faceted surface
                    x = radius * np.cos(angle) * (1 - u) + radius * np.cos(angle + 2*np.pi/num_faces) * u
                    y = -radius + v * (2 * radius + height_variation)
                    z = radius * np.sin(angle) * (1 - u) + radius * np.sin(angle + 2*np.pi/num_faces) * u
                    
                    # Crystal colors
                    r = 0.3 + 0.7 * np.sin(angle + u * np.pi)
                    g = 0.4 + 0.6 * np.cos(v * np.pi)
                    b = 0.8 + 0.2 * np.sin(angle * 2)
                    alpha = 0.6  # More transparent for crystal effect
                    
                    vertices.extend([x, y, z, r, g, b, alpha])
            
            # Create triangles for this face
            for i in range(subdivisions):
                for j in range(subdivisions):
                    base = face_start + i * (subdivisions + 1) + j
                    indices.extend([base, base + 1, base + subdivisions + 1])
                    indices.extend([base + 1, base + subdivisions + 2, base + subdivisions + 1])
        
        return vertices, indices

    def create_room(self):
        """Create the room geometry based on selected type"""
        try:
            if self.room_type == 0:
                vertices, indices = self.create_cube_room()
            elif self.room_type == 1:
                vertices, indices = self.create_sphere_room()
            elif self.room_type == 2:
                vertices, indices = self.create_tunnel_room()
            elif self.room_type == 3:
                vertices, indices = self.create_pyramid_room()
            else:
                vertices, indices = self.create_crystal_room()
            
            self.vertices = np.array(vertices, dtype=np.float32)
            self.indices = np.array(indices, dtype=np.uint32)
            self.original_vertices = self.vertices.copy()
            
            self.setup_buffers()
            
        except Exception as e:
            print(f"Error creating room: {e}")
            # Fallback geometry
            self.vertices = np.array([
                -5, -5, -5, 1, 0, 0, 0.8,
                 5, -5, -5, 0, 1, 0, 0.8,
                 5,  5, -5, 0, 0, 1, 0.8,
                -5,  5, -5, 1, 1, 0, 0.8
            ], dtype=np.float32)
            self.indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
            self.original_vertices = self.vertices.copy()
            self.setup_buffers()

    def setup_buffers(self):
        """Setup OpenGL buffers"""
        try:
            if self.VAO:
                glDeleteVertexArrays(1, [self.VAO])
            if self.VBO:
                glDeleteBuffers(1, [self.VBO])
            if self.EBO:
                glDeleteBuffers(1, [self.EBO])

            self.VAO = glGenVertexArrays(1)
            glBindVertexArray(self.VAO)

            self.VBO = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
            glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)

            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * ctypes.sizeof(GLfloat), ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
            glEnableVertexAttribArray(1)

            self.EBO = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

            glBindVertexArray(0)
        except Exception as e:
            print(f"Buffer setup error: {e}")

    def apply_wall_effects(self):
        """Apply visual effects to the walls based on effect mode"""
        if self.original_vertices is None:
            return
            
        try:
            vertex_count = len(self.vertices) // 7
            
            for i in range(vertex_count):
                idx = i * 7
                if idx + 6 >= len(self.vertices):
                    break
                
                # Get original position and color
                orig_x = self.original_vertices[idx]
                orig_y = self.original_vertices[idx + 1]
                orig_z = self.original_vertices[idx + 2]
                orig_r = self.original_vertices[idx + 3]
                orig_g = self.original_vertices[idx + 4]
                orig_b = self.original_vertices[idx + 5]
                orig_a = self.original_vertices[idx + 6]
                
                # Apply different effects based on mode
                if self.effect_mode == 0:  # Wave Patterns
                    wave_x = np.sin(self.time * self.speed + orig_x * 0.5) * 0.3 * self.intensity
                    wave_y = np.cos(self.time * self.speed + orig_y * 0.5) * 0.3 * self.intensity
                    wave_z = np.sin(self.time * self.speed + orig_z * 0.5) * 0.3 * self.intensity
                    
                    color_wave = 0.5 + 0.5 * np.sin(self.time * self.speed * 2 + orig_x + orig_y + orig_z)
                    
                elif self.effect_mode == 1:  # Fractal Growth
                    distance = np.sqrt(orig_x**2 + orig_y**2 + orig_z**2)
                    fractal = np.sin(distance * 0.3 + self.time * self.speed) * self.intensity
                    
                    wave_x = fractal * 0.2
                    wave_y = fractal * 0.2
                    wave_z = fractal * 0.2
                    
                    color_wave = 0.5 + 0.5 * fractal
                    
                elif self.effect_mode == 2:  # Mirror Kaleidoscope
                    angle = np.arctan2(orig_z, orig_x)
                    radius = np.sqrt(orig_x**2 + orig_z**2)
                    
                    mirror_angle = angle * 3 + self.time * self.speed
                    kaleidoscope = np.sin(mirror_angle) * np.cos(radius * 0.2 + self.time * self.speed)
                    
                    wave_x = kaleidoscope * 0.5 * self.intensity
                    wave_y = kaleidoscope * 0.3 * self.intensity
                    wave_z = kaleidoscope * 0.5 * self.intensity
                    
                    color_wave = 0.5 + 0.5 * kaleidoscope
                    
                elif self.effect_mode == 3:  # Digital Rain
                    rain = np.sin(self.time * self.speed * 5 + orig_x * 2 + orig_z * 2) * self.intensity
                    
                    wave_x = 0
                    wave_y = rain * 0.2
                    wave_z = 0
                    
                    # Digital green effect
                    color_wave = 0.3 + 0.7 * np.abs(rain)
                    
                else:  # Plasma Flow
                    plasma_x = np.sin(orig_x * 0.2 + self.time * self.speed)
                    plasma_y = np.cos(orig_y * 0.2 + self.time * self.speed * 1.3)
                    plasma_z = np.sin(orig_z * 0.2 + self.time * self.speed * 0.7)
                    
                    plasma = plasma_x * plasma_y * plasma_z * self.intensity
                    
                    wave_x = plasma * 0.3
                    wave_y = plasma * 0.3
                    wave_z = plasma * 0.3
                    
                    color_wave = 0.5 + 0.5 * plasma
                
                # Apply position changes (subtle, just on surface)
                self.vertices[idx] = orig_x + wave_x
                self.vertices[idx + 1] = orig_y + wave_y
                self.vertices[idx + 2] = orig_z + wave_z
                
                # Apply color changes
                if self.effect_mode == 3:  # Digital Rain - green
                    self.vertices[idx + 3] = 0.1 * color_wave
                    self.vertices[idx + 4] = 0.9 * color_wave
                    self.vertices[idx + 5] = 0.3 * color_wave
                else:
                    self.vertices[idx + 3] = np.clip(orig_r * (0.5 + 0.5 * color_wave), 0, 1)
                    self.vertices[idx + 4] = np.clip(orig_g * (0.5 + 0.5 * np.sin(color_wave + 2)), 0, 1)
                    self.vertices[idx + 5] = np.clip(orig_b * (0.5 + 0.5 * np.cos(color_wave + 4)), 0, 1)
                
                # Keep original alpha for transparency
                self.vertices[idx + 6] = orig_a

            # Update buffer
            glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices.nbytes, self.vertices)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
        except Exception as e:
            print(f"Effect application error: {e}")

    def resizeGL(self, width, height):
        if height == 0:
            height = 1
        glViewport(0, 0, width, height)

    def paintGL(self):
        # CLEAR WITH TRANSPARENT BACKGROUND
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if self.shader_program is None or self.VAO is None:
            return
            
        try:
            glUseProgram(self.shader_program)

            # Update time and effects
            self.time += 0.016
            self.apply_wall_effects()

            # FIXED CAMERA - you're inside looking around
            # Camera is at origin, looking in different directions slightly
            camera_pos = [0, 0, 0]  # Fixed at center
            
            # Slight rotation to see the room better
            look_x = np.sin(self.time * 0.1) * 0.3
            look_y = np.cos(self.time * 0.07) * 0.2
            look_z = np.cos(self.time * 0.13) * 0.3
            
            look_at = [look_x, look_y, look_z]

            # Fixed matrices - room doesn't move
            projection = self.perspective(90, 1.0, 0.1, 50.0)  # Wide FOV to see the room
            view = self.lookAt(
                np.array(camera_pos),
                np.array(look_at),
                np.array([0, 1, 0])
            )
            model = np.identity(4, dtype=np.float32)  # No movement

            # Set uniforms
            proj_loc = glGetUniformLocation(self.shader_program, "projection")
            view_loc = glGetUniformLocation(self.shader_program, "view")
            model_loc = glGetUniformLocation(self.shader_program, "model")
            
            if proj_loc != -1:
                glUniformMatrix4fv(proj_loc, 1, GL_FALSE, projection)
            if view_loc != -1:
                glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)
            if model_loc != -1:
                glUniformMatrix4fv(model_loc, 1, GL_FALSE, model)

            # Draw the room
            glBindVertexArray(self.VAO)
            glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
            glBindVertexArray(0)

        except Exception as e:
            print(f"Paint error: {e}")

    def perspective(self, fov, aspect, near, far):
        f = 1.0 / np.tan(np.radians(fov / 2.0))
        return np.array([
            [f / aspect, 0.0, 0.0, 0.0],
            [0.0, f, 0.0, 0.0],
            [0.0, 0.0, (far + near) / (near - far), -1.0],
            [0.0, 0.0, (2.0 * far * near) / (near - far), 0.0]
        ], dtype=np.float32)

    def lookAt(self, eye, center, up):
        try:
            f = (center - eye) / np.linalg.norm(center - eye)
            s = np.cross(f, up) / np.linalg.norm(np.cross(f, up))
            u = np.cross(s, f)

            return np.array([
                [s[0], u[0], -f[0], 0.0],
                [s[1], u[1], -f[1], 0.0],
                [s[2], u[2], -f[2], 0.0],
                [-np.dot(s, eye), -np.dot(u, eye), np.dot(f, eye), 1.0]
            ], dtype=np.float32).T
        except:
            return np.identity(4, dtype=np.float32)

    def cleanup(self):
        print("Cleaning up BuildingMadnessVisualizer")
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
            if self.EBO:
                glDeleteBuffers(1, [self.EBO])
                self.EBO = None
        except Exception as e:
            print(f"Error during cleanup: {e}")