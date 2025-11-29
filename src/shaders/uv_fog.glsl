#version 330
in vec2 uv;
out vec4 fragColor;

uniform float time;
uniform vec2 resolution;
uniform float density_mult;
uniform float glow_intensity;
uniform float color_shift;
uniform vec3 base_color;

// ------------------------------------------------------------------
// 3D Noise functions (Simplex/Gradient-ish)
// ------------------------------------------------------------------
vec3 hash33(vec3 p) { 
    p = vec3( dot(p,vec3(127.1,311.7, 74.7)),
              dot(p,vec3(269.5,183.3,246.1)),
              dot(p,vec3(113.5,271.9,124.6)));
    return -1.0 + 2.0 * fract(sin(p)*43758.5453123);
}

float noise(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    vec3 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix( dot( hash33( i + vec3(0,0,0) ), f - vec3(0,0,0) ), 
                        dot( hash33( i + vec3(1,0,0) ), f - vec3(1,0,0) ), u.x),
                   mix( dot( hash33( i + vec3(0,1,0) ), f - vec3(0,1,0) ), 
                        dot( hash33( i + vec3(1,1,0) ), f - vec3(1,1,0) ), u.x), u.y),
               mix(mix( dot( hash33( i + vec3(0,0,1) ), f - vec3(0,0,1) ), 
                        dot( hash33( i + vec3(1,0,1) ), f - vec3(1,0,1) ), u.x),
                   mix( dot( hash33( i + vec3(0,1,1) ), f - vec3(0,1,1) ), 
                        dot( hash33( i + vec3(1,1,1) ), f - vec3(1,1,1) ), u.x), u.y), u.z);
}

// Fractal Brownian Motion for organic nebulous detail
float fbm(vec3 p) {
    float f = 0.0;
    float amp = 0.5;
    for(int i = 0; i < 5; i++) {
        f += amp * noise(p);
        p *= 2.0;
        amp *= 0.5;
    }
    return f;
}

// ------------------------------------------------------------------
// Volumetric Map
// ------------------------------------------------------------------
float map(vec3 p) {
    // Slow breathing motion
    vec3 q = p + vec3(0.0, time * 0.05, time * 0.02);
    
    // Large organic shapes
    float n = fbm(q * 0.6);
    
    // Detail warping
    n += 0.3 * fbm(q * 2.0 + vec3(time * 0.05));
    
    // Sculpt density: keep it in center, fade out edges
    float dist = length(p.xy) * 0.4;
    float density = n - dist + 0.2; // Bias to separate clouds
    
    return max(0.0, density * density_mult);
}

// ------------------------------------------------------------------
// Main Raymarching
// ------------------------------------------------------------------
void main() {
    vec2 p = (uv - 0.5) * vec2(resolution.x / resolution.y, 1.0);
    
    // Camera setup
    vec3 ro = vec3(0.0, 0.0, 3.5); // Back a bit
    vec3 rd = normalize(vec3(p, -1.5)); // Wide angle
    
    vec3 col = vec3(0.01, 0.0, 0.02); // Deep near-black violet background
    
    float t = 0.0;
    vec3 sum = vec3(0.0);
    float transmittance = 1.0;
    
    // Palette: UV, Violet, Burgundy
    vec3 tintA = vec3(0.15, 0.0, 0.3);  // Deep Ultra Violet
    vec3 tintB = vec3(0.3, 0.0, 0.4);   // Purple
    vec3 tintC = vec3(0.4, 0.02, 0.1);  // Burgundy
    
    // Raymarch loop
    for(int i = 0; i < 96; i++) {
        vec3 pos = ro + rd * t;
        float dens = map(pos);
        
        if(dens > 0.001) {
            // Lighting / Absorption
            float step_size = 0.05 + t * 0.01;
            float absorb = dens * step_size;
            
            // Accumulate color based on density and position (pseudo-scattering)
            // Inner glow (high density) gets brighter/warmer
            vec3 scatter = mix(tintA, tintB, smoothstep(0.0, 0.5, dens));
            scatter = mix(scatter, tintC, smoothstep(0.4, 1.0, dens));
            
            // Add base user color shift
            scatter += base_color * 0.2;
            
            // Accumulate
            float light = absorb * glow_intensity * exp(-0.2 * t); // Decay with distance
            sum += scatter * light * transmittance;
            transmittance *= (1.0 - clamp(absorb * 2.0, 0.0, 1.0));
        }
        
        t += max(0.05, 0.02 * t); // Variable step size
        
        if(transmittance < 0.01) break;
        if(t > 10.0) break;
    }
    
    col = mix(col, sum, 1.0);
    
    // Tone mapping / Contrast
    col = pow(col, vec3(1.2)); // Darken darker areas (contrast)
    col *= 1.2; // Exposure
    
    // Subtle vignette
    col *= 1.0 - length(p) * 0.3;

    fragColor = vec4(col, 1.0);
}
