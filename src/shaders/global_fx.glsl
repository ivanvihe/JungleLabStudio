#version 330
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform float time;

// FX Intensities (0.0 to 1.0)
uniform float chromatic_aberration;
uniform float pixelate;
uniform float vhs_strength;
uniform float distortion;
uniform float bloom_intensity;
uniform float heat_strength;

uniform vec2 resolution;

// Noise functions
float hash12(vec2 p) {
    vec3 p3  = fract(vec3(p.xyx) * .1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float res = mix(mix(hash12(i), hash12(i + vec2(1.0, 0.0)), f.x),
                    mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), f.x), f.y);
    return res;
}

void main() {
    vec2 p = uv;

    // 1. Distortion / Heat Warp
    if (distortion > 0.0 || heat_strength > 0.0) {
        float offset = noise(vec2(p.y * 10.0, time * 2.0)) * 2.0 - 1.0;
        p.x += offset * (distortion * 0.05 + heat_strength * 0.02 * sin(p.y * 20.0 + time * 5.0));
    }

    // 2. VHS Jitter / Glitch
    if (vhs_strength > 0.0) {
        float y = p.y * resolution.y;
        float jitter = hash12(vec2(time, floor(y * 0.1))) * 2.0 - 1.0;
        if (abs(jitter) > 0.9) {
            p.x += jitter * vhs_strength * 0.05;
        }
    }

    // 3. Pixelate
    if (pixelate > 0.0) {
        float pixels = 256.0 * (1.0 - pixelate * 0.95);
        p = floor(p * pixels) / pixels;
    }

    // 4. Chromatic Aberration
    vec3 col;
    if (chromatic_aberration > 0.0) {
        float shift = chromatic_aberration * 0.02;
        float r = texture(tex0, p + vec2(shift, 0.0)).r;
        float g = texture(tex0, p).g;
        float b = texture(tex0, p - vec2(shift, 0.0)).b;
        col = vec3(r, g, b);
    } else {
        col = texture(tex0, p).rgb;
    }

    // 5. Scanlines (part of VHS)
    if (vhs_strength > 0.0) {
        float scanline = sin(uv.y * resolution.y * 0.5) * 0.5 + 0.5;
        col *= 1.0 - (vhs_strength * 0.2 * scanline);
    }

    // 6. Simple Bloom (High-pass add) - Cheap fake
    if (bloom_intensity > 0.0) {
        vec3 blur = vec3(0.0);
        float total = 0.0;
        // Very crude blur
        for(float x = -2.0; x <= 2.0; x++) {
            for(float y = -2.0; y <= 2.0; y++) {
                vec2 offset = vec2(x, y) * 0.004 * bloom_intensity;
                blur += texture(tex0, p + offset).rgb;
                total += 1.0;
            }
        }
        blur /= total;
        float lum = dot(blur, vec3(0.2126, 0.7152, 0.0722));
        if (lum > 0.6) {
            col += blur * bloom_intensity * 0.8;
        }
    }

    fragColor = vec4(col, 1.0);
}