#version 330
uniform float time;
uniform vec2 resolution;
uniform float gain;
uniform sampler2D audio_tex;
uniform int vertical;
out vec4 fragColor;
in vec2 uv;

float noise(vec3 p) {
    return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
}

float fbm(vec3 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 5; i++) {
        v += a * noise(p);
        p *= 2.3;
        a *= 0.5;
    }
    return v;
}

vec3 palette(float t) {
    vec3 a = vec3(0.2, 0.0, 0.4);
    vec3 b = vec3(0.0, 0.4, 0.8);
    vec3 c = vec3(1.0, 0.2, 0.8);
    vec3 d = vec3(0.0, 0.1, 0.2);
    return a + b * cos(6.28318 * (c * t + d));
}

void main() {
    vec2 frag = uv * 2.0 - 1.0;
    float aspect = resolution.x / resolution.y;
    frag.x *= aspect;
    if (vertical == 1) {
        frag = vec2(frag.x * 0.7, frag.y * 1.3);
    }
    vec3 ro = vec3(0.0, 0.0, -5.0);
    vec3 rd = normalize(vec3(frag, 1.4));

    float t = 0.0;
    vec3 col = vec3(0.0);
    float accum = 0.0;
    float audio = texture(audio_tex, vec2(0.1, 0.0)).r * gain;
    for (int i = 0; i < 80; i++) {
        vec3 pos = ro + rd * t;
        float d = fbm(pos * 0.9 + time * 0.2);
        float dens = smoothstep(0.5, 0.9, d + audio * 0.4);
        vec3 c = palette(d + time * 0.05);
        col += (1.0 - accum) * dens * c * 0.08;
        accum += dens * 0.05;
        if (accum > 0.95) break;
        t += 0.06;
    }
    fragColor = vec4(col, 1.0);
}
