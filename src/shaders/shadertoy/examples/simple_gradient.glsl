// ============================================================================
// SIMPLE GRADIENT - Shadertoy Test Shader
// A basic shader to test Shadertoy compatibility
// Uses only iTime and iResolution uniforms
// ============================================================================

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Normalize pixel coordinates (0-1)
    vec2 uv = fragCoord / iResolution.xy;

    // Create animated gradient
    vec3 col = vec3(
        uv.x,                           // Red increases left to right
        uv.y,                           // Green increases bottom to top
        0.5 + 0.5 * sin(iTime)         // Blue oscillates with time
    );

    // Output final color
    fragColor = vec4(col, 1.0);
}
