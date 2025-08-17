# visuals/presets/plasma_clouds.py
import logging
import numpy as np
import time
import math
from OpenGL.GL import *
from ..base_visualizer import BaseVisualizer
from ..render_backend import GLBackend

class PlasmaCloudsVisualizer(BaseVisualizer):
    """High-quality plasma loop visualizer with fluid wave motion"""
    
    visual_name = "Plasma Loop"
    
    def __init__(self):
        super().__init__()
        self.initialized = False
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.start_time = None
        
        # Visual parameters optimized for plasma loop
        self.intensity = 2.0
        self.speed = 0.8
        self.scale = 3.0
        self.complexity = 0.6
        self.color_shift = 0.0
        self.contrast = 1.8
        self.flow_direction = 0.0
        self.turbulence = 0.4
        self.glow_intensity = 1.5
        self.edge_softness = 0.4
        
        # Color palette controls
        self.color_palette = 1  # Ocean/cyan for the plasma look
        self.color_saturation = 1.4
        self.color_brightness = 1.6
        
        # Advanced controls
        self.layers = 3
        self.distortion = 0.2
        self.breathing_rate = 0.08
        self.pulse_sync = False
        
        # Plasma loop specific parameters
        self.reactor_width = 0.15  # Much narrower for the thin plasma effect
        self.reactor_power = 1.2
        self.core_intensity = 3.0  # Higher for that bright center
        self.energy_flow = 1.5     # Faster energy flow
        
        logging.info("PlasmaCloudsVisualizer (Reactor Mode) created")
    
    def initializeGL(self, backend=None):
        """Initialize OpenGL resources"""
        self.backend = backend or GLBackend()
        try:
            logging.debug("PlasmaCloudsVisualizer.initializeGL called")
            
            if not self.load_shaders():
                logging.error("Failed to load shaders")
                return
            
            if not self.setup_geometry():
                logging.error("Failed to setup geometry")
                return
            
            self.start_time = time.time()
            self.initialized = True
            logging.info("✅ PlasmaCloudsVisualizer initialized successfully")
            
        except Exception as e:
            logging.error(f"Error in PlasmaCloudsVisualizer.initializeGL: {e}")
            import traceback
            traceback.print_exc()
    
    def load_shaders(self):
        """Load high-quality plasma reactor shader"""
        try:
            vertex_shader_source = """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoord;
            
            out vec2 vTexCoord;
            out vec2 vPosition;
            
            void main() {
                gl_Position = vec4(aPos, 0.0, 1.0);
                vTexCoord = aTexCoord;
                vPosition = aPos;
            }
            """
            
            fragment_shader_source = """
            #version 330 core
            in vec2 vTexCoord;
            in vec2 vPosition;
            out vec4 FragColor;
            
            uniform float time;
            uniform float intensity;
            uniform float speed;
            uniform float scale;
            uniform float complexity;
            uniform float colorShift;
            uniform float contrast;
            uniform float flowDirection;
            uniform float turbulence;
            uniform float glowIntensity;
            uniform float edgeSoftness;
            uniform float colorPalette;
            uniform float colorSaturation;
            uniform float colorBrightness;
            uniform float layers;
            uniform float distortion;
            uniform float breathingRate;
            uniform float reactorWidth;
            uniform float reactorPower;
            uniform float coreIntensity;
            uniform float energyFlow;
            uniform vec2 resolution;
            
            // High-quality noise functions
            vec3 hash3(vec2 p) {
                vec3 q = vec3(dot(p, vec2(127.1, 311.7)), 
                             dot(p, vec2(269.5, 183.3)), 
                             dot(p, vec2(419.2, 371.9)));
                return fract(sin(q) * 43758.5453);
            }
            
            float noise(vec2 p) {
                vec2 i = floor(p);
                vec2 f = fract(p);
                vec2 u = f * f * (3.0 - 2.0 * f);
                
                return mix(mix(dot(hash3(i + vec2(0.0, 0.0)).xy, f - vec2(0.0, 0.0)),
                              dot(hash3(i + vec2(1.0, 0.0)).xy, f - vec2(1.0, 0.0)), u.x),
                          mix(dot(hash3(i + vec2(0.0, 1.0)).xy, f - vec2(0.0, 1.0)),
                              dot(hash3(i + vec2(1.0, 1.0)).xy, f - vec2(1.0, 1.0)), u.x), u.y);
            }
            
            // Fractional Brownian Motion with higher octaves for detail
            float fbm(vec2 p, int octaves) {
                float value = 0.0;
                float amplitude = 0.5;
                float frequency = 1.0;
                
                for(int i = 0; i < octaves; i++) {
                    value += amplitude * noise(p * frequency);
                    amplitude *= 0.52;
                    frequency *= 1.98;
                }
                return value;
            }
            
            // Plasma loop/wave function - centered and flowing
            float plasmaLoop(vec2 uv, float t) {
                // Center the coordinates
                vec2 pos = (uv - 0.5) * 2.0;
                
                // Aspect ratio correction
                if(resolution.x > resolution.y) {
                    pos.x *= resolution.x / resolution.y;
                } else {
                    pos.y *= resolution.y / resolution.x;
                }
                
                // Create flowing wave motion
                float flowSpeed = t * energyFlow * speed;
                
                // Create the main wave shape using sine functions
                float wavePhase = pos.x * scale * 0.5 + flowSpeed;
                float baseWave = sin(wavePhase) * 0.3;
                
                // Add secondary harmonics for complexity
                baseWave += sin(wavePhase * 2.1 + flowSpeed * 1.3) * 0.15;
                baseWave += sin(wavePhase * 3.7 + flowSpeed * 0.7) * 0.08;
                
                // Create the vertical profile (how thick the plasma is)
                float centerY = baseWave; // Wave oscillates around center
                float distFromWave = abs(pos.y - centerY);
                
                // Create smooth falloff from the wave center
                float waveWidth = reactorWidth * 0.5;
                float waveMask = 1.0 - smoothstep(0.0, waveWidth, distFromWave);
                waveMask = pow(waveMask, 1.5); // Make edges sharper
                
                // Multi-layer plasma generation
                float plasma = 0.0;
                float layerWeight = 1.0;
                
                int layerCount = int(layers);
                for(int i = 0; i < layerCount; i++) {
                    float freq = pow(1.8, float(i)) * scale * 0.3;
                    float timeOffset = flowSpeed * (1.0 + float(i) * 0.4);
                    
                    // Create flowing plasma patterns
                    vec2 flowOffset = vec2(
                        timeOffset * 1.2,
                        sin(timeOffset * 0.8 + float(i)) * turbulence * 0.2
                    );
                    
                    // Generate plasma noise along the wave
                    float plasmaPos = (pos.x + flowOffset.x) * freq;
                    float wave1 = sin(plasmaPos + timeOffset);
                    float wave2 = sin(plasmaPos * 1.6 + timeOffset * 1.1) * 0.7;
                    float noise1 = fbm(vec2(plasmaPos * 0.2, pos.y * freq * 2.0) + flowOffset, 3) * 0.5;
                    
                    // Add vertical flow variation
                    float verticalVar = sin((pos.y - centerY) * freq * 4.0 + timeOffset * 2.0) * 0.3;
                    
                    // Combine all elements
                    float layerPlasma = (wave1 + wave2 + noise1 + verticalVar) * 0.25;
                    plasma += layerPlasma * layerWeight;
                    layerWeight *= 0.7;
                }
                
                // Apply wave mask
                plasma *= waveMask;
                
                // Add core intensity along the wave center
                float coreGlow = exp(-distFromWave * (8.0 / waveWidth)) * coreIntensity * 0.3;
                plasma += coreGlow;
                
                // Add flowing energy pulses
                float pulsePhase = flowSpeed * 2.0;
                float pulse = sin(pulsePhase) * sin(pulsePhase * 0.7) * 0.2 + 0.8;
                plasma *= pulse * reactorPower;
                
                // Breathing effect
                float breathing = 1.0 + sin(t * breathingRate * 6.28) * 0.15;
                plasma *= breathing;
                
                return plasma;
            }
            
            // Enhanced color palettes for reactor effects
            vec3 frostPalette(float t) {
                t = clamp(t, 0.0, 1.0);
                vec3 cold = vec3(0.4, 0.7, 1.0);
                vec3 ice = vec3(0.8, 0.95, 1.0);
                vec3 white = vec3(1.0, 1.0, 1.0);
                if(t < 0.5) return mix(cold, ice, t * 2.0);
                return mix(ice, white, (t - 0.5) * 2.0);
            }
            
            vec3 oceanPalette(float t) {
                t = clamp(t, 0.0, 1.0);
                return vec3(0.1, 0.3, 0.8) + vec3(0.5, 0.7, 0.2) * cos(6.28 * (vec3(1.0) * t + vec3(0.0, 0.33, 0.67)));
            }
            
            vec3 auroraPalette(float t) {
                t = clamp(t, 0.0, 1.0);
                return vec3(0.2, 0.8, 0.3) + vec3(0.8, 0.2, 0.7) * cos(6.28 * (vec3(1.0) * t + vec3(0.3, 0.2, 0.2)));
            }
            
            vec3 neonPalette(float t) {
                t = clamp(t, 0.0, 1.0);
                vec3 base = vec3(1.0, 0.2, 0.8);
                vec3 bright = vec3(0.2, 1.0, 1.0);
                vec3 white = vec3(1.0, 1.0, 1.0);
                if(t < 0.3) return mix(base, bright, t / 0.3);
                if(t < 0.7) return mix(bright, white, (t - 0.3) / 0.4);
                return white;
            }
            
            vec3 cosmicPalette(float t) {
                t = clamp(t, 0.0, 1.0);
                return vec3(0.3, 0.1, 0.8) + vec3(0.7, 0.5, 0.2) * cos(6.28 * (vec3(2.0, 1.0, 1.0) * t + vec3(0.0, 0.25, 0.25)));
            }
            
            // Reactor-specific palettes
            vec3 fusionPalette(float t) {
                t = clamp(t, 0.0, 1.0);
                vec3 core = vec3(1.0, 0.9, 0.4);      // Hot core
                vec3 plasma = vec3(1.0, 0.3, 0.1);    // Hot plasma
                vec3 energy = vec3(0.2, 0.8, 1.0);    // Energy field
                if(t < 0.4) return mix(core, plasma, t / 0.4);
                return mix(plasma, energy, (t - 0.4) / 0.6);
            }
            
            vec3 getPaletteColor(float t, int palette) {
                switch(palette) {
                    case 1: return oceanPalette(t);
                    case 2: return auroraPalette(t);
                    case 3: return neonPalette(t);
                    case 4: return cosmicPalette(t);
                    case 5: return fusionPalette(t);
                    default: return frostPalette(t);
                }
            }
            
            void main() {
                vec2 uv = vTexCoord;
                
                float t = time;
                
                // Generate flowing plasma loop
                float plasmaValue = plasmaLoop(uv, t);
                
                // Apply intensity and contrast
                plasmaValue = pow(abs(plasmaValue) * intensity, contrast);
                
                // Color shifting over time
                float colorTime = plasmaValue * 0.8 + colorShift + t * 0.05;
                
                // Get base color from palette
                vec3 color = getPaletteColor(colorTime, int(colorPalette));
                
                // Enhanced saturation for reactor effect
                float gray = dot(color, vec3(0.299, 0.587, 0.114));
                color = mix(vec3(gray), color, colorSaturation);
                
                // Apply brightness
                color *= colorBrightness;
                
                // Professional glow effect - no circular constraint
                float reactorGlow = plasmaValue * glowIntensity;
                color += color * reactorGlow * vec3(1.2, 0.8, 1.0);
                
                // Add additive bloom effect for professional look
                vec3 bloom = color * smoothstep(0.3, 1.0, plasmaValue) * 0.3;
                color += bloom;
                
                // HDR tone mapping for professional quality
                color = color / (color + vec3(1.0));
                
                // Final gamma correction
                color = pow(color, vec3(1.0/2.2));
                
                // Alpha based on plasma intensity (no circular mask)
                float alpha = smoothstep(0.05, 0.3, plasmaValue);
                
                FragColor = vec4(color, alpha);
            }
            """
            
            self.shader_program = self.backend.program(
                vertex_shader_source, fragment_shader_source
            )
            
            logging.debug("PlasmaCloudsVisualizer reactor shaders compiled successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error loading shaders: {e}")
            return False
    
    def setup_geometry(self):
        """Setup fullscreen quad geometry"""
        try:
            # Fullscreen quad vertices (position + texture coordinates)
            vertices = np.array([
                # Position   TexCoord
                -1.0, -1.0,  0.0, 0.0,  # Bottom-left
                 1.0, -1.0,  1.0, 0.0,  # Bottom-right
                -1.0,  1.0,  0.0, 1.0,  # Top-left
                 1.0,  1.0,  1.0, 1.0,  # Top-right
            ], dtype=np.float32)
            
            self.vbo = self.backend.buffer(vertices.tobytes())
            self.vao = self.backend.vertex_array(
                self.shader_program,
                [(self.vbo, '2f 2f', 'aPos', 'aTexCoord')],
            )
            
            logging.debug("PlasmaCloudsVisualizer geometry setup complete")
            return True
            
        except Exception in e:
            logging.error(f"Error setting up geometry: {e}")
            return False
    
    def paintGL(self, current_time=0.0, size=None, backend=None):
        """Render the plasma reactor"""
        backend = backend or self.backend or GLBackend()
        
        try:
            if not self.initialized or not self.shader_program or not self.vao:
                backend.clear(0.0, 0.0, 0.0, 1.0)  # Pure black background
                return
            
            if self.start_time is None:
                self.start_time = current_time
            
            elapsed_time = current_time - self.start_time
            
            # Clear with pure black background
            backend.clear(0.0, 0.0, 0.0, 1.0)
            
            # Enable blending for professional glow effects
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            # Set all uniforms
            backend.uniform(self.shader_program, "time", elapsed_time)
            backend.uniform(self.shader_program, "intensity", self.intensity)
            backend.uniform(self.shader_program, "speed", self.speed)
            backend.uniform(self.shader_program, "scale", self.scale)
            backend.uniform(self.shader_program, "complexity", self.complexity)
            backend.uniform(self.shader_program, "colorShift", self.color_shift)
            backend.uniform(self.shader_program, "contrast", self.contrast)
            backend.uniform(self.shader_program, "flowDirection", self.flow_direction)
            backend.uniform(self.shader_program, "turbulence", self.turbulence)
            backend.uniform(self.shader_program, "glowIntensity", self.glow_intensity)
            backend.uniform(self.shader_program, "edgeSoftness", self.edge_softness)
            backend.uniform(self.shader_program, "colorPalette", float(self.color_palette))
            backend.uniform(self.shader_program, "colorSaturation", self.color_saturation)
            backend.uniform(self.shader_program, "colorBrightness", self.color_brightness)
            backend.uniform(self.shader_program, "layers", float(self.layers))
            backend.uniform(self.shader_program, "distortion", self.distortion)
            backend.uniform(self.shader_program, "breathingRate", self.breathing_rate)
            
            # Reactor-specific uniforms
            backend.uniform(self.shader_program, "reactorWidth", self.reactor_width)
            backend.uniform(self.shader_program, "reactorPower", self.reactor_power)
            backend.uniform(self.shader_program, "coreIntensity", self.core_intensity)
            backend.uniform(self.shader_program, "energyFlow", self.energy_flow)
            
            # Set resolution
            if size:
                backend.uniform(self.shader_program, "resolution", [float(size[0]), float(size[1])])
            else:
                backend.uniform(self.shader_program, "resolution", [800.0, 600.0])
            
            # Render fullscreen quad
            self.vao.render(GL_TRIANGLE_STRIP)
            
            glDisable(GL_BLEND)
            
        except Exception as e:
            if not hasattr(self, '_last_error_time') or \
               time.time() - self._last_error_time > 5:
                logging.error(f"PlasmaClouds paint error: {e}")
                self._last_error_time = time.time()
            
            backend.clear(0.0, 0.0, 0.0, 1.0)
    
    def resizeGL(self, width, height, backend=None):
        """Handle resize"""
        if backend:
            backend.set_viewport(0, 0, width, height)
        else:
            glViewport(0, 0, width, height)
    
    def cleanup(self):
        """Clean up OpenGL resources"""
        try:
            logging.debug("Cleaning up PlasmaCloudsVisualizer")
            
            if self.vao:
                if hasattr(self.vao, "release"):
                    try:
                        self.vao.release()
                    except Exception:
                        pass
                else:
                    try:
                        glDeleteVertexArrays(1, [self.vao.vao])
                    except Exception:
                        pass
                self.vao = None
            
            if self.vbo:
                if hasattr(self.vbo, "release"):
                    try:
                        self.vbo.release()
                    except Exception:
                        pass
                else:
                    try:
                        glDeleteBuffers(1, [self.vbo.buffer_id])
                    except Exception:
                        pass
                self.vbo = None
            
            if self.shader_program:
                if hasattr(self.shader_program, "release"):
                    try:
                        self.shader_program.release()
                    except Exception:
                        pass
                else:
                    try:
                        if glIsProgram(self.shader_program):
                            glDeleteProgram(self.shader_program)
                    except Exception:
                        pass
                self.shader_program = None
            
            self.initialized = False
            logging.debug("PlasmaCloudsVisualizer cleanup complete")
            
        except Exception as e:
            logging.debug(f"Cleanup error (non-critical): {e}")
    
    def get_controls(self):
        """Return available controls"""
        return {
            "Intensity": {
                "type": "slider",
                "min": 0,
                "max": 300,
                "value": int(self.intensity * 100),
                "default": 150
            },
            "Speed": {
                "type": "slider",
                "min": 0,
                "max": 400,
                "value": int(self.speed * 100),
                "default": 120
            },
            "Scale": {
                "type": "slider",
                "min": 50,
                "max": 800,
                "value": int(self.scale * 100),
                "default": 200
            },
            "Complexity": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.complexity * 100),
                "default": 80
            },
            "Color Shift": {
                "type": "slider",
                "min": 0,
                "max": 628,
                "value": int(self.color_shift * 100),
                "default": 0
            },
            "Contrast": {
                "type": "slider",
                "min": 50,
                "max": 400,
                "value": int(self.contrast * 100),
                "default": 140
            },
            "Turbulence": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.turbulence * 100),
                "default": 60
            },
            "Glow Intensity": {
                "type": "slider",
                "min": 0,
                "max": 300,
                "value": int(self.glow_intensity * 100),
                "default": 120
            },
            "Color Palette": {
                "type": "combo",
                "options": ["Frost", "Ocean", "Aurora", "Neon", "Cosmic", "Fusion"],
                "value": self.color_palette,
                "default": 3
            },
            "Color Saturation": {
                "type": "slider",
                "min": 0,
                "max": 300,
                "value": int(self.color_saturation * 100),
                "default": 120
            },
            "Color Brightness": {
                "type": "slider",
                "min": 0,
                "max": 300,
                "value": int(self.color_brightness * 100),
                "default": 130
            },
            "Layers": {
                "type": "slider",
                "min": 2,
                "max": 8,
                "value": self.layers,
                "default": 4
            },
            "Distortion": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.distortion * 100),
                "default": 30
            },
            "Breathing Rate": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.breathing_rate * 100),
                "default": 15
            },
            "Reactor Width": {
                "type": "slider",
                "min": 5,
                "max": 50,
                "value": int(self.reactor_width * 100),
                "default": 15
            },
            "Reactor Power": {
                "type": "slider",
                "min": 0,
                "max": 200,
                "value": int(self.reactor_power * 100),
                "default": 100
            },
            "Core Intensity": {
                "type": "slider",
                "min": 0,
                "max": 500,
                "value": int(self.core_intensity * 100),
                "default": 300
            },
            "Energy Flow": {
                "type": "slider",
                "min": 0,
                "max": 300,
                "value": int(self.energy_flow * 100),
                "default": 100
            }
        }
    
    def update_control(self, name, value):
        """Update a control value"""
        try:
            if name == "Intensity":
                self.intensity = value / 100.0
            elif name == "Speed":
                self.speed = value / 100.0
            elif name == "Scale":
                self.scale = value / 100.0
            elif name == "Complexity":
                self.complexity = value / 100.0
            elif name == "Color Shift":
                self.color_shift = value / 100.0
            elif name == "Contrast":
                self.contrast = value / 100.0
            elif name == "Turbulence":
                self.turbulence = value / 100.0
            elif name == "Glow Intensity":
                self.glow_intensity = value / 100.0
            elif name == "Color Palette":
                self.color_palette = int(value)
            elif name == "Color Saturation":
                self.color_saturation = value / 100.0
            elif name == "Color Brightness":
                self.color_brightness = value / 100.0
            elif name == "Layers":
                self.layers = int(value)
            elif name == "Distortion":
                self.distortion = value / 100.0
            elif name == "Breathing Rate":
                self.breathing_rate = value / 100.0
            elif name == "Reactor Width":
                self.reactor_width = value / 100.0
            elif name == "Reactor Power":
                self.reactor_power = value / 100.0
            elif name == "Core Intensity":
                self.core_intensity = value / 100.0
            elif name == "Energy Flow":
                self.energy_flow = value / 100.0
                
            logging.debug(f"Updated {name} to {value}")
            
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")