#version 330
uniform sampler2D tex0;
uniform float time;
uniform float strength;
uniform float pixel_sort;
in vec2 uv;
out vec4 fragColor;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void main() {
    vec2 coord = uv;
    float block = floor(coord.y * 24.0);
    float glitch = step(0.5, hash(vec2(block, floor(time * 2.0))));
    float offset = (hash(vec2(block, block + 7.0)) - 0.5) * 0.08 * strength;
    if (glitch > 0.0) {
        coord.x += offset;
    }
    // Pixel-sort stripe on glitch rows
    if (pixel_sort > 0.0) {
        float stripe = step(0.92, fract(coord.y * 24.0 + time * 0.7));
        if (stripe > 0.0) {
            coord.x = mix(coord.x, 1.0 - coord.x, clamp(strength * pixel_sort, 0.0, 1.0));
        }
    }
    vec3 col = texture(tex0, coord).rgb;
    // Chromatic split
    col.r = texture(tex0, coord + vec2(offset * 0.4, 0.0)).r;
    col.b = texture(tex0, coord - vec2(offset * 0.4, 0.0)).b;
    fragColor = vec4(col, 1.0);
}
