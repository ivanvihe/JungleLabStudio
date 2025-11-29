#version 330
uniform float time;
in vec2 uv;
out vec4 fragColor;

vec3 tv_color_bar(float x) {
    if (x < 1.0/7.0) return vec3(1.0, 1.0, 1.0);
    if (x < 2.0/7.0) return vec3(1.0, 1.0, 0.0);
    if (x < 3.0/7.0) return vec3(0.0, 1.0, 1.0);
    if (x < 4.0/7.0) return vec3(0.0, 1.0, 0.0);
    if (x < 5.0/7.0) return vec3(1.0, 0.0, 1.0);
    if (x < 6.0/7.0) return vec3(1.0, 0.0, 0.0);
    return vec3(0.0, 0.0, 1.0);
}

void main() {
    vec2 p = uv;
    vec3 col = tv_color_bar(p.x);
    // Add grayscale bars at bottom
    if (p.y > 0.75) {
        float g = fract(p.x * 8.0);
        col = mix(vec3(g), vec3(0.1), 0.2);
    }
    // Grid overlay
    float grid = step(0.995, fract(p.x * 32.0)) + step(0.995, fract(p.y * 18.0));
    col = mix(col, vec3(0.0), clamp(grid, 0.0, 1.0) * 0.2);
    // Slight scanline
    col *= 0.95 + 0.05 * sin((p.y + time * 0.2) * 600.0);
    fragColor = vec4(col, 1.0);
}
