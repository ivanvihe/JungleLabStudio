#version 330
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform float time;
uniform vec2 resolution;

// Effect Intensities
uniform float slice_amt;
uniform float transform_amt;
uniform float rays_amt;
uniform float interference_amt;

// Utils
float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
float noise(vec2 p) { return hash(floor(p)); }

void main() {
    vec2 p = uv;
    
    // 1. Glitch Slice (Cortante)
    if (slice_amt > 0.0) {
        float block = floor(p.y * 20.0 + time * 10.0);
        float offset = hash(vec2(block, floor(time * 5.0))) - 0.5;
        if (hash(vec2(block, 1.0)) < slice_amt) {
            p.x += offset * 0.2;
        }
    }
    
    // 2. Transform (Twist/Zoom)
    if (transform_amt > 0.0) {
        vec2 c = p - 0.5;
        float ang = atan(c.y, c.x);
        float len = length(c);
        ang += sin(len * 10.0 - time * 5.0) * transform_amt;
        p = vec2(cos(ang), sin(ang)) * len + 0.5;
    }
    
    // 3. Interference (Noise/Lines)
    float inter = 0.0;
    if (interference_amt > 0.0) {
        float scan = sin(p.y * 800.0 + time * 20.0) * 0.1;
        float grain = hash(p * time) * 0.2;
        inter = (scan + grain) * interference_amt;
    }
    
    vec4 col = texture(tex0, p);
    col.rgb += inter;
    
    // 4. Light Rays (Post-sampling add)
    if (rays_amt > 0.0) {
        vec2 center = vec2(0.5, 0.5);
        vec2 dt = (p - center) * 0.01 * rays_amt;
        vec2 t = p + dt;
        for(int i=0; i<8; i++) {
            col.rgb += texture(tex0, t).rgb * 0.05 * rays_amt;
            t += dt;
        }
    }
    
    fragColor = col;
}
