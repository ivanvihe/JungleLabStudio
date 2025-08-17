import logging
import numpy as np
import ctypes
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import time
import math

from ..base_visualizer import BaseVisualizer


class BuildingMadnessVisualizer(BaseVisualizer):
    """Audio reactive infinite city visualizer - Inception/Interstellar style."""

    visual_name = "Building Madness"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.ebo = None
        self.time = 0.0
        self.grid_size = 15
        self.building_layers = 3
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
        self.smooth_fft = np.zeros(32)
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
        """Compile and link advanced shaders."""
        try:
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
                // Apply audio-reactive transformation
                vec3 pos = aPos;
                float audioInfluence = audioData.x * 0.3 + audioData.y * 0.2;
                
                // Vertical wave based on position and time
                pos.y += sin(pos.x * 2.0 + time * 2.0) * 0.1 * audioInfluence;
                pos.y += cos(pos.z * 2.0 + time * 1.5) * 0.1 * audioInfluence;
                
                // Tesseract-like warping
                float dist = length(pos.xz);
                float warpFactor = 1.0 + warp * sin(dist * 0.5 - time) * 0.2;
                pos.xz *= warpFactor;
                
                // Space-time distortion (Interstellar effect)
                float bend = sin(time * 0.5 + dist * 0.3) * warp * 0.3;
                mat2 rotation = mat2(cos(bend), -sin(bend), sin(bend), cos(bend));
                pos.xz = rotation * pos.xz;
                
                vec4 worldPosition = model * vec4(pos, 1.0);
                vec4 viewPosition = view * worldPosition;
                gl_Position = projection * viewPosition;
                
                FragPos = vec3(worldPosition);
                WorldPos = pos;
                Normal = mat3(transpose(inverse(model))) * aNormal;
                TexCoord = aTexCoord;
                Color = aColor;
                Glow = aGlow + audioData.z * 0.5;
                Depth = -viewPosition.z;
            }
            """

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
            
            // Procedural texture generation
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
                return mix(a, b, u.x) + (c - a)* u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
            }
            
            vec3 getWindowColor(vec2 uv, float glow) {
                // More realistic window grid
                vec2 grid = fract(uv);
                
                // Window frame thickness
                float frameThickness = 0.08;
                float window = 1.0;
                window *= step(frameThickness, grid.x) * step(grid.x, 1.0 - frameThickness);
                window *= step(frameThickness, grid.y) * step(grid.y, 1.0 - frameThickness);
                
                // Floor separation (horizontal lines every few windows)
                float floorLine = step(0.95, fract(uv.y * 0.25));
                window *= 1.0 - floorLine;
                
                // Random window lighting with more variation
                vec2 windowId = floor(uv);
                float lightOn = random(windowId) > 0.4 ? 1.0 : 0.0;
                
                // Animated flickering for some windows
                if(random(windowId * 0.5) > 0.8) {
                    lightOn *= (sin(time * 5.0 + random(windowId) * 20.0) * 0.5 + 0.5);
                }
                
                // React to audio
                lightOn = clamp(lightOn + audioData.x * 0.3, 0.0, 1.0);
                
                // Window colors - warm interior light
                vec3 windowColor = vec3(1.0, 0.9, 0.7) * lightOn * window * 0.8;
                
                // Some windows with colored lights (offices, signs)
                float colorType = random(windowId * 2.0);
                if(colorType > 0.9) {
                    windowColor = vec3(0.0, 0.8, 1.0) * lightOn * window; // Cyan
                } else if(colorType > 0.85) {
                    windowColor = vec3(1.0, 0.2, 0.5) * lightOn * window; // Magenta
                } else if(colorType > 0.8) {
                    windowColor = vec3(0.2, 1.0, 0.2) * lightOn * window; // Green
                }
                
                // Add reflections on glass
                float reflection = (1.0 - window) * 0.3;
                windowColor += vec3(0.1, 0.15, 0.2) * reflection;
                
                // Glow from windows
                windowColor += vec3(0.1, 0.3, 0.6) * glow * 2.0 * audioData.y;
                
                // Building frame/structure
                vec3 frameColor = vec3(0.15, 0.15, 0.18) * (1.0 - window);
                
                return windowColor + frameColor;
            }
            
            void main() {
                vec3 norm = normalize(Normal);
                vec3 viewDir = normalize(viewPos - FragPos);
                
                // Base color with procedural texture
                vec3 baseColor = Color.rgb * 0.5;
                float noiseVal = noise(TexCoord * 30.0 + vec2(time * 0.1, WorldPos.y * 0.1));
                baseColor = mix(baseColor, baseColor * 1.5, noiseVal * 0.4);
                
                // Enhanced window texture
                vec3 windowTex = getWindowColor(TexCoord, Glow);
                baseColor = mix(baseColor, windowTex, 0.85);
                
                // Multiple light sources for complex lighting
                vec3 lightPos1 = vec3(sin(time) * 15.0, 10.0, cos(time) * 15.0);
                vec3 lightPos2 = vec3(cos(time * 0.7) * 10.0, 5.0, sin(time * 0.7) * 10.0);
                
                vec3 lightDir1 = normalize(lightPos1 - FragPos);
                vec3 lightDir2 = normalize(lightPos2 - FragPos);
                
                float diff1 = max(dot(norm, lightDir1), 0.0);
                float diff2 = max(dot(norm, lightDir2), 0.0);
                
                vec3 diffuse = diff1 * vec3(1.0, 0.8, 0.6) + diff2 * vec3(0.6, 0.8, 1.0) * 0.5;
                
                // Enhanced specular with metallic feel
                vec3 reflectDir1 = reflect(-lightDir1, norm);
                float spec = pow(max(dot(viewDir, reflectDir1), 0.0), 64);
                vec3 specular = spec * vec3(1.0, 0.9, 0.8) * 0.8;
                
                // Fresnel effect for glass-like surfaces
                float fresnel = pow(1.0 - max(dot(norm, viewDir), 0.0), 3.0);
                vec3 fresnelColor = vec3(0.3, 0.6, 1.0) * fresnel * 2.0;
                
                // Ambient occlusion with height gradient
                float ao = 1.0 - (1.0 / (1.0 + Depth * 0.008));
                ao *= (1.0 - smoothstep(0.0, 10.0, WorldPos.y) * 0.3);
                
                // Enhanced rim lighting
                float rim = 1.0 - max(dot(norm, viewDir), 0.0);
                rim = pow(rim, 1.5);
                vec3 rimColor = mix(vec3(0.2, 0.6, 1.0), vec3(1.0, 0.3, 0.8), sin(time + WorldPos.y)) * rim * glowIntensity * 1.5;
                
                // Audio-reactive energy waves
                float energyWave = sin(WorldPos.y * 2.0 - time * 3.0 + audioData.x * 10.0) * 0.5 + 0.5;
                vec3 audioGlow = vec3(audioData.x, audioData.y, audioData.z) * Glow * glowIntensity * 2.0;
                audioGlow *= mix(vec3(1.0, 0.3, 0.1), vec3(0.1, 0.5, 1.0), energyWave);
                
                // Holographic color shifting
                vec3 shiftedColor = baseColor;
                float shift = time * 0.5 + colorShift + WorldPos.y * 0.1;
                shiftedColor.r = baseColor.r * (1.0 + sin(shift) * 0.3);
                shiftedColor.g = baseColor.g * (1.0 + sin(shift + 2.094) * 0.3);
                shiftedColor.b = baseColor.b * (1.0 + sin(shift + 4.189) * 0.3);
                
                // Combine all lighting with HDR tonemapping
                vec3 result = (shiftedColor * 0.2 + diffuse * 0.5 + specular) * ao;
                result += rimColor + fresnelColor * 0.3;
                result += audioGlow;
                result += windowTex * 0.5; // Extra window glow
                
                // Volumetric fog with color
                float fogFactor = exp(-Depth * 0.03);
                vec3 fogColor = mix(vec3(0.0, 0.0, 0.15), vec3(0.1, 0.0, 0.2), sin(time * 0.3) * 0.5 + 0.5);
                result = mix(fogColor, result, fogFactor);
                
                // Enhanced bloom effect
                float brightness = dot(result, vec3(0.2126, 0.7152, 0.0722));
                if(brightness > 0.6) {
                    vec3 bloom = (result - 0.6) * 3.0 * glowIntensity;
                    result += bloom * mix(vec3(1.0, 0.5, 0.2), vec3(0.2, 0.5, 1.0), sin(time));
                }
                
                // HDR tonemapping
                result = result / (result + vec3(1.0));
                result = pow(result, vec3(1.0/2.2)); // Gamma correction
                
                FragColor = vec4(result, Color.a);
                
                // Subtle scanlines and grain
                float scanline = sin(gl_FragCoord.y * 0.7 + time * 5.0) * 0.01;
                float grain = (random(gl_FragCoord.xy * 0.01 + time) - 0.5) * 0.02;
                FragColor.rgb += scanline + grain;
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
        """Create complex 3D city geometry."""
        vertices = []
        indices = []
        vertex_offset = 0
        
        # Generate city grid with multiple layers and better distribution
        for layer in range(self.building_layers):
            layer_scale = 1.0 + layer * 1.5
            layer_offset = layer * 8.0
            
            for x in range(-self.grid_size, self.grid_size):
                for z in range(-self.grid_size, self.grid_size):
                    # Skip some positions for variety
                    seed_value = abs(hash((x, z, layer))) % (2**32 - 1)
                    np.random.seed(seed_value)
                    
                    if np.random.random() > 0.85:  # 15% chance to skip
                        continue
                    
                    # More varied building parameters
                    height = np.random.uniform(0.8, self.max_height * (1.0 + layer * 0.3))
                    width = np.random.uniform(0.4, 1.0)
                    depth = np.random.uniform(0.4, 1.0)
                    
                    # Position with layer offset and some randomness
                    pos_x = x * 1.5 * layer_scale + np.random.uniform(-0.2, 0.2)
                    pos_z = z * 1.5 * layer_scale - layer_offset + np.random.uniform(-0.2, 0.2)
                    
                    # Color variation - more muted, realistic colors
                    r = 0.15 + np.random.random() * 0.1
                    g = 0.15 + np.random.random() * 0.1
                    b = 0.18 + np.random.random() * 0.15
                    
                    # Glow factor
                    glow = np.random.random() * 0.3
                    
                    # Create building with detailed geometry
                    building_verts, building_indices = self._create_building(
                        pos_x, 0, pos_z, width, height, depth,
                        r, g, b, 1.0, glow, vertex_offset
                    )
                    
                    vertices.extend(building_verts)
                    indices.extend(building_indices)
                    vertex_offset += len(building_verts) // 11  # 11 floats per vertex
        
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
        # Position
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        # Normal
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(1)
        # TexCoord
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(2)
        # Color
        glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(3)
        # Glow
        glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(10 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(4)
        
        glBindVertexArray(0)

    def _create_building(self, x, y, z, width, height, depth, r, g, b, a, glow, offset):
        """Create vertices and indices for a detailed building."""
        vertices = []
        indices = []
        
        # Create multi-level building with setbacks
        levels = min(3, int(height / 0.5))
        current_width = width
        current_depth = depth
        current_y = 0
        level_height = height / levels
        
        # Building base detail
        base_height = min(0.2, height * 0.1)
        
        # Define positions for each level with proper UV mapping
        for level in range(levels):
            # Reduce size for upper levels (setback effect)
            if level > 0:
                current_width *= 0.85
                current_depth *= 0.85
            
            # Calculate texture coordinates based on building dimensions
            # This creates a proper window grid pattern
            u_scale = max(3, int(current_width * 10))  # Number of windows horizontally
            v_scale = max(2, int(level_height * 8))    # Number of window rows
            
            # Front face
            positions = [
                [-current_width/2, current_y, current_depth/2],
                [current_width/2, current_y, current_depth/2],
                [current_width/2, current_y + level_height, current_depth/2],
                [-current_width/2, current_y + level_height, current_depth/2],
            ]
            normals = [[0, 0, 1]] * 4
            texcoords = [[0, 0], [u_scale, 0], [u_scale, v_scale], [0, v_scale]]
            
            # Add vertices for front face
            face_start = len(vertices) // 11
            for i in range(4):
                px, py, pz = positions[i]
                nx, ny, nz = normals[i]
                tx, ty = texcoords[i]
                vertices.extend([
                    x + px, y + py, z + pz,
                    nx, ny, nz,
                    tx, ty,
                    r * (1.0 - level * 0.1), g * (1.0 - level * 0.1), b * (1.0 - level * 0.1), a,
                    glow + level * 0.1
                ])
            
            # Front face indices
            indices.extend([
                offset + face_start, offset + face_start + 1, offset + face_start + 2,
                offset + face_start + 2, offset + face_start + 3, offset + face_start
            ])
            
            # Back face
            positions = [
                [current_width/2, current_y, -current_depth/2],
                [-current_width/2, current_y, -current_depth/2],
                [-current_width/2, current_y + level_height, -current_depth/2],
                [current_width/2, current_y + level_height, -current_depth/2],
            ]
            normals = [[0, 0, -1]] * 4
            texcoords = [[0, 0], [u_scale, 0], [u_scale, v_scale], [0, v_scale]]
            
            face_start = len(vertices) // 11
            for i in range(4):
                px, py, pz = positions[i]
                nx, ny, nz = normals[i]
                tx, ty = texcoords[i]
                vertices.extend([
                    x + px, y + py, z + pz,
                    nx, ny, nz,
                    tx, ty,
                    r * (1.0 - level * 0.1), g * (1.0 - level * 0.1), b * (1.0 - level * 0.1), a,
                    glow + level * 0.1
                ])
            
            indices.extend([
                offset + face_start, offset + face_start + 1, offset + face_start + 2,
                offset + face_start + 2, offset + face_start + 3, offset + face_start
            ])
            
            # Left face
            positions = [
                [-current_width/2, current_y, -current_depth/2],
                [-current_width/2, current_y, current_depth/2],
                [-current_width/2, current_y + level_height, current_depth/2],
                [-current_width/2, current_y + level_height, -current_depth/2],
            ]
            normals = [[-1, 0, 0]] * 4
            u_scale_side = max(3, int(current_depth * 10))
            texcoords = [[0, 0], [u_scale_side, 0], [u_scale_side, v_scale], [0, v_scale]]
            
            face_start = len(vertices) // 11
            for i in range(4):
                px, py, pz = positions[i]
                nx, ny, nz = normals[i]
                tx, ty = texcoords[i]
                vertices.extend([
                    x + px, y + py, z + pz,
                    nx, ny, nz,
                    tx, ty,
                    r * (1.0 - level * 0.1), g * (1.0 - level * 0.1), b * (1.0 - level * 0.1), a,
                    glow + level * 0.1
                ])
            
            indices.extend([
                offset + face_start, offset + face_start + 1, offset + face_start + 2,
                offset + face_start + 2, offset + face_start + 3, offset + face_start
            ])
            
            # Right face
            positions = [
                [current_width/2, current_y, current_depth/2],
                [current_width/2, current_y, -current_depth/2],
                [current_width/2, current_y + level_height, -current_depth/2],
                [current_width/2, current_y + level_height, current_depth/2],
            ]
            normals = [[1, 0, 0]] * 4
            texcoords = [[0, 0], [u_scale_side, 0], [u_scale_side, v_scale], [0, v_scale]]
            
            face_start = len(vertices) // 11
            for i in range(4):
                px, py, pz = positions[i]
                nx, ny, nz = normals[i]
                tx, ty = texcoords[i]
                vertices.extend([
                    x + px, y + py, z + pz,
                    nx, ny, nz,
                    tx, ty,
                    r * (1.0 - level * 0.1), g * (1.0 - level * 0.1), b * (1.0 - level * 0.1), a,
                    glow + level * 0.1
                ])
            
            indices.extend([
                offset + face_start, offset + face_start + 1, offset + face_start + 2,
                offset + face_start + 2, offset + face_start + 3, offset + face_start
            ])
            
            # Top face (roof)
            if level == levels - 1:
                positions = [
                    [-current_width/2, current_y + level_height, current_depth/2],
                    [current_width/2, current_y + level_height, current_depth/2],
                    [current_width/2, current_y + level_height, -current_depth/2],
                    [-current_width/2, current_y + level_height, -current_depth/2],
                ]
                normals = [[0, 1, 0]] * 4
                texcoords = [[0, 0], [1, 0], [1, 1], [0, 1]]
                
                face_start = len(vertices) // 11
                for i in range(4):
                    px, py, pz = positions[i]
                    nx, ny, nz = normals[i]
                    tx, ty = texcoords[i]
                    vertices.extend([
                        x + px, y + py, z + pz,
                        nx, ny, nz,
                        tx, ty,
                        r * 0.3, g * 0.3, b * 0.3, a,  # Darker roof
                        glow * 0.5
                    ])
                
                indices.extend([
                    offset + face_start, offset + face_start + 1, offset + face_start + 2,
                    offset + face_start + 2, offset + face_start + 3, offset + face_start
                ])
            
            current_y += level_height
        
        return vertices, indices  # IMPORTANT: Return the vertices and indices!
        
        # Create vertex data
        for i in range(24):
            px, py, pz = positions[i]
            nx, ny, nz = normals[i]
            tx, ty = texcoords[i]
            vertices.extend([
                x + px, y + py, z + pz,  # Position
                nx, ny, nz,              # Normal
                tx, ty,                  # TexCoord
                r, g, b, a,              # Color
                glow                     # Glow
            ])
        
        # Create indices for the cube faces
        face_indices = [
            0, 1, 2, 2, 3, 0,      # Front
            4, 5, 6, 6, 7, 4,      # Back
            8, 9, 10, 10, 11, 8,   # Left
            12, 13, 14, 14, 15, 12, # Right
            16, 17, 18, 18, 19, 16, # Top
            20, 21, 22, 22, 23, 20  # Bottom
        ]
        
        # Offset indices
        for idx in face_indices:
            indices.append(offset + idx)
        
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
            # Smooth the FFT data
            target_fft = np.interp(np.linspace(0, len(fft)-1, 32), 
                                  np.arange(len(fft)), fft)
            self.smooth_fft = self.smooth_fft * 0.7 + target_fft * 0.3
            
            # Calculate frequency bands
            self.bass_energy = np.mean(self.smooth_fft[:8]) / 100.0 * self.audio_response
            self.mid_energy = np.mean(self.smooth_fft[8:20]) / 100.0 * self.audio_response
            self.high_energy = np.mean(self.smooth_fft[20:]) / 100.0 * self.audio_response
        else:
            # Demo mode with synthetic audio
            self.bass_energy = (math.sin(self.time * 0.5) * 0.5 + 0.5) * self.audio_response
            self.mid_energy = (math.sin(self.time * 0.7) * 0.5 + 0.5) * self.audio_response
            self.high_energy = (math.sin(self.time * 1.1) * 0.5 + 0.5) * self.audio_response
        
        # Get viewport dimensions
        viewport = glGetIntegerv(GL_VIEWPORT)
        width = viewport[2]
        height = viewport[3]
        
        # Setup matrices
        aspect = width / height if height > 0 else 1.0
        projection = self._perspective_matrix(60.0, aspect, 0.1, 100.0)
        
        # Animate camera with better path
        self.camera_rotation += self.rotation_speed * self.delta_time
        cam_radius = 8.0 + math.sin(self.time * 0.2) * 3.0
        cam_x = math.sin(self.camera_rotation) * cam_radius
        cam_z = math.cos(self.camera_rotation) * cam_radius
        cam_y = 3.0 + math.sin(self.time * 0.3) * 1.5 + self.bass_energy * 2.0
        
        view = self._look_at_matrix(
            [cam_x, cam_y, cam_z],     # Eye position
            [0, 1, 0],                  # Look at center of city
            [0, 1, 0]                   # Up vector
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
                "max": 25,
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