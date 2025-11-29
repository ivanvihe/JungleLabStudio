#version 330
uniform float time;
uniform sampler2D audio_tex;
uniform vec2 resolution;
uniform float twist;
uniform int vertical;
out vec4 fragColor;
in vec2 uv;

mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float sdLine(vec2 p, vec2 a, vec2 b, float r){
    vec2 pa = p-a, ba = b-a;
    float h = clamp(dot(pa,ba)/dot(ba,ba), 0.0, 1.0);
    return length(pa - ba*h) - r;
}

void main() {
    vec2 p = uv * 2.0 - 1.0;
    if (vertical == 1) p = p.yx;
    p *= rot(sin(time * 0.2) * 0.4);
    float audio = texture(audio_tex, vec2(0.4, 0.0)).r;
    float scene = 0.0;
    for (int i = 0; i < 6; i++) {
        float t = float(i) * 0.6 + time * (0.8 + audio * 0.6);
        vec2 a = vec2(sin(t), cos(t * 0.7 + twist));
        vec2 b = vec2(cos(t * 0.8 + 1.2), sin(t + twist));
        float d = sdLine(p, a * 0.6, b * 0.8, 0.04 + audio * 0.08);
        scene += smoothstep(0.15, 0.0, d);
    }
    vec3 base = vec3(0.05, 0.0, 0.08);
    vec3 col = mix(base, vec3(0.2,0.8,1.0), scene);
    col += vec3(0.9, 0.2, 0.6) * scene * audio * 1.5;
    fragColor = vec4(col, 1.0);
}
