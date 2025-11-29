// FBM Terrain Shader
// Fractal Brownian Motion terrain generation

#ifdef VERTEX_SHADER
in vec2 in_pos;
in vec2 in_uv;
varying vec2 v_uv;

void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
#endif

#ifdef FRAGMENT_SHADER
varying vec2 v_uv;
out vec4 fragColor;

uniform float u_time;
uniform vec2 u_resolution;
uniform float u_scale;
uniform float u_height;
uniform float u_octaves;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);

    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float value = 0.0;
    float amplitude = 0.5;
    float frequency = 1.0;

    int octaves = int(u_octaves);
    for (int i = 0; i < octaves; i++) {
        value += amplitude * noise(p * frequency);
        frequency *= 2.0;
        amplitude *= 0.5;
    }

    return value;
}

void main() {
    vec2 uv = v_uv;

    // Animated terrain
    vec2 p = uv * u_scale;
    p.x += u_time * 0.1;

    float height = fbm(p) * u_height;

    // Create terrain visualization
    float terrainLine = abs(uv.y - (0.5 + height - 0.5));
    float terrain = smoothstep(0.02, 0.0, terrainLine);

    // Color based on height
    vec3 lowColor = vec3(0.1, 0.2, 0.3);
    vec3 midColor = vec3(0.3, 0.5, 0.4);
    vec3 highColor = vec3(0.8, 0.9, 0.95);

    vec3 color = mix(lowColor, midColor, smoothstep(0.3, 0.5, height));
    color = mix(color, highColor, smoothstep(0.6, 0.8, height));

    // Apply terrain mask
    color *= terrain;

    // Add gradient for filled terrain
    if (uv.y < (0.5 + height - 0.5)) {
        color += vec3(0.1, 0.15, 0.2) * (1.0 - uv.y);
    }

    fragColor = vec4(color, max(terrain, step(uv.y, 0.5 + height - 0.5) * 0.5));
}
#endif
