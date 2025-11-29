"""
ShaderNode - Generic GLSL Shader Generator
Loads and executes custom GLSL fragment shaders as generator nodes.
"""

import moderngl
from pathlib import Path
from typing import Dict, Any
from core.graph.node import GeneratorNode
from core.graph.registry import NodeRegistry
from core.error_handling import get_error_handler, ErrorCategory, ErrorSeverity


@NodeRegistry.register("shader")
class ShaderNode(GeneratorNode):
    """
    Generic shader generator node.
    Loads GLSL shaders with #ifdef VERTEX_SHADER / FRAGMENT_SHADER sections.
    Automatically exposes shader uniforms as parameters.

    Usage in DSL:
        - id: my_shader
          type: shader
          params:
            shader_path: src/shaders/generators/my_shader.glsl
            frequency: 2.0
            color_a: [0.0, 1.0, 1.0]
            # ... any other uniforms in the shader
    """

    # Shader cache to avoid recompilation
    _shader_cache: Dict[str, moderngl.Program] = {}

    DEFAULT_VERTEX_SHADER = """
#version 330
in vec2 in_pos;
in vec2 in_uv;
out vec2 uv;
void main() {
    uv = in_uv;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

    def __init__(self, ctx: moderngl.Context, node_id: str, resolution: tuple[int, int]):
        super().__init__(ctx, node_id, resolution)

        self.shader_path: str = ""
        self.shader_program: moderngl.Program | None = None
        self.vao: moderngl.VertexArray | None = None

        # Track which uniforms exist in shader
        self.shader_uniforms: set = set()

    def set_shader_path(self, path: str):
        """Set shader path and load shader"""
        self.shader_path = path
        self._load_shader()

    def _load_shader(self):
        """Load and compile GLSL shader from file"""
        error_handler = get_error_handler()

        if not self.shader_path:
            error_handler.log(
                f"ShaderNode {self.id}: No shader_path set",
                ErrorSeverity.WARNING,
                ErrorCategory.SHADER
            )
            return

        path = Path(self.shader_path)
        if not path.exists():
            error_handler.log(
                f"ShaderNode {self.id}: Shader file not found: {self.shader_path}",
                ErrorSeverity.ERROR,
                ErrorCategory.SHADER
            )
            return

        # Check cache
        cache_key = str(path.absolute())
        if cache_key in ShaderNode._shader_cache:
            self.shader_program = ShaderNode._shader_cache[cache_key]
            self._setup_vao()
            self._detect_uniforms()
            error_handler.log(
                f"ShaderNode {self.id}: Loaded from cache",
                ErrorSeverity.DEBUG,
                ErrorCategory.SHADER
            )
            return

        # Load source
        try:
            source = path.read_text()
        except Exception as e:
            error_handler.handle_file_io_error(path, "read", e)
            return

        # Extract vertex and fragment sections
        vertex_src = self._extract_section(source, "VERTEX_SHADER")
        fragment_src = self._extract_section(source, "FRAGMENT_SHADER")

        # Fallback logic for fragment-only shaders
        if not vertex_src:
            vertex_src = self.DEFAULT_VERTEX_SHADER

        if not fragment_src:
            # If no specific sections found, assume whole file is fragment shader
            if "VERTEX_SHADER" not in source and "FRAGMENT_SHADER" not in source:
                fragment_src = source
            else:
                error_handler.log(
                    f"ShaderNode {self.id}: Missing FRAGMENT_SHADER section but VERTEX_SHADER tag found",
                    ErrorSeverity.ERROR,
                    ErrorCategory.SHADER
                )
                return

        # Compile shader
        try:
            self.shader_program = self.ctx.program(
                vertex_shader=vertex_src,
                fragment_shader=fragment_src
            )
            # Cache it
            ShaderNode._shader_cache[cache_key] = self.shader_program
            error_handler.log(
                f"ShaderNode {self.id}: Shader compiled successfully",
                ErrorSeverity.INFO,
                ErrorCategory.SHADER
            )

        except Exception as e:
            # Use specialized shader error handler
            error_handler.handle_shader_error(
                shader_name=f"{self.id} ({path.name})",
                error_msg=str(e),
                source_code=fragment_src
            )
            return

        self._setup_vao()
        self._detect_uniforms()
        error_handler.log(
            f"ShaderNode {self.id}: VAO created, {len(self.shader_uniforms)} uniforms detected",
            ErrorSeverity.DEBUG,
            ErrorCategory.SHADER
        )

    def _extract_section(self, source: str, section_name: str) -> str:
        """
        Extract shader section from source.
        Supports two formats:
        1. #ifdef SECTION_NAME ... #endif
        2. // SECTION_NAME ... (until next // SECTION or end)
        """
        lines = source.split('\n')
        in_section = False
        result = []

        # Try #ifdef format first
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

        # If found via #ifdef, return it
        if result:
            return '\n'.join(result)

        # Try comment-based format: // SECTION_NAME
        in_section = False
        result = []
        for line in lines:
            stripped = line.strip()

            # Check for section marker
            if stripped.startswith('//') and section_name in stripped:
                in_section = True
                continue

            # Stop at next section or end
            if in_section and stripped.startswith('//') and ('VERTEX_SHADER' in stripped or 'FRAGMENT_SHADER' in stripped):
                break

            if in_section:
                result.append(line)

        return '\n'.join(result)

    def _setup_vao(self):
        """Create vertex array object for fullscreen quad"""
        if not self.shader_program:
            return

        # Try different input attribute name combinations
        input_combos = [
            ('in_position', 'in_texcoord'),  # Original format
            ('in_pos', 'in_uv'),             # Alternative format
        ]

        for pos_name, uv_name in input_combos:
            try:
                self.vao = self.ctx.vertex_array(
                    self.shader_program,
                    [(self.quad_vbo, '2f 2f', pos_name, uv_name)]
                )
                return  # Success!
            except Exception:
                continue  # Try next combo

        print(f"ShaderNode {self.id}: Failed to create VAO with any input attribute combination")

    def _detect_uniforms(self):
        """Detect which uniforms exist in the shader"""
        if not self.shader_program:
            return

        self.shader_uniforms = set(self.shader_program._members.keys())

    def render(self):
        """Render shader to FBO"""
        if not self.shader_program or not self.vao:
            # Shader not loaded, clear FBO
            if not hasattr(self, '_warned_no_shader'):
                print(f"ShaderNode {self.id}: WARNING - Cannot render, no shader/VAO loaded")
                print(f"  shader_program: {self.shader_program}")
                print(f"  vao: {self.vao}")
                print(f"  shader_path: {self.shader_path}")
                self._warned_no_shader = True
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)
            return

        # Debug first render
        if not hasattr(self, '_first_render'):
            print(f"ShaderNode {self.id}: First render, params: {list(self.params.keys())}")
            print(f"  FBO size: {self.fbo.size}, Texture size: {self.texture.size}")
            print(f"  Time: {self.time}")
            self._first_render = True

        # Use this node's FBO
        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)

        # Set standard uniforms
        self._set_uniform('u_time', self.time)
        self._set_uniform('u_resolution', self.resolution)

        # Set parameter uniforms
        for param_name, param in self.params.items():
            uniform_name = f'u_{param_name}'
            value = param.value

            if isinstance(value, list):
                # Vector parameter
                if len(value) == 2:
                    self._set_uniform(uniform_name, tuple(value))
                elif len(value) == 3:
                    self._set_uniform(uniform_name, tuple(value))
                elif len(value) == 4:
                    self._set_uniform(uniform_name, tuple(value))
            elif isinstance(value, (int, float)):
                # Scalar parameter
                # Handle int uniforms (like octaves)
                if 'octaves' in param_name or 'iterations' in param_name or 'steps' in param_name:
                    self._set_uniform(uniform_name, int(value))
                else:
                    self._set_uniform(uniform_name, float(value))

        # Render fullscreen quad
        self.vao.render(moderngl.TRIANGLE_STRIP)

    def _set_uniform(self, name: str, value: Any):
        """Set uniform if it exists in shader"""
        if name in self.shader_uniforms:
            try:
                self.shader_program[name].value = value
            except Exception as e:
                # Silently ignore uniform errors (common with type mismatches)
                pass


# Alternative: EffectNode for shaders that process inputs
# (Similar implementation but inherits from EffectNode and binds input textures)
