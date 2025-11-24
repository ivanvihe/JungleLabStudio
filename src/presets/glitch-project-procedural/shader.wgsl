// Advanced Procedural Shader with Raymarching, SDF, and Volumetric Effects
// TouchDesigner / GLSL-style high-definition complexity

struct VertexInput {
    @location(0) position: vec3f,
    @location(1) normal: vec3f,
    @location(2) uv: vec2f,
};

struct VertexOutput {
    @builtin(position) position: vec4f,
    @location(0) worldPosition: vec3f,
    @location(1) normal: vec3f,
    @location(2) uv: vec2f,
    @location(3) viewDirection: vec3f,
};

struct Uniforms {
    modelViewProjection: mat4x4f,
    model: mat4x4f,
    view: mat4x4f,
    cameraPosition: vec3f,
    time: f32,

    // Shader parameters
    distortionIntensity: f32,
    noiseScale: f32,
    rayMarchSteps: f32,
    sdfSmoothing: f32,
    volumetricDensity: f32,

    // Motion
    flowSpeed: f32,
    turbulence: f32,
    smoothness: f32,

    // Audio reactivity
    lowFreq: f32,
    midFreq: f32,
    highFreq: f32,
    beatPulse: f32,

    // Colors
    primaryColor: vec3f,
    accent1Color: vec3f,
    accent2Color: vec3f,
    highlightColor: vec3f,
    glowColor: vec3f,

    // Effects flags
    enableVolumetric: f32,
    enableRaymarching: f32,
    enableDistortion: f32,
    enableGlow: f32,
};

@group(0) @binding(0) var<uniform> uniforms: Uniforms;

// ============================================================================
// NOISE FUNCTIONS - High quality procedural noise
// ============================================================================

fn hash(p: vec3f) -> vec3f {
    var q = vec3f(
        dot(p, vec3f(127.1, 311.7, 74.7)),
        dot(p, vec3f(269.5, 183.3, 246.1)),
        dot(p, vec3f(113.5, 271.9, 124.6))
    );
    return fract(sin(q) * 43758.5453123);
}

fn noise3D(p: vec3f) -> f32 {
    let i = floor(p);
    let f = fract(p);
    let u = f * f * (3.0 - 2.0 * f);

    return mix(
        mix(
            mix(dot(hash(i + vec3f(0.0, 0.0, 0.0)), f - vec3f(0.0, 0.0, 0.0)),
                dot(hash(i + vec3f(1.0, 0.0, 0.0)), f - vec3f(1.0, 0.0, 0.0)), u.x),
            mix(dot(hash(i + vec3f(0.0, 1.0, 0.0)), f - vec3f(0.0, 1.0, 0.0)),
                dot(hash(i + vec3f(1.0, 1.0, 0.0)), f - vec3f(1.0, 1.0, 0.0)), u.x), u.y),
        mix(
            mix(dot(hash(i + vec3f(0.0, 0.0, 1.0)), f - vec3f(0.0, 0.0, 1.0)),
                dot(hash(i + vec3f(1.0, 0.0, 1.0)), f - vec3f(1.0, 0.0, 1.0)), u.x),
            mix(dot(hash(i + vec3f(0.0, 1.0, 1.0)), f - vec3f(0.0, 1.0, 1.0)),
                dot(hash(i + vec3f(1.0, 1.0, 1.0)), f - vec3f(1.0, 1.0, 1.0)), u.x), u.y), u.z
    );
}

fn fbm(p: vec3f, octaves: i32) -> f32 {
    var value = 0.0;
    var amplitude = 0.5;
    var frequency = 1.0;
    var position = p;

    for (var i = 0; i < octaves; i = i + 1) {
        value += amplitude * noise3D(position * frequency);
        frequency *= 2.0;
        amplitude *= 0.5;
        position = position * 2.0 + vec3f(0.1);
    }

    return value;
}

// ============================================================================
// SDF FUNCTIONS - Signed Distance Fields for complex shapes
// ============================================================================

fn sdSphere(p: vec3f, radius: f32) -> f32 {
    return length(p) - radius;
}

fn sdBox(p: vec3f, b: vec3f) -> f32 {
    let d = abs(p) - b;
    return length(max(d, vec3f(0.0))) + min(max(d.x, max(d.y, d.z)), 0.0);
}

