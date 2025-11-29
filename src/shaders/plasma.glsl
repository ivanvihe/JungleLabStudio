// VERTEX_SHADER
#version 330
in vec2 in_pos;
in vec2 in_uv;
out vec2 uv;

void main() {
    uv = in_uv;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}

// FRAGMENT_SHADER
#version 330
in vec2 uv;
out vec4 fragColor;

uniform float u_time;
uniform float u_complexity;

void main() {
    vec2 p = uv * u_complexity - vec2(u_complexity / 2.0);
    float v = sin(p.x + u_time);
    v += sin((p.y + u_time) / 2.0);
    v += sin((p.x + p.y + u_time) / 2.0);
    p += u_complexity / 2.0 * vec2(sin(u_time / 3.0), cos(u_time / 2.0));
    v += sin(sqrt(p.x * p.x + p.y * p.y + 1.0) + u_time);
    v = v / 2.0;
    vec3 col = vec3(sin(v * 3.14), sin(v * 3.14 + 2.0), sin(v * 3.14 + 4.0));
    fragColor = vec4(col * 0.5 + 0.5, 1.0);
}
