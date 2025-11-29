#version 330
uniform float time;
uniform sampler2D audio_tex;
uniform vec2 resolution;
uniform float flux;
uniform int vertical;
in vec2 uv;
out vec4 fragColor;

float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}

float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float map(vec3 p) {
    float t = time * 0.6;
    vec3 q = p;
    q.xy *= mat2(cos(t), -sin(t), sin(t), cos(t));
    q.xz *= mat2(cos(t*0.7), -sin(t*0.7), sin(t*0.7), cos(t*0.7));
    float d1 = sdTorus(q, vec2(0.7 + sin(t)*0.1, 0.15));
    float d2 = sdSphere(p + vec3(sin(t*0.8), cos(t*0.5), sin(t*0.3))*0.4, 0.9);
    return min(d1, d2);
}

vec3 shade(vec3 ro, vec3 rd) {
    float t = 0.0;
    float atten = 1.0;
    vec3 col = vec3(0.0);
    float audio = texture(audio_tex, vec2(0.6,0.0)).r;
    for (int i = 0; i < 120; i++) {
        vec3 pos = ro + rd * t;
        float d = map(pos);
        float glow = exp(-abs(d) * 6.0) * atten;
        vec3 palette = mix(vec3(0.1,0.6,1.0), vec3(1.0,0.2,0.7), audio + flux);
        col += palette * glow * (0.6 + audio);
        atten *= 0.99;
        t += clamp(abs(d), 0.02, 0.15);
        if (t > 6.0) break;
    }
    return col;
}

void main() {
    vec2 p = uv * 2.0 - 1.0;
    float aspect = resolution.x / resolution.y;
    p.x *= aspect;
    if (vertical == 1) p = p.yx;
    vec3 ro = vec3(0.0, 0.0, -3.5);
    vec3 rd = normalize(vec3(p, 1.4));
    vec3 col = shade(ro, rd);
    fragColor = vec4(col, 1.0);
}