fn sdTorus(p: vec3f, t: vec2f) -> f32 {
    let q = vec2f(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}

fn opSmoothUnion(d1: f32, d2: f32, k: f32) -> f32 {
    let h = max(k - abs(d1 - d2), 0.0) / k;
    return min(d1, d2) - h * h * k * 0.25;
}

fn opSmoothSubtraction(d1: f32, d2: f32, k: f32) -> f32 {
    let h = max(k - abs(-d1 - d2), 0.0) / k;
    return max(-d1, d2) + h * h * k * 0.25;
}

fn sdScene(p: vec3f) -> f32 {
    let time = uniforms.time * uniforms.flowSpeed;

    // Audio-reactive transformations
    let audioMorph = uniforms.lowFreq * 0.5 + uniforms.beatPulse * 0.3;

    // Rotating point for dynamic geometry
    let angle = time * 0.3 + audioMorph;
    let rotP = vec3f(
        p.x * cos(angle) - p.z * sin(angle),
        p.y + sin(time * 0.2) * 0.3 * uniforms.midFreq,
        p.x * sin(angle) + p.z * cos(angle)
    );

    // Multiple SDF shapes combined with smooth operations
    var d = sdSphere(rotP, 1.0 + sin(time) * 0.2 * audioMorph);

    // Add torus with audio reactivity
    let torus1 = sdTorus(rotP - vec3f(0.0, 0.0, 0.0), vec2f(1.5 + uniforms.midFreq * 0.3, 0.3));
    d = opSmoothUnion(d, torus1, uniforms.sdfSmoothing);

    // Add deformed box
    let boxP = rotP + vec3f(sin(time * 0.5), cos(time * 0.3), sin(time * 0.7)) * 0.5;
    let box1 = sdBox(boxP, vec3f(0.6 + uniforms.highFreq * 0.2));
    d = opSmoothSubtraction(box1, d, uniforms.sdfSmoothing * 0.5);

    // Add noise-based distortion
    let noiseFreq = uniforms.noiseScale * (1.0 + uniforms.turbulence);
    let distortion = fbm(rotP * noiseFreq + vec3f(time * 0.1), 4) * uniforms.distortionIntensity;

    return d + distortion * 0.3;
}

// ============================================================================
// RAYMARCHING - High quality volumetric rendering
// ============================================================================

fn calcNormal(p: vec3f) -> vec3f {
    let e = vec2f(0.001, 0.0);
    return normalize(vec3f(
        sdScene(p + e.xyy) - sdScene(p - e.xyy),
        sdScene(p + e.yxy) - sdScene(p - e.yxy),
        sdScene(p + e.yyx) - sdScene(p - e.yyx)
    ));
}

fn raymarch(ro: vec3f, rd: vec3f, maxSteps: i32) -> vec2f {
    var t = 0.0;
    var minDist = 999.0;

    for (var i = 0; i < maxSteps; i = i + 1) {
        let pos = ro + rd * t;
        let dist = sdScene(pos);

        minDist = min(minDist, dist);

        if (dist < 0.001) {
            return vec2f(t, 1.0); // Hit
        }

        if (t > 20.0) {
            break;
        }

        t += dist * 0.5; // Slower step for better quality
    }

    // Return distance and glow factor based on closest approach
    let glow = 1.0 / (1.0 + minDist * 10.0);
    return vec2f(t, glow);
}

// ============================================================================
// LIGHTING - Advanced PBR-style lighting
// ============================================================================

fn calculateLighting(p: vec3f, n: vec3f, viewDir: vec3f) -> vec3f {
    let time = uniforms.time * uniforms.flowSpeed;

    // Multiple dynamic lights
    let light1Dir = normalize(vec3f(sin(time), 1.0, cos(time)));
    let light2Dir = normalize(vec3f(-cos(time * 0.7), 0.5, -sin(time * 0.7)));
    let light3Dir = normalize(vec3f(0.0, -1.0, 0.0));

    // Audio-reactive light intensities
    let light1Intensity = 0.8 + uniforms.lowFreq * 0.4;
    let light2Intensity = 0.6 + uniforms.midFreq * 0.4;
    let light3Intensity = 0.3 + uniforms.highFreq * 0.3;

    // Diffuse lighting
    let diff1 = max(dot(n, light1Dir), 0.0) * light1Intensity;
    let diff2 = max(dot(n, light2Dir), 0.0) * light2Intensity;
    let diff3 = max(dot(n, light3Dir), 0.0) * light3Intensity;

    // Specular highlights (Blinn-Phong)
    let h1 = normalize(light1Dir + viewDir);
    let h2 = normalize(light2Dir + viewDir);
    let spec1 = pow(max(dot(n, h1), 0.0), 64.0) * light1Intensity;
    let spec2 = pow(max(dot(n, h2), 0.0), 32.0) * light2Intensity;

    // Fresnel effect for rim lighting
    let fresnel = pow(1.0 - max(dot(n, viewDir), 0.0), 3.0);
    let rimLight = fresnel * uniforms.highlightColor * 0.5;

    // Combine lighting
    let diffuse = (diff1 * uniforms.accent1Color + diff2 * uniforms.accent2Color + diff3 * uniforms.primaryColor) * 0.5;
    let specular = (spec1 + spec2) * uniforms.glowColor;

    return diffuse + specular + rimLight;
}

// ============================================================================
// VOLUMETRIC EFFECTS - Atmospheric scattering and fog
// ============================================================================

fn volumetricScattering(ro: vec3f, rd: vec3f, t: f32) -> vec3f {
    if (uniforms.enableVolumetric < 0.5) {
        return vec3f(0.0);
    }

    var scatter = vec3f(0.0);
    let steps = 8;
    let stepSize = t / f32(steps);

    for (var i = 0; i < steps; i = i + 1) {
        let sampleT = f32(i) * stepSize;
        let samplePos = ro + rd * sampleT;

        // Density based on distance to surface
        let dist = abs(sdScene(samplePos));
        let density = exp(-dist * 3.0) * uniforms.volumetricDensity;

        // Noise-based variation
        let noiseVal = fbm(samplePos * 2.0 + vec3f(uniforms.time * 0.1), 3);
        let variation = (noiseVal * 0.5 + 0.5) * density;

        // Color based on audio reactivity
        let scatterColor = mix(uniforms.accent2Color, uniforms.glowColor, uniforms.highFreq);
        scatter += scatterColor * variation * stepSize;
    }

    return scatter * 0.3;
}

// ============================================================================
// VERTEX SHADER
// ============================================================================

@vertex
fn vertexMain(input: VertexInput) -> VertexOutput {
    var output: VertexOutput;

    // Apply procedural displacement for organic movement
    var displaced = input.position;

    if (uniforms.enableDistortion > 0.5) {
        let noisePos = input.position * uniforms.noiseScale + vec3f(uniforms.time * uniforms.flowSpeed * 0.1);
        let displacement = fbm(noisePos, 4) * uniforms.distortionIntensity * 0.2;
        let audioDisp = (uniforms.lowFreq + uniforms.midFreq) * 0.1;
        displaced += input.normal * displacement * (1.0 + audioDisp);
    }

    let worldPos = uniforms.model * vec4f(displaced, 1.0);
    output.worldPosition = worldPos.xyz;
    output.position = uniforms.modelViewProjection * vec4f(displaced, 1.0);
    output.normal = normalize((uniforms.model * vec4f(input.normal, 0.0)).xyz);
    output.uv = input.uv;
    output.viewDirection = normalize(uniforms.cameraPosition - worldPos.xyz);

    return output;
}

// ============================================================================
// FRAGMENT SHADER
// ============================================================================

@fragment
fn fragmentMain(input: VertexOutput) -> @location(0) vec4f {
    let viewDir = normalize(input.viewDirection);
    var finalColor = vec3f(0.0);

    // Raymarching for advanced volumetric effects
    if (uniforms.enableRaymarching > 0.5) {
        let ro = uniforms.cameraPosition;
        let rd = -viewDir;
        let maxSteps = i32(uniforms.rayMarchSteps);
        let result = raymarch(ro, rd, maxSteps);
        let t = result.x;
        let glow = result.y;

        if (t < 20.0) {
            // Hit surface - calculate lighting
            let hitPos = ro + rd * t;
            let normal = calcNormal(hitPos);
            let lighting = calculateLighting(hitPos, normal, viewDir);

            // Add volumetric scattering
            let scatter = volumetricScattering(ro, rd, t);

            finalColor = lighting + scatter;

            // Apply glow effect
            if (uniforms.enableGlow > 0.5) {
                finalColor += uniforms.glowColor * glow * glow * uniforms.highFreq * 0.5;
            }
        } else {
            // Missed - add atmospheric glow
            if (uniforms.enableGlow > 0.5) {
                finalColor = uniforms.glowColor * glow * 0.3;
            }
        }
    } else {
        // Standard lighting without raymarching
        let lighting = calculateLighting(input.worldPosition, input.normal, viewDir);
        finalColor = lighting;
    }

    // Post-processing: subtle color grading for dark minimal aesthetic
    finalColor = pow(finalColor, vec3f(1.2)); // Slight contrast boost
    finalColor = mix(finalColor, uniforms.primaryColor, 0.1); // Tint towards primary color

    // Audio-reactive pulse
    let pulse = sin(uniforms.time * 3.0) * 0.5 + 0.5;
    finalColor += uniforms.glowColor * uniforms.beatPulse * pulse * 0.1;

    return vec4f(finalColor, 1.0);
}
