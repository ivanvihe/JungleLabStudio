#version 330
uniform sampler2D tex0;
uniform float intensity;
uniform float threshold;
uniform vec2 resolution;
in vec2 uv;
out vec4 fragColor;

vec3 blur_dir(vec2 dir) {
    vec3 sum = vec3(0.0);
    float total = 0.0;
    for (int i = -5; i <= 5; i++) {
        float w = exp(-float(i * i) * 0.15);
        sum += texture(tex0, uv + dir * float(i)).rgb * w;
        total += w;
    }
    return sum / total;
}

void main() {
    vec3 base = texture(tex0, uv).rgb;
    vec3 hi = max(base - threshold, 0.0);
    float mask = clamp(max(max(hi.r, hi.g), hi.b) * 2.0, 0.0, 1.0);
    vec3 blur_h = blur_dir(vec2(1.0 / resolution.x, 0.0));
    vec3 blur_v = blur_dir(vec2(0.0, 1.0 / resolution.y));
    vec3 glow = ((blur_h + blur_v) * 0.5) * mask;
    vec3 color = base + glow * intensity;
    fragColor = vec4(color, 1.0);
}
