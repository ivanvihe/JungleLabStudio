import logging
import numpy as np
import ctypes
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import time
import math

from ..base_visualizer import BaseVisualizer


class BuildingMadnessVisualizer(BaseVisualizer):
    """Audio reactive infinite city visualizer - Balanced performance optimization."""

    visual_name = "Building Madness"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.ebo = None
        self.time = 0.0
        
        # Slightly reduced complexity but maintain visual quality
        self.grid_size = 12  # Reduced from 15 but not too much
        self.building_layers = 3  # Keep original layers
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
        self.max_height = 3.0
        self.building_data = []
        self.vertex_count = 0
        
        # Frame timing
        self.last_time = time.time()
        self.delta_time = 0.0
        
        # Audio smoothing
        self.smooth_fft = np.zeros(24)  # Reduced from 32 but not too much
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

    def initializeGL(self):
        """Initialize OpenGL resources."""
        try:
            # Dark space background
            glClearColor(0.0, 0.0, 0.05, 1.0)
            
            # Enable depth testing and blending
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LESS)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            # Enable face culling for performance
            glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)
            
            if not self._load_shaders():
                logging.error("BuildingMadness: shader compilation failed")
                return
                
            self._setup_geometry()
            
        except Exception as exc:
            logging.error(f"BuildingMadness.initializeGL error: {exc}")

    def _load_shaders(self) -> bool:
        """Compile and link moderately optimized shaders."""
        try:
            # Keep most vertex shader features but simplify some calculations
            vertex_src = """
            #version 330 core
            layout(location = 0) in vec3 aPos;
            layout(location = 1) in vec3 aNormal;
            layout(location = 2) in vec2 aTexCoord;
            layout(location = 3) in vec4 aColor;
            layout(location = 4) in float aGlow;
            
            out vec3 FragPos;
            out vec3 Normal;
            out vec2 TexCoord;
            out vec4 Color;
            out float Glow;
            out float Depth;
            out vec3 WorldPos;
            
            uniform mat4 projection;
            uniform mat4 view;
            uniform mat4 model;
            uniform float time;
            uniform float warp;
            uniform vec3 audioData;
            
            void main() {
                vec3 pos = aPos;
                float audioInfluence = audioData.x * 0.25 + audioData.y * 0.15;
                
                // Simplified but still nice wave effects
                pos.y += sin(pos.x * 1.5 + time * 1.5) * 0.08 * audioInfluence;
                pos.y += cos(pos.z * 1.5 + time * 1.2) * 0.08 * audioInfluence;
                
                // Reduced tesseract warping (still visible but less expensive)
                float dist = length(pos.xz);
                float warpFactor = 1.0 + warp * sin(dist * 0.4 - time * 0.8) * 0.15;
                pos.xz *= warpFactor;
                
                // Simplified space-time distortion
                float bend = sin(time * 0.4 + dist * 0.2) * warp * 0.2;
                float cosB = cos(bend);
                float sinB = sin(bend);
                vec2 rotated = vec2(cosB * pos.x - sinB * pos.z, sinB * pos.x + cosB * pos.z);
                pos.xz = rotated;
                
                vec4 worldPosition = model * vec4(pos, 1.0);
                vec4 viewPosition = view * worldPosition;
                gl_Position = projection * viewPosition;
                
                FragPos = vec3(worldPosition);
                WorldPos = pos;
                Normal = mat3(transpose(inverse(model))) * aNormal;
                TexCoord = aTexCoord;
                Color = aColor;
                Glow = aGlow + audioData.z * 0.4;
                Depth = -viewPosition.z;
            }
            """

            # Optimized fragment shader but keep the visual quality
            fragment_src = """
            #version 330 core
            in vec3 FragPos;
            in vec3 Normal;
            in vec2 TexCoord;
            in vec4 Color;
            in float Glow;
            in float Depth;
            in vec3 WorldPos;
            
            out vec4 FragColor;
            
            uniform float time;
            uniform vec3 viewPos;
            uniform vec3 audioData;
            uniform float glowIntensity;
            uniform float colorShift;
            
            // Keep noise but optimize it
            float random(vec2 st) {
                return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
            }
            
            float noise(vec2 st) {
                vec2 i = floor(st);
                vec2 f = fract(st);
                float a = random(i);
                float b = random(i + vec2(1.0, 0.0));
                float c = random(i + vec2(0.0, 1.0));
                float d = random(i + vec2(1.0, 1.0));
                vec2 u = f * f * (3.0 - 2.0 * f);
                return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
            }
            
            // Optimized but still good window function
            vec3 getWindowColor(vec2 uv, float glow) {
                vec2 grid = fract(uv);
                
                // Window frame
                float frameThickness = 0.08;
                float window = 1.0;
                window *= step(frameThickness, grid.x) * step(grid.x, 1.0 - frameThickness);
                window *= step(frameThickness, grid.y) * step(grid.y, 1.0 - frameThickness);
                
                // Floor separation
                float floorLine = step(0.95, fract(uv.y * 0.25));
                window *= 1.0 - floorLine;
                
                // Window lighting
                vec2 windowId = floor(uv);
                float lightOn = random(windowId) > 0.4 ? 1.0 : 0.0;
                
                // Some animated windows (but not all to reduce cost)
                if(random(windowId * 0.5) > 0.9) {
                    lightOn *= (sin(time * 4.0 + random(windowId) * 15.0) * 0.5 + 0.5);
                }
                
                // Audio reaction
                lightOn = clamp(lightOn + audioData.x * 0.25, 0.0, 1.0);
                
                // Window colors
                vec3 windowColor = vec3(1.0, 0.9, 0.7) * lightOn * window * 0.7;
                
                // Some colored windows (reduced frequency)
                float colorType = random(windowId * 2.0);
                if(colorType > 0.92) {
                    windowColor = vec3(0.0, 0.7, 1.0) * lightOn * window;
                } else if(colorType > 0.88) {
                    windowColor = vec3(1.0, 0.3, 0.6) * lightOn * window;
                }
                
                // Reflections
                float reflection = (1.0 - window) * 0.25;
                windowColor += vec3(0.08, 0.12, 0.18) * reflection;
                
                // Window glow
                windowColor += vec3(0.1, 0.25, 0.5) * glow * 1.5 * audioData.y;
                
                // Building frame
                vec3 frameColor = vec3(0.12, 0.12, 0.15) * (1.0 - window);
                
                return windowColor + frameColor;
            }
            
            void main() {
                vec3 norm = normalize(Normal);
                vec3 viewDir = normalize(viewPos - FragPos);
                
                // Base color
                vec3 baseColor = Color.rgb * 0.6;
                float noiseVal = noise(TexCoord * 20.0 + vec2(time * 0.08, WorldPos.y * 0.08));
                baseColor = mix(baseColor, baseColor * 1.3, noiseVal * 0.3);
                
                // Window texture
                vec3 windowTex = getWindowColor(TexCoord, Glow);
                baseColor = mix(baseColor, windowTex, 0.8);
                
                // Two light sources instead of multiple (performance vs quality balance)
                vec3 lightPos1 = vec3(sin(time * 0.8) * 12.0, 8.0, cos(time * 0.8) * 12.0);
                vec3 lightPos2 = vec3(cos(time * 0.6) * 8.0, 6.0, sin(time * 0.6) * 8.0);
                
                vec3 lightDir1 = normalize(lightPos1 - FragPos);
                vec3 lightDir2 = normalize(lightPos2 - FragPos);
                
                float diff1 = max(dot(norm, lightDir1), 0.0);
                float diff2 = max(dot(norm, lightDir2), 0.0);
                
                vec3 diffuse = diff1 * vec3(0.9, 0.7, 0.5) + diff2 * vec3(0.5, 0.7, 0.9) * 0.6;
                
                // Specular (simplified but still present)
                vec3 reflectDir1 = reflect(-lightDir1, norm);
                float spec = pow(max(dot(viewDir, reflectDir1), 0.0), 48);
                vec3 specular = spec * vec3(0.8, 0.7, 0.6) * 0.6;
                
                // Fresnel effect (simplified)
                float fresnel = pow(1.0 - max(dot(norm, viewDir), 0.0), 2.5);
                vec3 fresnelColor = vec3(0.25, 0.5, 0.8) * fresnel * 1.5;
                
                // Ambient occlusion
                float ao = 1.0 - (1.0 / (1.0 + Depth * 0.006));
                ao *= (1.0 - smoothstep(0.0, 8.0, WorldPos.y) * 0.25);
                
                // Rim lighting
                float rim = 1.0 - max(dot(norm, viewDir), 0.0);
                rim = pow(rim, 1.2);
                vec3 rimColor = mix(vec3(0.15, 0.5, 0.9), vec3(0.8, 0.2, 0.6), sin(time * 0.8 + WorldPos.y * 0.1)) * rim * glowIntensity;
                
                // Audio glow
                float energyWave = sin(WorldPos.y * 1.5 - time * 2.5 + audioData.x * 8.0) * 0.5 + 0.5;
                vec3 audioGlow = vec3(audioData.x, audioData.y, audioData.z) * Glow * glowIntensity * 1.5;
                audioGlow *= mix(vec3(0.8, 0.2, 0.1), vec3(0.1, 0.4, 0.9), energyWave);
                
                // Color shifting
                vec3 shiftedColor = baseColor;
                float shift = time * 0.4 + colorShift + WorldPos.y * 0.08;
                shiftedColor.r = baseColor.r * (1.0 + sin(shift) * 0.25);
                shiftedColor.g = baseColor.g * (1.0 + sin(shift + 2.094) * 0.25);
                shiftedColor.b = baseColor.b * (1.0 + sin(shift + 4.189) * 0.25);
                
                // Combine lighting
                vec3 result = (shiftedColor * 0.25 + diffuse * 0.55 + specular) * ao;
                result += rimColor + fresnelColor * 0.25;
                result += audioGlow;
                result += windowTex * 0.3;
                
                // Volumetric fog
                float fogFactor = exp(-Depth * 0.025);
                vec3 fogColor = mix(vec3(0.0, 0.0, 0.12), vec3(0.08, 0.0, 0.15), sin(time * 0.25) * 0.5 + 0.5);
                result = mix(fogColor, result, fogFactor);
                
                // Simplified bloom (less expensive)
                float brightness = dot(result, vec3(0.2126, 0.7152, 0.0722));
                if(brightness > 0.7) {
                    vec3 bloom = (result - 0.7) * 2.0 * glowIntensity;
                    result += bloom * mix(vec3(0.8, 0.4, 0.15), vec3(0.15, 0.4, 0.8), sin(time * 0.8));
                }
                
                // Simple tonemapping
                result = result / (result + vec3(0.8));
                result = pow(result, vec3(1.0/2.2));
                
                FragColor = vec4(result, Color.a);
                
                // Reduced scanlines effect
                float scanline = sin(gl_FragCoord.y * 0.5 + time * 3.0) * 0.008;
                FragColor.rgb += scanline;
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
        """Create optimized but still detailed 3D city geometry."""
        vertices = []
        indices = []
        vertex_offset = 0
        
        # Keep multi-layer city but with some optimizations
        for layer in range(self.building_layers):
            layer_scale = 1.0 + layer * 1.4
            layer_offset = layer * 7.0
            
            for x in range(-self.grid_size, self.grid_size):
                for z in range(-self.grid_size, self.grid_size):
                    # Moderate building density (not too sparse)
                    seed_value = abs(hash((x, z, layer))) % (2**32 - 1)
                    np.random.seed(seed_value)
                    
                    if np.random.random() > 0.8:  # 20% chance to skip
                        continue
                    
                    # Building parameters
                    height = np.random.uniform(0.8, self.max_height * (1.0 + layer * 0.25))
                    width = np.random.uniform(0.45, 0.9)
                    depth = np.random.uniform(0.45, 0.9)
                    
                    # Position
                    pos_x = x * 1.4 * layer_scale + np.random.uniform(-0.15, 0.15)
                    pos_z = z * 1.4 * layer_scale - layer_offset + np.random.uniform(-0.15, 0.15)
                    
                    # Colors
                    r = 0.12 + np.random.random() * 0.08
                    g = 0.12 + np.random.random() * 0.08
                    b = 0.16 + np.random.random() * 0.12
                    
                    # Glow factor
                    glow = np.random.random() * 0.25
                    
                    # Create building with moderate detail (2 levels max instead of 3)
                    building_verts, building_indices = self._create_building(
                        pos_x, 0, pos_z, width, height, depth,
                        r, g, b, 1.0, glow, vertex_offset
                    )
                    
                    vertices.extend(building_verts)
                    indices.extend(building_indices)
                    vertex_offset += len(building_verts) // 11
        
        # Convert to numpy arrays
        self.vertex_data = np.array(vertices, dtype=np.float32)
        self.index_data = np.array(indices, dtype=np.uint32)
        self.vertex_count = len(self.index_data)
        
        # Create VAO, VBO, EBO
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertex_data.nbytes, self.vertex_data, GL_STATIC_DRAW)
        
        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_data.nbytes, self.index_data, GL_STATIC_DRAW)
        
        # Setup vertex attributes
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

    def _create_building(self, x, y, z, width, height, depth, r, g, b, a, glow, offset):
        """Create building with moderate detail - balance between performance and quality."""
        vertices = []
        indices = []
        
        # Create 2-level building max (instead of 3+ levels)
        levels = min(2, int(height / 0.6))
        if levels == 0:
            levels = 1
            
        current_width = width
        current_depth = depth
        current_y = 0
        level_height = height / levels
        
        for level in range(levels):
            # Setback for upper levels
            if level > 0:
                current_width *= 0.8
                current_depth *= 0.8
            
            # Texture coordinates for windows
            u_scale = max(2, int(current_width * 8))
            v_scale = max(1, int(level_height * 6))
            
            # Create faces for this level
            faces = [
                # Front face
                {
                    'positions': [
                        [-current_width/2, current_y, current_depth/2],
                        [current_width/2, current_y, current_depth/2],
                        [current_width/2, current_y + level_height, current_depth/2],
                        [-current_width/2, current_y + level_height, current_depth/2],
                    ],
                    'normal': [0, 0, 1],
                    'uvs': [[0, 0], [u_scale, 0], [u_scale, v_scale], [0, v_scale]]
                },
                # Back face
                {
                    'positions': [
                        [current_width/2, current_y, -current_depth/2],
                        [-current_width/2, current_y, -current_depth/2],
                        [-current_width/2, current_y + level_height, -current_depth/2],
                        [current_width/2, current_y + level_height, -current_depth/2],
                    ],
                    'normal': [0, 0, -1],
                    'uvs': [[0, 0], [u_scale, 0], [u_scale, v_scale], [0, v_scale]]
                },
                # Left face
                {
                    'positions': [
                        [-current_width/2, current_y, -current_depth/2],
                        [-current_width/2, current_y, current_depth/2],
                        [-current_width/2, current_y + level_height, current_depth/2],
                        [-current_width/2, current_y + level_height, -current_depth/2],
                    ],
                    'normal': [-1, 0, 0],
                    'uvs': [[0, 0], [int(current_depth * 8), 0], [int(current_depth * 8), v_scale], [0, v_scale]]
                },
                # Right face
                {
                    'positions': [
                        [current_width/2, current_y, current_depth/2],
                        [current_width/2, current_y, -current_depth/2],
                        [current_width/2, current_y + level_height, -current_depth/2],
                        [current_width/2, current_y + level_height, current_depth/2],
                    ],
                    'normal': [1, 0, 0],
                    'uvs': [[0, 0], [int(current_depth * 8), 0], [int(current_depth * 8), v_scale], [0, v_scale]]
                }
            ]
            
            # Add top face for highest level
            if level == levels - 1:
                faces.append({
                    'positions': [
                        [-current_width/2, current_y + level_height, current_depth/2],
                        [current_width/2, current_y + level_height, current_depth/2],
                        [current_width/2, current_y + level_height, -current_depth/2],
                        [-current_width/2, current_y + level_height, -current_depth/2],
                    ],
                    'normal': [0, 1, 0],
                    'uvs': [[0, 0], [1, 0], [1, 1], [0, 1]]
                })
            
            # Generate vertices for all faces
            for face in faces:
                face_start = len(vertices) // 11
                for i in range(4):
                    px, py, pz = face['positions'][i]
                    nx, ny, nz = face['normal']
                    tx, ty = face['uvs'][i]
                    
                    # Slightly darker for upper levels
                    level_factor = 1.0 - level * 0.08
                    vertices.extend([
                        x + px, y + py, z + pz,
                        nx, ny, nz,
                        tx, ty,
                        r * level_factor, g * level_factor, b * level_factor, a,
                        glow + level * 0.05
                    ])
                
                # Face indices
                indices.extend([
                    offset + face_start, offset + face_start + 1, offset + face_start + 2,
                    offset + face_start + 2, offset + face_start + 3, offset + face_start
                ])
            
            current_y += level_height
        
        return vertices, indices

    def paintGL(self):
        """Render the scene."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if not self.shader_program or self.vao is None:
            return
        
        # Update timing
        current_time = time.time()
        self.delta_time = current_time - self.last_time
        self.last_time = current_time
        self.time += self.delta_time * self.camera_speed
        
        # Get audio data
        if hasattr(self, "analyzer") and self.analyzer and self.analyzer.is_active():
            fft = self.analyzer.get_fft_data().astype(np.float32)
            # Moderate interpolation
            target_fft = np.interp(np.linspace(0, len(fft)-1, 24), 
                                  np.arange(len(fft)), fft)
            self.smooth_fft = self.smooth_fft * 0.75 + target_fft * 0.25
            
            # Calculate frequency bands
            self.bass_energy = np.mean(self.smooth_fft[:6]) / 100.0 * self.audio_response
            self.mid_energy = np.mean(self.smooth_fft[6:16]) / 100.0 * self.audio_response
            self.high_energy = np.mean(self.smooth_fft[16:]) / 100.0 * self.audio_response
        else:
            # Demo mode
            self.bass_energy = (math.sin(self.time * 0.5) * 0.5 + 0.5) * self.audio_response
            self.mid_energy = (math.sin(self.time * 0.7) * 0.5 + 0.5) * self.audio_response
            self.high_energy = (math.sin(self.time * 1.1) * 0.5 + 0.5) * self.audio_response
        
        # Get viewport dimensions
        viewport = glGetIntegerv(GL_VIEWPORT)
        width = viewport[2]
        height = viewport[3]
        
        # Setup matrices
        aspect = width / height if height > 0 else 1.0
        projection = self._perspective_matrix(58.0, aspect, 0.1, 85.0)
        
        # Camera movement
        self.camera_rotation += self.rotation_speed * self.delta_time
        cam_radius = 10.0 + math.sin(self.time * 0.15) * 2.0
        cam_x = math.sin(self.camera_rotation) * cam_radius
        cam_z = math.cos(self.camera_rotation) * cam_radius
        cam_y = 4.0 + math.sin(self.time * 0.25) * 1.0 + self.bass_energy * 1.5
        
        view = self._look_at_matrix(
            [cam_x, cam_y, cam_z],
            [0, 1, 0],
            [0, 1, 0]
        )
        
        model = np.identity(4, dtype=np.float32)
        
        # Use shader
        glUseProgram(self.shader_program)
        
        # Set uniforms
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 
                          1, GL_FALSE, projection)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 
                          1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 
                          1, GL_FALSE, model)
        
        glUniform1f(glGetUniformLocation(self.shader_program, "time"), self.time)
        glUniform1f(glGetUniformLocation(self.shader_program, "warp"), self.perspective_warp)
        glUniform1f(glGetUniformLocation(self.shader_program, "glowIntensity"), self.glow_intensity)
        glUniform1f(glGetUniformLocation(self.shader_program, "colorShift"), self.color_shift)
        
        glUniform3f(glGetUniformLocation(self.shader_program, "viewPos"), 
                   cam_x, cam_y, cam_z)
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
        """Get control parameters."""
        return {
            "Grid Size": {
                "type": "slider",
                "min": 5,
                "max": 18,
                "value": self.grid_size,
            },
            "Camera Speed": {
                "type": "slider",
                "min": 0.1,
                "max": 3.0,
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
                "max": 2.0,
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
                "max": 3.0,
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
        }

    def update_control(self, name, value):
        """Update control values."""
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