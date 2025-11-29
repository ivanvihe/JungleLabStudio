#version 330
uniform sampler2D tex0;
uniform float intensity;
uniform vec2 screen_size;
uniform int vertical;
in vec2 uv;
out vec4 fragColor;

void main() {
    vec2 safe_screen = max(screen_size, vec2(1.0));
    float target_aspect = vertical == 1 ? (9.0 / 16.0) : (16.0 / 9.0);
    float screen_aspect = safe_screen.x / safe_screen.y;
    vec2 region = vec2(1.0);
    if (screen_aspect > target_aspect) {
        region.x = target_aspect / screen_aspect;
    } else {
        region.y = screen_aspect / target_aspect;
    }
    vec2 offset_region = (vec2(1.0) - region) * 0.5;
    vec2 local = (uv - offset_region) / region;
    bool inside = local.x >= 0.0 && local.x <= 1.0 && local.y >= 0.0 && local.y <= 1.0;

    vec3 col;
    if (inside) {
        vec2 uv_scene = local;
        vec2 offset = (uv_scene - 0.5) * intensity * 0.005;
        float r = texture(tex0, uv_scene + offset).r;
        float g = texture(tex0, uv_scene).g;
        float b = texture(tex0, uv_scene - offset).b;
        col = vec3(r, g, b);
    } else {
        float hatch = fract((uv.x + uv.y) * 40.0);
        float line = smoothstep(0.45, 0.5, hatch);
        col = mix(vec3(0.1), vec3(0.04), line);
    }
    fragColor = vec4(col, 1.0);
}
