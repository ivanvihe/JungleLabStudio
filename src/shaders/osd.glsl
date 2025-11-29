#version 330

uniform sampler2D tex0;
uniform float alpha;
uniform int overlay; // 0=Text, 1=Note, 2=Background, 3=Selection
uniform float time;
uniform float selection_y; // normalized Y position of selection

in vec2 uv;
out vec4 fragColor;

float rect(vec2 uv, vec2 pos, vec2 size) {
    vec2 d = abs(uv - pos) - size;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

void main() {
    vec2 v = vec2(uv.x, 1.0 - uv.y); // flip Y so text matches top-left origin

    // Background Panel
    if (overlay == 2) {
        // Sci-fi grid background
        vec2 grid_uv = v * 40.0 + vec2(time * 0.05, time * 0.02); // Animate grid
        vec2 grid = fract(grid_uv);
        float line = step(0.98, grid.x) + step(0.98, grid.y);
        vec3 bg = vec3(0.02, 0.02, 0.05) + vec3(line * 0.02);
        
        // Vignette
        float vig = 1.0 - length(v - 0.5) * 0.8;
        bg *= vig;

        // Border
        float d = rect(v, vec2(0.5), vec2(0.48, 0.48));
        float border = 1.0 - step(0.002, abs(d));
        bg += vec3(0.0, 0.8, 0.8) * border * alpha;

        fragColor = vec4(bg, alpha * 0.9);
        return;
    }
    
    // Note Overlay (Popup)
    if (overlay == 1) {
        v.y = mix(0.7, 0.9, v.y); // Remap UVs for small box
        v.x = mix(0.05, 0.95, v.x);
        vec4 c = texture(tex0, v);
        fragColor = vec4(c.rgb, c.a * alpha);
        return;
    }

    // Text Layer
    if (overlay == 0) {
        vec4 c = texture(tex0, v);
        // Add a slight glow to text
        fragColor = vec4(c.rgb * 1.2, c.a * alpha);
        return;
    }
}