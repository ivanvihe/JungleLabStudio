import logging
import numpy as np
import ctypes
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import time
import math

from ..base_visualizer import BaseVisualizer


class BuildingMadnessVisualizer(BaseVisualizer):
    """Audio reactive infinite city visualizer - PROPERLY optimized for performance."""

    visual_name = "Building Madness"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.ebo = None
        self.time = 0.0
        
        # DRASTICALLY reduced for actual performance
        self.grid_size = 8
        self.building_layers = 1  # Single layer only
        self.camera_speed = 1.0
        self.rotation_speed = 0.3
        self.glow_intensity = 1.0
        self.perspective_warp = 0.5
        self.audio_response = 1.0
        self.color_shift = 0.0
        
        # Camera parameters
        self.camera_z = 5.0
        self.camera_rotation = 0.0
        
        # Building parameters
        self.max_height = 2.0
        self.building_data = []
        self.vertex_count = 0
        
        # Frame timing
        self.last_time = time.time()
        self.delta_time = 0.0
        
        # Audio smoothing - minimal but keep your FFT structure
        self.smooth_fft = np.zeros(8)  # Much smaller
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

    def initializeGL(self):
        """Initialize OpenGL resources."""
        try:
            glClearColor(0.0, 0.0, 0.05, 1.0)
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LESS)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)
            
            if not self._load_shaders():
                logging.error("BuildingMadness: shader compilation failed")
                return
                
            self._setup_geometry()
            
        except Exception as exc:
            logging.error(f"BuildingMadness.initializeGL error: {exc}")

    def _load_shaders(self) -> bool:
        """MINIMAL shaders - the main performance killer was here!"""
        try:
            # ULTRA SIMPLE vertex shader
            vertex_src = """
            #version 330 core
            layout(location = 0) in vec3 aPos;
            layout(location = 1) in vec3 aNormal;
            layout(location = 2) in vec2 aTexCoord;
            layout(location = 3) in vec4 aColor;
            layout(location = 4) in float aGlow;
            
            out vec3 Normal;
            out vec2 TexCoord;
            out vec4 Color;
            out float Glow;
            out float Depth;
            
            uniform mat4 projection;
            uniform mat4 view;
            uniform mat4 model;
            uniform float time;
            uniform vec3 audioData;
            
            void main() {
                vec3 pos = aPos;
                
                // MINIMAL audio effect - just a tiny bit of movement
                float audioInfluence = audioData.x * 0.1;
                pos.y += sin(pos.x + time) * 0.02 * audioInfluence;
                
                vec4 worldPosition = model * vec4(pos, 1.0);
                vec4 viewPosition = view * worldPosition;
                gl_Position = projection * viewPosition;
                
                Normal = aNormal;  // Skip expensive normal transformation
                TexCoord = aTexCoord;
                Color = aColor;
                Glow = aGlow + audioData.z * 0.1;
                Depth = -viewPosition.z;
            }
            """

            # ULTRA SIMPLE fragment shader - this was killing your GPU!
            fragment_src = """
            #version 330 core
            in vec3 Normal;
            in vec2 TexCoord;
            in vec4 Color;
            in float Glow;
            in float Depth;
            
            out vec4 FragColor;
            
            uniform float time;
            uniform vec3 audioData;
            uniform float glowIntensity;
            
            // Simple noise for basic variation
            float random(vec2 st) {
                return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
            }
            
            void main() {
                // SIMPLE window pattern - no complex calculations
                vec2 grid = fract(TexCoord * 4.0);
                float window = step(0.1, grid.x) * step(grid.x, 0.9) * 
                              step(0.1, grid.y) * step(grid.y, 0.9);
                
                // Window lighting with simple randomness
                vec2 windowId = floor(TexCoord * 4.0);
                float lightOn = random(windowId) > 0.5 ? 0.8 : 0.1;
                
                // Simple audio reaction
                lightOn = clamp(lightOn + audioData.x * 0.3, 0.0, 1.0);
                
                // Base color
                vec3 baseColor = Color.rgb;
                
                // Simple window glow
                vec3 windowColor = vec3(0.8, 0.7, 0.5) * window * lightOn;
                baseColor += windowColor;
                
                // MINIMAL lighting - just one fixed light
                float diff = max(dot(Normal, vec3(0.5, 0.8, 0.5)), 0.3);
                baseColor *= diff;
                
                // Simple audio glow
                baseColor += vec3(audioData.x, audioData.y * 0.5, audioData.z) * Glow * glowIntensity * 0.4;
                
                // Simple fog
                float fog = exp(-Depth * 0.01);
                baseColor = mix(vec3(0.0, 0.0, 0.08), baseColor, fog);
                
                FragColor = vec4(baseColor, Color.a);
            }
            """

            self.shader_program = compileProgram(
                compileShader(vertex_src, GL_VERTEX_SHADER),
                compileShader(fragment_src, GL_FRAGMENT_SHADER)
            )
            
            return True
            
        except Exception as exc:
            logging.error(f"BuildingMadness shader load error: {exc}")
            return False

    def _setup_geometry(self):
        """MINIMAL geometry - much fewer buildings."""
        vertices = []
        indices = []
        vertex_offset = 0
        
        # SINGLE layer only, much fewer buildings
        for x in range(-self.grid_size, self.grid_size, 2):  # Skip every other position
            for z in range(-self.grid_size, self.grid_size, 2):
                # Even fewer buildings
                seed_value = abs(hash((x, z))) % (2**32 - 1)
                np.random.seed(seed_value)
                
                if np.random.random() > 0.6:  # Only 40% buildings
                    continue
                
                # Simple parameters
                height = np.random.uniform(1.0, self.max_height)
                width = 0.7
                depth = 0.7
                
                pos_x = x * 2.0
                pos_z = z * 2.0
                
                r = 0.1 + np.random.random() * 0.05
                g = 0.1 + np.random.random() * 0.05
                b = 0.15 + np.random.random() * 0.05
                glow = np.random.random() * 0.1
                
                # Create SIMPLE box
                building_verts, building_indices = self._create_simple_box(
                    pos_x, 0, pos_z, width, height, depth,
                    r, g, b, 1.0, glow, vertex_offset
                )
                
                vertices.extend(building_verts)
                indices.extend(building_indices)
                vertex_offset += len(building_verts) // 11
        
        if not vertices:  # Safety check
            # Create at least one building
            vertices, indices = self._create_simple_box(0, 0, 0, 1, 2, 1, 0.1, 0.1, 0.2, 1.0, 0.1, 0)
        
        self.vertex_data = np.array(vertices, dtype=np.float32)
        self.index_data = np.array(indices, dtype=np.uint32)
        self.vertex_count = len(self.index_data)
        
        # Create buffers
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertex_data.nbytes, self.vertex_data, GL_STATIC_DRAW)
        
        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_data.nbytes, self.index_data, GL_STATIC_DRAW)
        
        stride = 11 * ctypes.sizeof(GLfloat)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(10 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(4)
        
        glBindVertexArray(0)

    def _create_simple_box(self, x, y, z, width, height, depth, r, g, b, a, glow, offset):
        """Create the SIMPLEST possible box - 8 vertices, 12 triangles."""
        vertices = []
        indices = []
        
        hw, hh, hd = width/2, height, depth/2
        
        # Just 8 vertices for a box
        box_verts = [
            # Bottom face (y=0)
            [-hw, y, -hd], [hw, y, -hd], [hw, y, hd], [-hw, y, hd],
            # Top face (y=height)
            [-hw, y+hh, -hd], [hw, y+hh, -hd], [hw, y+hh, hd], [-hw, y+hh, hd]
        ]
        
        # Normals for each vertex (approximate)
        normals = [
            [0, -1, 0], [0, -1, 0], [0, -1, 0], [0, -1, 0],  # Bottom
            [0, 1, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0]       # Top
        ]
        
        # Simple UV coordinates for windows
        uvs = [
            [0, 0], [1, 0], [1, 1], [0, 1],
            [0, 0], [1, 0], [1, 1], [0, 1]
        ]
        
        # Create vertex data
        for i in range(8):
            px, py, pz = box_verts[i]
            nx, ny, nz = normals[i]
            tx, ty = uvs[i]
            vertices.extend([
                x + px, py, z + pz,
                nx, ny, nz,
                tx, ty,
                r, g, b, a,
                glow
            ])
        
        # Box indices (12 triangles = 36 indices)
        box_indices = [
            # Bottom face
            0, 2, 1, 0, 3, 2,
            # Top face  
            4, 5, 6, 4, 6, 7,
            # Front face
            3, 6, 2, 3, 7, 6,
            # Back face
            0, 1, 5, 0, 5, 4,
            # Left face
            0, 4, 7, 0, 7, 3,
            # Right face
            1, 2, 6, 1, 6, 5
        ]
        
        for idx in box_indices:
            indices.append(offset + idx)
        
        return vertices, indices

    def paintGL(self):
        """Render with MINIMAL processing but keep your audio structure."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if not self.shader_program or self.vao is None:
            return
        
        current_time = time.time()
        self.delta_time = current_time - self.last_time
        self.last_time = current_time
        self.time += self.delta_time * self.camera_speed
        
        # Keep your audio processing but simplified
        if hasattr(self, "analyzer") and self.analyzer and self.analyzer.is_active():
            fft = self.analyzer.get_fft_data().astype(np.float32)
            # Much simpler interpolation - just take first 8 values
            if len(fft) >= 8:
                target_fft = fft[:8]
            else:
                target_fft = np.pad(fft, (0, 8 - len(fft)), 'constant')
            
            self.smooth_fft = self.smooth_fft * 0.8 + target_fft * 0.2
            
            # Calculate frequency bands - much simpler
            self.bass_energy = np.mean(self.smooth_fft[:3]) / 150.0 * self.audio_response
            self.mid_energy = np.mean(self.smooth_fft[3:6]) / 150.0 * self.audio_response
            self.high_energy = np.mean(self.smooth_fft[6:]) / 150.0 * self.audio_response
        else:
            # Demo mode
            self.bass_energy = (math.sin(self.time * 0.5) * 0.5 + 0.5) * self.audio_response * 0.3
            self.mid_energy = (math.sin(self.time * 0.7) * 0.5 + 0.5) * self.audio_response * 0.3
            self.high_energy = (math.sin(self.time * 1.1) * 0.5 + 0.5) * self.audio_response * 0.3
        
        # Get viewport
        viewport = glGetIntegerv(GL_VIEWPORT)
        width = viewport[2]
        height = viewport[3]
        aspect = width / height if height > 0 else 1.0
        
        # SIMPLE matrices
        projection = self._perspective_matrix(60.0, aspect, 0.1, 50.0)
        
        self.camera_rotation += self.rotation_speed * self.delta_time
        cam_radius = 15.0  # Further back to see more
        cam_x = math.sin(self.camera_rotation) * cam_radius
        cam_z = math.cos(self.camera_rotation) * cam_radius
        cam_y = 8.0 + self.bass_energy * 2.0
        
        view = self._look_at_matrix([cam_x, cam_y, cam_z], [0, 0, 0], [0, 1, 0])
        model = np.identity(4, dtype=np.float32)
        
        glUseProgram(self.shader_program)
        
        # Set minimal uniforms
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model)
        
        glUniform1f(glGetUniformLocation(self.shader_program, "time"), self.time)
        glUniform1f(glGetUniformLocation(self.shader_program, "glowIntensity"), self.glow_intensity)
        glUniform3f(glGetUniformLocation(self.shader_program, "audioData"), 
                   self.bass_energy, self.mid_energy, self.high_energy)
        
        # Draw
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.vertex_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glUseProgram(0)

    def _perspective_matrix(self, fov, aspect, near, far):
        """Create perspective projection matrix."""
        f = 1.0 / math.tan(math.radians(fov) / 2.0)
        nf = 1.0 / (near - far)
        return np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) * nf, 2 * far * near * nf],
            [0, 0, -1, 0]
        ], dtype=np.float32).T

    def _look_at_matrix(self, eye, center, up):
        """Create view matrix."""
        eye = np.array(eye, dtype=np.float32)
        center = np.array(center, dtype=np.float32)
        up = np.array(up, dtype=np.float32)
        
        f = center - eye
        f = f / np.linalg.norm(f)
        s = np.cross(f, up)
        s = s / np.linalg.norm(s)
        u = np.cross(s, f)
        
        result = np.identity(4, dtype=np.float32)
        result[0, :3] = s
        result[1, :3] = u
        result[2, :3] = -f
        result[3, :3] = -np.dot(result[:3, :3], eye)
        return result.T

    def get_controls(self):
        """Get control parameters - keep your structure."""
        controls = super().get_controls()
        controls.update({
            "Grid Size": {
                "type": "slider",
                "min": 3,
                "max": 12,  # Reduced max for performance
                "value": self.grid_size,
            },
            "Camera Speed": {
                "type": "slider",
                "min": 0.1,
                "max": 2.0,  # Reduced max
                "value": self.camera_speed,
                "step": 0.1
            },
            "Rotation Speed": {
                "type": "slider",
                "min": 0.0,
                "max": 1.0,
                "value": self.rotation_speed,
                "step": 0.05
            },
            "Glow Intensity": {
                "type": "slider",
                "min": 0.0,
                "max": 1.5,  # Reduced max
                "value": self.glow_intensity,
                "step": 0.1
            },
            "Warp Effect": {
                "type": "slider",
                "min": 0.0,
                "max": 1.0,
                "value": self.perspective_warp,
                "step": 0.05
            },
            "Audio Response": {
                "type": "slider",
                "min": 0.0,
                "max": 2.0,  # Reduced max
                "value": self.audio_response,
                "step": 0.1
            },
            "Color Shift": {
                "type": "slider",
                "min": 0.0,
                "max": 6.28,
                "value": self.color_shift,
                "step": 0.1
            }
        })
        return controls

    def update_control(self, name, value):
        """Update control values - keep your structure."""
        if super().update_control(name, value):
            return
        if name == "Grid Size":
            self.grid_size = int(value)
            self._setup_geometry()
        elif name == "Camera Speed":
            self.camera_speed = float(value)
        elif name == "Rotation Speed":
            self.rotation_speed = float(value)
        elif name == "Glow Intensity":
            self.glow_intensity = float(value)
        elif name == "Warp Effect":
            self.perspective_warp = float(value)
        elif name == "Audio Response":
            self.audio_response = float(value)
        elif name == "Color Shift":
            self.color_shift = float(value)

    def cleanup(self):
        """Clean up OpenGL resources."""
        try:
            if self.shader_program:
                glDeleteProgram(self.shader_program)
                self.shader_program = None
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.ebo:
                glDeleteBuffers(1, [self.ebo])
                self.ebo = None
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
                self.vao = None
        except Exception as exc:
            logging.error(f"BuildingMadness.cleanup error: {exc}")