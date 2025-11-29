// ============================================================================
// VOLUMETRIC CURL NOISE 3D GENERATOR
// Creates organic, flowing volumetric structures
// Perfect for wire clouds, nebula-like formations, terrain evolution
// ============================================================================

#version 330

#ifdef VERTEX_SHADER
in vec2 in_position;
in vec2 in_texcoord;
varying vec2 v_uv;

void main() {
    v_uv = in_texcoord;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
#endif

#ifdef FRAGMENT_SHADER
varying vec2 v_uv;
out vec4 fragColor;

// Uniforms - exposed as parameters in the DSL
uniform float u_time;           // Time for animation
uniform vec2 u_resolution;      // Screen resolution
uniform float u_frequency;      // Noise frequency/scale (default: 2.0)
uniform float u_amplitude;      // Noise amplitude (default: 1.0)
uniform int u_octaves;          // FBM octaves for detail (default: 6)
uniform float u_lacunarity;     // Frequency multiplier per octave (default: 2.0)
uniform float u_persistence;    // Amplitude multiplier per octave (default: 0.5)
uniform float u_warp;           // Domain warping amount (default: 0.3)
uniform float u_speed;          // Animation speed (default: 0.3)
uniform float u_depth;          // Z-depth range for 3D effect (default: 2.0)
uniform vec3 u_color_a;         // Color A (dark) (default: vec3(0.0, 0.1, 0.2))
uniform vec3 u_color_b;         // Color B (bright) (default: vec3(0.0, 1.0, 1.0))
uniform float u_glow;           // Glow intensity (default: 0.8)
uniform float u_density;        // Density/threshold (default: 0.5)

// Include noise library
// Note: In production, use #include or concatenate these files
// For this example, I'll inline simplified versions

// Hash functions
float hash13(vec3 p3) {
    p3  = fract(p3 * 0.1031);
    p3 += dot(p3, p3.zyx + 31.32);
    return fract((p3.x + p3.y) * p3.z);
}

vec3 hash33(vec3 p3) {
    p3 = fract(p3 * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yxz + 33.33);
    return fract((p3.xxy + p3.yxx) * p3.zyx);
}

// 3D Perlin Noise
float perlin3D(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    vec3 u = f * f * (3.0 - 2.0 * f);

    float n000 = dot(hash33(i + vec3(0.0, 0.0, 0.0)) * 2.0 - 1.0, f - vec3(0.0, 0.0, 0.0));
    float n100 = dot(hash33(i + vec3(1.0, 0.0, 0.0)) * 2.0 - 1.0, f - vec3(1.0, 0.0, 0.0));
    float n010 = dot(hash33(i + vec3(0.0, 1.0, 0.0)) * 2.0 - 1.0, f - vec3(0.0, 1.0, 0.0));
    float n110 = dot(hash33(i + vec3(1.0, 1.0, 0.0)) * 2.0 - 1.0, f - vec3(1.0, 1.0, 0.0));
    float n001 = dot(hash33(i + vec3(0.0, 0.0, 1.0)) * 2.0 - 1.0, f - vec3(0.0, 0.0, 1.0));
    float n101 = dot(hash33(i + vec3(1.0, 0.0, 1.0)) * 2.0 - 1.0, f - vec3(1.0, 0.0, 1.0));
    float n011 = dot(hash33(i + vec3(0.0, 1.0, 1.0)) * 2.0 - 1.0, f - vec3(0.0, 1.0, 1.0));
    float n111 = dot(hash33(i + vec3(1.0, 1.0, 1.0)) * 2.0 - 1.0, f - vec3(1.0, 1.0, 1.0));

    return mix(
        mix(mix(n000, n100, u.x), mix(n010, n110, u.x), u.y),
        mix(mix(n001, n101, u.x), mix(n011, n111, u.x), u.y),
        u.z);
}

// FBM (Fractal Brownian Motion)
float fbm3D(vec3 p, int octaves, float lacunarity, float persistence) {
    float value = 0.0;
    float amplitude = 0.5;
    float frequency = 1.0;

    for (int i = 0; i < octaves; i++) {
        value += amplitude * perlin3D(p * frequency);
        frequency *= lacunarity;
        amplitude *= persistence;
        if (i >= octaves - 1) break; // Prevent over-iteration
    }

    return value;
}

// 3D Curl Noise (divergence-free vector field)
vec3 curlNoise3D(vec3 p) {
    float eps = 0.01;

    // Sample noise at offset positions to calculate curl
    float n1 = perlin3D(p + vec3(0.0, eps, 0.0));
    float n2 = perlin3D(p - vec3(0.0, eps, 0.0));
    float n3 = perlin3D(p + vec3(0.0, 0.0, eps));
    float n4 = perlin3D(p - vec3(0.0, 0.0, eps));
    float n5 = perlin3D(p + vec3(eps, 0.0, 0.0));
    float n6 = perlin3D(p - vec3(eps, 0.0, 0.0));

    float x = (n1 - n2) - (n3 - n4);
    float y = (n3 - n4) - (n5 - n6);
    float z = (n5 - n6) - (n1 - n2);

    return vec3(x, y, z) / (2.0 * eps);
}

// Domain Warping
float warpedNoise3D(vec3 p, float warp) {
    vec3 q = vec3(
        perlin3D(p),
        perlin3D(p + vec3(5.2, 1.3, 4.1)),
        perlin3D(p + vec3(2.7, 6.9, 3.5))
    );

    vec3 r = vec3(
        perlin3D(p + warp * q + vec3(1.7, 9.2, 6.3)),
        perlin3D(p + warp * q + vec3(8.3, 2.8, 1.1)),
        perlin3D(p + warp * q + vec3(4.5, 7.6, 9.4))
    );

    return perlin3D(p + warp * r);
}

void main() {
    // Normalized coordinates with aspect correction
    vec2 uv = v_uv;
    vec2 p = (uv - 0.5) * 2.0;
    p.x *= u_resolution.x / u_resolution.y;

    // Animate time
    float t = u_time * u_speed;

    // Create 3D position by adding depth (Z coordinate)
    // Z varies across screen for perspective effect
    float z = t + length(p) * u_depth;
    vec3 pos = vec3(p * u_frequency, z);

    // Apply curl noise for flowing, organic motion
    vec3 curl = curlNoise3D(pos);

    // Build volumetric density using FBM with domain warping
    float noise = warpedNoise3D(pos + curl * 0.5, u_warp);
    noise = fbm3D(pos + curl * 0.3, u_octaves, u_lacunarity, u_persistence);

    // Normalize and apply amplitude
    noise = noise * u_amplitude * 0.5 + 0.5;

    // Apply density threshold for structure
    float density = smoothstep(u_density - 0.1, u_density + 0.1, noise);

    // Map density to color gradient
    vec3 color = mix(u_color_a, u_color_b, density);

    // Add glow effect (highlights bright areas)
    color += color * density * u_glow;

    // Add subtle edge glow for depth
    float edge = 1.0 - length(p) * 0.5;
    color *= edge;

    // Output with density as alpha for compositing
    fragColor = vec4(color, density);
}

#endif // FRAGMENT_SHADER

// ============================================================================
// USAGE IN DSL:
//
// - id: volumetric_curl
//   type: shader
//   params:
//     shader_path: src/shaders/generators/volumetric_curl_3d.glsl
//     frequency: 2.0
//     amplitude: 1.0
//     octaves: 6
//     lacunarity: 2.0
//     persistence: 0.5
//     warp: 0.3
//     speed: 0.2
//     depth: 2.0
//     color_a: [0.0, 0.1, 0.2]  # Dark blue-black
//     color_b: [0.0, 1.0, 1.0]  # Cyan
//     glow: 0.8
//     density: 0.5
//     animate:
//       warp:
//         lfo:
//           type: sine
//           freq: 0.1
//           amp: 0.2
//       frequency:
//         lfo:
//           type: random_walk
//           freq: 0.05
//           amp: 0.5
// ============================================================================
