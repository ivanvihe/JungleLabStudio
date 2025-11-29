"""
ShadertoyNode - 100% compatible Shadertoy shader node for JungleLabStudio

This node allows running shaders from Shadertoy.com without modifications.
Automatically converts mainImage() function and provides all Shadertoy uniforms.
"""

import moderngl
import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from core.graph.node import GeneratorNode
from core.graph.registry import NodeRegistry
from core.error_handling import get_error_handler, ErrorCategory, ErrorSeverity
from shadertoy.converter import ShadertoyConverter


@NodeRegistry.register("shadertoy")
class ShadertoyNode(GeneratorNode):
    """
    Generator node that runs Shadertoy shaders

    Supports all Shadertoy uniforms:
    - iResolution (vec3): viewport resolution (x, y, aspect ratio)
    - iTime (float): shader playback time in seconds
    - iTimeDelta (float): render time delta in seconds
    - iFrame (int): shader playback frame counter
    - iMouse (vec4): mouse pixel coords (xy: current, zw: click)
    - iChannel0-3 (sampler2D): input textures/buffers
    - iChannelTime[4] (float): channel playback time
    - iChannelResolution[4] (vec3): channel resolution
    - iDate (vec4): date and time (year, month, day, seconds)
    - iSampleRate (float): audio sample rate

    Usage in YAML:
        - id: my_shadertoy
          type: shadertoy
          params:
            shadertoy_code: |
              void mainImage(out vec4 fragColor, in vec2 fragCoord) {
                  vec2 uv = fragCoord / iResolution.xy;
                  fragColor = vec4(uv, 0.5 + 0.5 * sin(iTime), 1.0);
              }
    """

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        self.error_handler = get_error_handler()

        # Shadertoy-specific state
        self.frame_count = 0
        self.last_time = 0.0
        self.delta_time = 0.0

        # Mouse state (iMouse uniform)
        self.mouse_pos = [0.0, 0.0]       # Current mouse position (xy)
        self.mouse_click = [0.0, 0.0]     # Last click position (zw)
        self.mouse_down = False

        # Channel inputs (iChannel0-3)
        # These can be textures from other nodes or loaded from files
        self.channels = [None, None, None, None]

        # Shader code and compilation
        self.shadertoy_code = ""
        self.shader_program: Optional[moderngl.Program] = None
        self.vao: Optional[moderngl.VertexArray] = None
        self.shader_uniforms: set = set()

        # Converter instance
        self.converter = ShadertoyConverter()

        # Track if we've shown first render debug info
        self._first_render = False

    def set_shadertoy_code(self, code: str):
        """
        Set Shadertoy shader code and compile it

        Args:
            code: Raw Shadertoy shader code with mainImage() function
        """
        self.shadertoy_code = code
        self._convert_and_compile()

    def _convert_and_compile(self):
        """Convert Shadertoy code and compile shader"""
        if not self.shadertoy_code:
            self.error_handler.log(
                f"ShadertoyNode {self.id}: No shader code provided",
                ErrorSeverity.WARNING,
                ErrorCategory.SHADER
            )
            return

        # Validate shader
        validation = self.converter.validate_shader(self.shadertoy_code)
        if not validation['valid']:
            for error in validation['errors']:
                self.error_handler.log(
                    f"ShadertoyNode {self.id}: {error}",
                    ErrorSeverity.ERROR,
                    ErrorCategory.SHADER
                )
            return

        # Show warnings
        for warning in validation['warnings']:
            self.error_handler.log(
                f"ShadertoyNode {self.id}: {warning}",
                ErrorSeverity.WARNING,
                ErrorCategory.SHADER
            )

        # Convert to GLSL
        try:
            glsl_code = self.converter.convert(self.shadertoy_code)
        except Exception as e:
            self.error_handler.log(
                f"ShadertoyNode {self.id}: Conversion failed: {e}",
                ErrorSeverity.ERROR,
                ErrorCategory.SHADER
            )
            return

        # Compile shader
        self._compile_shader(glsl_code)

    def _compile_shader(self, glsl_code: str):
        """Compile GLSL shader code"""
        # Extract vertex and fragment sections
        vertex_src = self._extract_section(glsl_code, "VERTEX_SHADER")
        fragment_src = self._extract_section(glsl_code, "FRAGMENT_SHADER")

        if not vertex_src or not fragment_src:
            self.error_handler.log(
                f"ShadertoyNode {self.id}: Failed to extract shader sections",
                ErrorSeverity.ERROR,
                ErrorCategory.SHADER
            )
            return

        # Compile
        try:
            self.shader_program = self.ctx.program(
                vertex_shader=vertex_src,
                fragment_shader=fragment_src
            )
            self.error_handler.log(
                f"ShadertoyNode {self.id}: Shader compiled successfully",
                ErrorSeverity.INFO,
                ErrorCategory.SHADER
            )
        except Exception as e:
            self.error_handler.handle_shader_error(
                shader_name=f"ShadertoyNode {self.id}",
                error_msg=str(e),
                source_code=fragment_src
            )
            return

        # Setup VAO
        self._setup_vao()
        self._detect_uniforms()

    def _extract_section(self, source: str, section_name: str) -> str:
        """Extract shader section from source code"""
        lines = source.split('\n')
        in_section = False
        result = []

        for line in lines:
            stripped = line.strip()

            if f'#ifdef {section_name}' in stripped:
                in_section = True
                continue
            elif stripped.startswith('#endif') and in_section:
                in_section = False
                continue

            if in_section:
                result.append(line)

        return '\n'.join(result)

    def _setup_vao(self):
        """Create vertex array object for fullscreen quad"""
        if not self.shader_program:
            return

        # Try different input attribute combinations
        input_combos = [
            ('in_pos', 'in_uv'),
            ('in_position', 'in_texcoord'),
        ]

        for pos_name, uv_name in input_combos:
            try:
                self.vao = self.ctx.vertex_array(
                    self.shader_program,
                    [(self.quad_vbo, '2f 2f', pos_name, uv_name)]
                )
                return
            except Exception:
                continue

        self.error_handler.log(
            f"ShadertoyNode {self.id}: Failed to create VAO",
            ErrorSeverity.ERROR,
            ErrorCategory.SHADER
        )

    def _detect_uniforms(self):
        """Detect which uniforms exist in the shader"""
        if not self.shader_program:
            return

        self.shader_uniforms = set(self.shader_program._members.keys())

        # Log detected dependencies
        deps = self.converter.detect_dependencies(self.shadertoy_code)
        self.error_handler.log(
            f"ShadertoyNode {self.id}: Dependencies: {deps}",
            ErrorSeverity.DEBUG,
            ErrorCategory.SHADER
        )

    def update_mouse(self, x: float, y: float, button_down: bool):
        """
        Update mouse state for iMouse uniform

        Args:
            x: Mouse x position in pixels
            y: Mouse y position in pixels
            button_down: Whether mouse button is pressed
        """
        self.mouse_pos = [x, y]

        # Update click position when button is first pressed
        if button_down and not self.mouse_down:
            self.mouse_click = [x, y]

        self.mouse_down = button_down

    def set_channel(self, channel_index: int, texture: moderngl.Texture):
        """
        Set input texture for iChannel uniform

        Args:
            channel_index: Channel index (0-3)
            texture: ModernGL texture to use as input
        """
        if 0 <= channel_index < 4:
            self.channels[channel_index] = texture
        else:
            self.error_handler.log(
                f"ShadertoyNode {self.id}: Invalid channel index {channel_index}",
                ErrorSeverity.WARNING,
                ErrorCategory.SHADER
            )

    def render(self):
        """Render shader with all Shadertoy uniforms"""
        if not self.shader_program or not self.vao:
            # Shader not loaded, clear FBO
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)
            return

        # Debug first render
        if not self._first_render:
            self.error_handler.log(
                f"ShadertoyNode {self.id}: First render - resolution: {self.resolution}",
                ErrorSeverity.DEBUG,
                ErrorCategory.SHADER
            )
            self._first_render = True

        # Calculate delta time
        self.delta_time = self.time - self.last_time
        self.last_time = self.time

        # Use this node's FBO
        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)

        # Set Shadertoy uniforms
        self._set_shadertoy_uniforms()

        # Render fullscreen quad
        self.vao.render(moderngl.TRIANGLE_STRIP)

        # Increment frame counter
        self.frame_count += 1

    def _set_shadertoy_uniforms(self):
        """Set all Shadertoy uniforms"""
        # iResolution (vec3): viewport resolution (x, y, aspect_ratio)
        aspect_ratio = self.resolution[0] / max(self.resolution[1], 1)
        self._set_uniform('iResolution', (
            float(self.resolution[0]),
            float(self.resolution[1]),
            aspect_ratio
        ))

        # iTime (float): shader playback time
        self._set_uniform('iTime', self.time)

        # iTimeDelta (float): render delta time
        self._set_uniform('iTimeDelta', self.delta_time)

        # iFrame (int): frame counter
        self._set_uniform('iFrame', self.frame_count)

        # iMouse (vec4): mouse coords (xy: current, zw: click)
        mouse_uniform = (*self.mouse_pos, *self.mouse_click)
        self._set_uniform('iMouse', mouse_uniform)

        # iDate (vec4): date and time info
        now = datetime.datetime.now()
        time_in_seconds = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1000000.0
        date_uniform = (float(now.year), float(now.month), float(now.day), time_in_seconds)
        self._set_uniform('iDate', date_uniform)

        # iSampleRate (float): audio sample rate
        self._set_uniform('iSampleRate', 44100.0)

        # Bind channel textures (iChannel0-3)
        for i, channel in enumerate(self.channels):
            if channel:
                channel.use(location=i)
                self._set_uniform(f'iChannel{i}', i)

                # iChannelResolution[i] (vec3)
                if hasattr(channel, 'size'):
                    ch_aspect = channel.size[0] / max(channel.size[1], 1)
                    ch_res = (float(channel.size[0]), float(channel.size[1]), ch_aspect)
                    self._set_uniform(f'iChannelResolution[{i}]', ch_res)

                # iChannelTime[i] (float) - for video inputs (TODO)
                self._set_uniform(f'iChannelTime[{i}]', 0.0)

    def _set_uniform(self, name: str, value: Any):
        """Set uniform if it exists in shader"""
        if name in self.shader_uniforms:
            try:
                self.shader_program[name].value = value
            except Exception as e:
                # Silently ignore uniform errors (type mismatches, etc.)
                pass
