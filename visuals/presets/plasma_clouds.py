# visuals/presets/plasma_clouds.py
import logging
import numpy as np
import time
import math
from OpenGL.GL import *
from ..base_visualizer import BaseVisualizer
from ..render_backend import GLBackend

class PlasmaCloudsVisualizer(BaseVisualizer):
    """High-quality plasma clouds visualizer with fluid motion and color morphing"""
    
    visual_name = "Plasma Clouds"
    
    def __init__(self):
        super().__init__()
        self.initialized = False
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.start_time = None
        
        # Visual parameters
        self.intensity = 1.0
        self.speed = 1.0
        self.scale = 1.0
        self.complexity = 0.7
        self.color_shift = 0.0
        self.contrast = 1.0
        self.flow_direction = 0.0
        self.turbulence = 0.5
        self.glow_intensity = 0.8
        self.edge_softness = 0.3
        
        # Color palette controls
        self.color_palette = 0  # 0=fire, 1=ocean, 2=aurora, 3=neon, 4=cosmic
        self.color_saturation = 1.0
        self.color_brightness = 1.0
        
        # Advanced controls
        self.layers = 3
        self.distortion = 0.4
        self.breathing_rate = 0.1
        self.pulse_sync = False
        
        logging.info("PlasmaCloudsVisualizer created")
    
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
        """Load high-quality plasma shader"""
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
            // These were previously declared as integers, but our GLBackend
            // currently sets all scalar uniforms using glUniform1f.  Using an
            // integer uniform with glUniform1f results in GL_INVALID_OPERATION
            // errors (1282).  To avoid this mismatch the uniforms are stored
            // as floats and explicitly cast to integers where required in the
            // shader code.
            uniform float colorPalette;
            uniform float colorSaturation;
            uniform float colorBrightness;
            uniform float layers;
            uniform float distortion;
            uniform float breathingRate;
            uniform vec2 resolution;
            
            // Noise functions for organic movement
            float hash(vec2 p) {
                return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
            }
            
            float noise(vec2 p) {
                vec2 i = floor(p);
                vec2 f = fract(p);
                f = f * f * (3.0 - 2.0 * f);
                
                float a = hash(i);
                float b = hash(i + vec2(1.0, 0.0));
                float c = hash(i + vec2(0.0, 1.0));
                float d = hash(i + vec2(1.0, 1.0));
                
                return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
            }
            
            float fbm(vec2 p) {
                float value = 0.0;
                float amplitude = 0.5;
                float frequency = 1.0;
                
                for(int i = 0; i < 6; i++) {
                    value += amplitude * noise(p * frequency);
                    amplitude *= 0.5;
                    frequency *= 2.0;
                }
                return value;
            }
            
            // Advanced plasma function with multiple octaves
            float plasma(vec2 uv, float t) {
                vec2 pos = uv * scale;
                
                // Create flowing motion
                float flowT = t * speed * 0.3;
                vec2 flow = vec2(
                    sin(flowT + flowDirection) * 0.5,
                    cos(flowT + flowDirection * 0.7) * 0.5
                );
                pos += flow;
                
                // Multi-layer plasma with different frequencies
                float result = 0.0;
                float layerWeight = 1.0;
                
                // Cast the uniform float to int for loop iteration
                int layerCount = int(layers);
                for(int i = 0; i < layerCount; i++) {
                    float freq = pow(2.0, float(i)) * (1.0 + complexity);
                    float timeOffset = t * speed * (0.5 + float(i) * 0.2);
                    
                    // Create organic movement patterns
                    vec2 offset1 = vec2(
                        sin(timeOffset * 0.8 + float(i)) * turbulence,
                        cos(timeOffset * 1.2 + float(i)) * turbulence
                    );
                    
                    vec2 offset2 = vec2(
                        sin(timeOffset * 1.3 + float(i) * 2.0) * turbulence * 0.5,
                        cos(timeOffset * 0.9 + float(i) * 1.5) * turbulence * 0.5
                    );
                    
                    // Generate plasma wave
                    float wave1 = sin(length(pos + offset1) * freq + timeOffset);
                    float wave2 = cos((pos.x + offset2.x) * freq * 0.8 + timeOffset * 1.1);
                    float wave3 = sin((pos.y + offset2.y) * freq * 1.2 + timeOffset * 0.7);
                    
                    // Add distortion
                    float dist = distortion * sin(timeOffset * 0.5 + float(i));
                    wave1 += dist * fbm(pos * freq * 0.3 + offset1);
                    
                    result += (wave1 + wave2 + wave3) * layerWeight;
                    layerWeight *= 0.6;
                }
                
                // Add breathing effect
                float breathing = 1.0 + sin(t * breathingRate * 6.28) * 0.1;
                result *= breathing;
                
                return result / layers;
            }
            
            // Color palette functions
            vec3 firePalette(float t) {
                t = clamp(t, 0.0, 1.0);
                vec3 a = vec3(0.5, 0.0, 0.0);
                vec3 b = vec3(2.0, 1.0, 0.1);
                vec3 c = vec3(1.0, 1.0, 1.0);
                vec3 d = vec3(0.0, 0.33, 0.67);
                return a + b * cos(6.28 * (c * t + d));
            }
            
            vec3 oceanPalette(float t) {
                t = clamp(t, 0.0, 1.0);
                vec3 a = vec3(0.0, 0.2, 0.5);
                vec3 b = vec3(0.1, 0.5, 1.0);
                vec3 c = vec3(1.0, 1.0, 1.0);
                vec3 d = vec3(0.0, 0.2, 0.5);
                return a + b * cos(6.28 * (c * t + d));
            }
            
            vec3 auroraPalette(float t) {
                t = clamp(t, 0.0, 1.0);
                vec3 a = vec3(0.0, 0.5, 0.2);
                vec3 b = vec3(1.0, 0.5, 1.0);
                vec3 c = vec3(1.0, 1.0, 1.0);
                vec3 d = vec3(0.3, 0.2, 0.2);
                return a + b * cos(6.28 * (c * t + d));
            }
            
            vec3 neonPalette(float t) {
                t = clamp(t, 0.0, 1.0);
                vec3 a = vec3(0.5, 0.0, 0.5);
                vec3 b = vec3(1.0, 1.0, 0.5);
                vec3 c = vec3(1.0, 1.0, 1.0);
                vec3 d = vec3(0.0, 0.33, 0.67);
                return a + b * cos(6.28 * (c * t + d));
            }
            
            vec3 cosmicPalette(float t) {
                t = clamp(t, 0.0, 1.0);
                vec3 a = vec3(0.2, 0.0, 0.3);
                vec3 b = vec3(0.5, 0.3, 1.0);
                vec3 c = vec3(2.0, 1.0, 1.0);
                vec3 d = vec3(0.0, 0.25, 0.25);
                return a + b * cos(6.28 * (c * t + d));
            }
            
            vec3 getPaletteColor(float t, int palette) {
                switch(palette) {
                    case 1: return oceanPalette(t);
                    case 2: return auroraPalette(t);
                    case 3: return neonPalette(t);
                    case 4: return cosmicPalette(t);
                    default: return firePalette(t);
                }
            }
            
            void main() {
                vec2 uv = vTexCoord;
                vec2 centered = (uv - 0.5) * 2.0;
                
                // Aspect ratio correction
                if(resolution.x > resolution.y) {
                    centered.x *= resolution.x / resolution.y;
                } else {
                    centered.y *= resolution.y / resolution.x;
                }
                
                float t = time;
                
                // Generate plasma field
                float plasmaValue = plasma(centered, t);
                
                // Apply contrast and intensity
                plasmaValue = pow(abs(plasmaValue) * intensity, contrast);
                
                // Add color shifting over time
                float colorTime = plasmaValue + colorShift + t * 0.1;
                
                // Get base color from palette (uniform passed as float)
                vec3 color = getPaletteColor(colorTime, int(colorPalette));
                
                // Apply saturation
                float gray = dot(color, vec3(0.299, 0.587, 0.114));
                color = mix(vec3(gray), color, colorSaturation);
                
                // Apply brightness
                color *= colorBrightness;
                
                // Add glow effect
                float glow = 1.0 + glowIntensity * exp(-length(centered) * (2.0 - edgeSoftness));
                color *= glow;
                
                // Edge fadeout for seamless looping
                float edge = 1.0 - smoothstep(0.8, 1.0, length(centered));
                color *= edge;
                
                // Final gamma correction
                color = pow(color, vec3(1.0/2.2));
                
                FragColor = vec4(color, 1.0);
            }
            """
            
            self.shader_program = self.backend.program(
                vertex_shader_source, fragment_shader_source
            )
            
            logging.debug("PlasmaCloudsVisualizer shaders compiled successfully")
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
            
        except Exception as e:
            logging.error(f"Error setting up geometry: {e}")
            return False
    
    def paintGL(self, current_time=0.0, size=None, backend=None):
        """Render the plasma clouds"""
        backend = backend or self.backend or GLBackend()
        
        try:
            if not self.initialized or not self.shader_program or not self.vao:
                backend.clear(0.0, 0.0, 0.0, 1.0)
                return
            
            if self.start_time is None:
                self.start_time = current_time
            
            elapsed_time = current_time - self.start_time
            
            # Clear background
            backend.clear(0.0, 0.0, 0.0, 1.0)
            
            # Set uniforms
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
            # colorPalette and layers are floats in the shader (casted to int
            # where needed), so pass them as float values here.
            backend.uniform(self.shader_program, "colorPalette", float(self.color_palette))
            backend.uniform(self.shader_program, "colorSaturation", self.color_saturation)
            backend.uniform(self.shader_program, "colorBrightness", self.color_brightness)
            backend.uniform(self.shader_program, "layers", float(self.layers))
            backend.uniform(self.shader_program, "distortion", self.distortion)
            backend.uniform(self.shader_program, "breathingRate", self.breathing_rate)
            
            # Set resolution
            if size:
                backend.uniform(self.shader_program, "resolution", [float(size[0]), float(size[1])])
            else:
                backend.uniform(self.shader_program, "resolution", [800.0, 600.0])
            
            # Render fullscreen quad
            self.vao.render(GL_TRIANGLE_STRIP)
            
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
                "max": 200,
                "value": int(self.intensity * 100),
                "default": 100
            },
            "Speed": {
                "type": "slider",
                "min": 0,
                "max": 300,
                "value": int(self.speed * 100),
                "default": 100
            },
            "Scale": {
                "type": "slider",
                "min": 10,
                "max": 500,
                "value": int(self.scale * 100),
                "default": 100
            },
            "Complexity": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.complexity * 100),
                "default": 70
            },
            "Color Shift": {
                "type": "slider",
                "min": 0,
                "max": 628,  # 2*PI*100
                "value": int(self.color_shift * 100),
                "default": 0
            },
            "Contrast": {
                "type": "slider",
                "min": 10,
                "max": 300,
                "value": int(self.contrast * 100),
                "default": 100
            },
            "Flow Direction": {
                "type": "slider",
                "min": 0,
                "max": 628,  # 2*PI*100
                "value": int(self.flow_direction * 100),
                "default": 0
            },
            "Turbulence": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.turbulence * 100),
                "default": 50
            },
            "Glow Intensity": {
                "type": "slider",
                "min": 0,
                "max": 200,
                "value": int(self.glow_intensity * 100),
                "default": 80
            },
            "Edge Softness": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.edge_softness * 100),
                "default": 30
            },
            "Color Palette": {
                "type": "combo",
                "options": ["Fire", "Ocean", "Aurora", "Neon", "Cosmic"],
                "value": self.color_palette,
                "default": 0
            },
            "Color Saturation": {
                "type": "slider",
                "min": 0,
                "max": 200,
                "value": int(self.color_saturation * 100),
                "default": 100
            },
            "Color Brightness": {
                "type": "slider",
                "min": 0,
                "max": 200,
                "value": int(self.color_brightness * 100),
                "default": 100
            },
            "Layers": {
                "type": "slider",
                "min": 1,
                "max": 6,
                "value": self.layers,
                "default": 3
            },
            "Distortion": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.distortion * 100),
                "default": 40
            },
            "Breathing Rate": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": int(self.breathing_rate * 100),
                "default": 10
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
            elif name == "Flow Direction":
                self.flow_direction = value / 100.0
            elif name == "Turbulence":
                self.turbulence = value / 100.0
            elif name == "Glow Intensity":
                self.glow_intensity = value / 100.0
            elif name == "Edge Softness":
                self.edge_softness = value / 100.0
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
                
            logging.debug(f"Updated {name} to {value}")
            
        except Exception as e:
            logging.error(f"Error updating control {name}: {e}")