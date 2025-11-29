#version 330
in vec2 uv;
out vec4 fragColor;

uniform float time;
uniform vec2 resolution;
uniform float warp;
uniform float flash;
uniform vec3 color_a;
uniform vec3 color_b;

// SDF and Noise
mat2 rot(float a) {
    float s = sin(a), c = cos(a);
    return mat2(c, -s, s, c);
}

float hash(float n) { return fract(sin(n) * 43758.5453); }
float noise(vec3 x) {
    vec3 p = floor(x);
    vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    float n = p.x + p.y * 57.0 + p.z * 113.0;
    return mix(mix(mix(hash(n + 0.0), hash(n + 1.0), f.x),
                   mix(hash(n + 57.0), hash(n + 58.0), f.x), f.y),
               mix(mix(hash(n + 113.0), hash(n + 114.0), f.x),
                   mix(hash(n + 170.0), hash(n + 171.0), f.x), f.y), f.z);
}

float fbm(vec3 p) {
    float f = 0.0;
    f += 0.5000 * noise(p); p *= 2.01;
    f += 0.2500 * noise(p); p *= 2.02;
    f += 0.1250 * noise(p); p *= 2.03;
    f += 0.0625 * noise(p);
    return f;
}

float map(vec3 p) {
    vec3 q = p - vec3(0.0, 0.0, time * 0.5);
    float f = fbm(q * 0.5 + warp * sin(q.z * 0.5));
    return 1.0 - f - length(p.xy) * 0.2;
}

void main() {
    vec2 p = (uv - 0.5) * vec2(resolution.x / resolution.y, 1.0);
    vec3 ro = vec3(0.0, 0.0, 2.0);
    vec3 rd = normalize(vec3(p, -1.5));
    
    float t = 0.0;
    vec3 col = vec3(0.0);
    float den = 0.0;
    
    for(int i = 0; i < 64; i++) {
        vec3 pos = ro + rd * t;
        float d = map(pos);
        if(d > 0.0) {
            float ld = 0.05 * d;
            den += ld;
            // Color gradient
            vec3 c = mix(color_a, color_b, sin(pos.z * 0.1 + time) * 0.5 + 0.5);
            col += c * ld * exp(-0.1 * t);
        }
        t += max(0.05, 0.02 * t);
        if(den > 1.0) break;
    }
    
    col += flash * vec3(1.0, 0.9, 0.8) * exp(-length(p) * 2.0);
    fragColor = vec4(col, 1.0);
}
