// ============================================================================
// AUDIO CIRCLE - Simple bouncing circle shader
// ============================================================================

// VERTEX_SHADER
#version 330
in vec2 in_pos;
in vec2 in_uv;
out vec2 v_uv;

void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}

// FRAGMENT_SHADER
#version 330
in vec2 v_uv;
out vec4 fragColor;

uniform float u_time;
uniform vec2 u_resolution;
uniform float u_radius;
uniform vec2 u_position;
uniform vec3 u_color;
uniform float u_glow;
uniform float u_bounce_scale;

void main() {
    // Normalize coordinates to -1..1 with aspect ratio correction
    vec2 aspect = vec2(u_resolution.x / u_resolution.y, 1.0);
    vec2 p = (v_uv - u_position) * aspect;

    // Calculate distance from center
    float dist = length(p);

    // Apply bounce scale to radius
    float scaledRadius = u_radius * u_bounce_scale;

    // Create circle with smooth edge
    float circle = 1.0 - smoothstep(scaledRadius - 0.01, scaledRadius + 0.01, dist);

    // Add glow effect
    float glow = u_glow * (1.0 / (dist * 10.0 + 1.0));

    // Combine circle and glow
    float intensity = circle + glow;

    // Apply color
    vec3 col = u_color * intensity;

    fragColor = vec4(col, 1.0);
}
