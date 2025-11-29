// ============================================================================
// ANIMATED CIRCLE - Shadertoy Test Shader
// Simple animated circle to test iTime and iResolution
// ============================================================================

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Normalize coordinates with aspect correction
    vec2 uv = fragCoord / iResolution.xy;
    uv = uv * 2.0 - 1.0;  // Center coordinates (-1 to 1)
    uv.x *= iResolution.x / iResolution.y;  // Correct aspect ratio

    // Animated circle position
    vec2 circlePos = vec2(
        sin(iTime) * 0.5,
        cos(iTime) * 0.5
    );

    // Distance from circle center
    float d = length(uv - circlePos);

    // Create smooth circle
    float circle = smoothstep(0.3, 0.28, d);

    // Animated color
    vec3 col = vec3(
        0.5 + 0.5 * sin(iTime),
        0.5 + 0.5 * cos(iTime * 0.7),
        0.5 + 0.5 * sin(iTime * 0.5)
    ) * circle;

    // Add glow
    col += vec3(0.1, 0.2, 0.3) * (1.0 - smoothstep(0.0, 0.5, d));

    fragColor = vec4(col, 1.0);
}
