// ============================================================================
// TEST SIMPLE - Shader de prueba super simple
// Solo dibuja un gradiente para verificar que el sistema funciona
// ============================================================================

// VERTEX_SHADER
#version 330
in vec2 in_pos;
in vec2 in_uv;
out vec2 v_uv;

void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}

// FRAGMENT_SHADER
#version 330
in vec2 v_uv;
out vec4 fragColor;

uniform float u_time;

void main() {
    // Simple gradiente de color
    vec3 col = vec3(v_uv.x, v_uv.y, 0.5 + 0.5 * sin(u_time));
    fragColor = vec4(col, 1.0);
}
