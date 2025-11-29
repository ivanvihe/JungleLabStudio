// ============================================================================
// RAYMARCHING SPHERE - Shadertoy Test Shader
// Classic raymarching example
// Tests iTime, iResolution, and demonstrates typical Shadertoy raymarching
// ============================================================================

// Signed distance function for a sphere
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

// Scene SDF
float map(vec3 p) {
    // Animated sphere
    vec3 spherePos = vec3(0.0, 0.0, 0.0);
    float sphere = sdSphere(p - spherePos, 1.0);

    return sphere;
}

// Calculate normal using gradient
vec3 calcNormal(vec3 p) {
    float eps = 0.001;
    vec2 h = vec2(eps, 0.0);
    return normalize(vec3(
        map(p + h.xyy) - map(p - h.xyy),
        map(p + h.yxy) - map(p - h.yxy),
        map(p + h.yyx) - map(p - h.yyx)
    ));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Normalized coordinates
    vec2 uv = (fragCoord - 0.5 * iResolution.xy) / iResolution.y;

    // Camera setup
    vec3 ro = vec3(0.0, 0.0, 3.0);  // Ray origin
    vec3 rd = normalize(vec3(uv, -1.0));  // Ray direction

    // Rotate camera
    float angle = iTime * 0.5;
    float c = cos(angle);
    float s = sin(angle);
    ro.xz = mat2(c, -s, s, c) * ro.xz;
    rd.xz = mat2(c, -s, s, c) * rd.xz;

    // Raymarching
    float t = 0.0;
    vec3 col = vec3(0.0);

    for (int i = 0; i < 80; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);

        if (d < 0.001) {
            // Hit! Calculate lighting
            vec3 normal = calcNormal(p);
            vec3 lightDir = normalize(vec3(1.0, 1.0, 1.0));

            // Simple diffuse lighting
            float diff = max(dot(normal, lightDir), 0.0);

            // Animated color
            vec3 baseCol = vec3(
                0.5 + 0.5 * sin(iTime),
                0.5 + 0.5 * cos(iTime * 0.7),
                0.5 + 0.5 * sin(iTime * 0.5)
            );

            col = baseCol * diff;

            // Add specular
            vec3 viewDir = normalize(-rd);
            vec3 reflectDir = reflect(-lightDir, normal);
            float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32.0);
            col += vec3(spec);

            break;
        }

        if (t > 20.0) {
            // Ray escaped, use background
            col = vec3(0.1, 0.1, 0.2) * (1.0 - length(uv) * 0.5);
            break;
        }

        t += d;
    }

    fragColor = vec4(col, 1.0);
}
