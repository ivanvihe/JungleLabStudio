struct Uniforms {
    time: f32,
    audio_low: f32,
    audio_mid: f32,
    audio_high: f32,
    opacity: f32,
    amplitude: f32,
    layers: f32,
    glow: f32,
    distortion: f32,
    morphing: f32,
    resolution: f32,
}

@group(0) @binding(0) var<uniform> uniforms: Uniforms;

// Noise functions for organic movement
fn hash(p: vec2<f32>) -> f32 {
    return fract(sin(dot(p, vec2<f32>(127.1, 311.7))) * 43758.5453);
}

fn noise(p: vec2<f32>) -> f32 {
    let i = floor(p);
    let f = fract(p);
    let u = f * f * (3.0 - 2.0 * f);
    
    return mix(
        mix(hash(i + vec2<f32>(0.0, 0.0)), hash(i + vec2<f32>(1.0, 0.0)), u.x),
        mix(hash(i + vec2<f32>(0.0, 1.0)), hash(i + vec2<f32>(1.0, 1.0)), u.x),
        u.y
    );
}

fn fbm(p: vec2<f32>) -> f32 {
    var value = 0.0;
    var amplitude = 0.5;
    var frequency = 1.0;
    
    for (var i = 0; i < 4; i++) {
        value += amplitude * noise(p * frequency);
        amplitude *= 0.5;
        frequency *= 2.0;
    }
    
    return value;
}

// High-quality waveform generation
fn generateWaveform(uv: vec2<f32>, time: f32, layer: f32, audioData: vec3<f32>) -> f32 {
    let frequency = 8.0 + layer * 2.0;
    let phase = time * (0.5 + layer * 0.3) + layer * 1.57;
    
    // Multi-octave waveform with audio reactivity
    var wave = sin(uv.x * frequency + phase) * (0.3 + audioData.x * 0.7);
    wave += sin(uv.x * frequency * 1.618 + phase * 1.3) * (0.2 + audioData.y * 0.5) * 0.5;
    wave += sin(uv.x * frequency * 2.718 + phase * 0.7) * (0.1 + audioData.z * 0.3) * 0.25;
    
    // Add organic distortion
    let distortionNoise = fbm(uv * 3.0 + time * 0.2) * uniforms.distortion;
    wave += distortionNoise * (0.5 + audioData.x * 0.5);
    
    // Morphing between different wave types
    let morphFactor = uniforms.morphing * (0.5 + audioData.y * 0.5);
    let altWave = cos(uv.x * frequency * 0.8 + phase) * sin(uv.x * frequency * 1.3 + phase * 2.0);
    wave = mix(wave, altWave, morphFactor);
    
    return wave * uniforms.amplitude * (0.7 + layer * 0.1);
}

// Distance to waveform line with variable thickness
fn distanceToWaveform(uv: vec2<f32>, time: f32, layer: f32, audioData: vec3<f32>) -> f32 {
    let waveHeight = generateWaveform(uv, time, layer, audioData);
    let baseThickness = 0.02 + layer * 0.01;
    let audioThickness = baseThickness * (1.0 + audioData.x * 2.0);
    
    return smoothstep(audioThickness, 0.0, abs(uv.y - waveHeight));
}

// Advanced color mixing with HDR-like response
fn getWaveformColor(layer: f32, intensity: f32, audioData: vec3<f32>) -> vec3<f32> {
    // Base colors (cyan, magenta, yellow gradient)
    let color1 = vec3<f32>(0.0, 0.96, 1.0);  // Cyan
    let color2 = vec3<f32>(1.0, 0.08, 0.58); // Magenta  
    let color3 = vec3<f32>(1.0, 0.84, 0.0);  // Gold
    
    // Color progression based on layer and audio
    var color = mix(color1, color2, layer / uniforms.layers);
    color = mix(color, color3, audioData.z * 0.7);
    
    // HDR-like intensity boost
    let hdrFactor = 1.0 + intensity * 2.0 + audioData.y * 1.5;
    color *= hdrFactor;
    
    return color;
}

// Particle generation for high frequencies
fn generateParticles(uv: vec2<f32>, time: f32) -> f32 {
    let particleNoise = fbm(uv * 15.0 + time * 2.0);
    let threshold = 0.8 - uniforms.audio_high * 0.3;
    
    if (particleNoise > threshold) {
        let sparkle = sin(time * 10.0 + dot(uv, vec2<f32>(127.1, 311.7))) * 0.5 + 0.5;
        return sparkle * (particleNoise - threshold) * 10.0;
    }
    
    return 0.0;
}

// Chromatic aberration effect
fn chromaticAberration(uv: vec2<f32>, time: f32, audioData: vec3<f32>) -> vec3<f32> {
    let aberrationStrength = 0.002 + audioData.z * 0.005;
    let offset = vec2<f32>(aberrationStrength, 0.0);
    
    var result = vec3<f32>(0.0);
    
    for (var layer = 0.0; layer < uniforms.layers; layer += 1.0) {
        let r_intensity = distanceToWaveform(uv - offset, time, layer, audioData);
        let g_intensity = distanceToWaveform(uv, time, layer, audioData);
        let b_intensity = distanceToWaveform(uv + offset, time, layer, audioData);
        
        let layerColor = getWaveformColor(layer, g_intensity, audioData);
        
        result.r += r_intensity * layerColor.r;
        result.g += g_intensity * layerColor.g;
        result.b += b_intensity * layerColor.b;
    }
    
    return result;
}

@vertex
fn vs_main(@builtin(vertex_index) vertex_index: u32) -> @builtin(position) vec4<f32> {
    var pos = array<vec2<f32>, 3>(
        vec2<f32>(-1.0, -1.0),
        vec2<f32>(3.0, -1.0),
        vec2<f32>(-1.0, 3.0)
    );
    return vec4<f32>(pos[vertex_index], 0.0, 1.0);
}

@fragment
fn fs_main(@builtin(position) frag_coord: vec4<f32>) -> @location(0) vec4<f32> {
    let resolution = vec2<f32>(1920.0, 1080.0); // High resolution base
    var uv = (frag_coord.xy / resolution) * 2.0 - 1.0;
    uv.x *= resolution.x / resolution.y; // Aspect ratio correction
    
    let time = uniforms.time;
    let audioData = vec3<f32>(uniforms.audio_low, uniforms.audio_mid, uniforms.audio_high);
    
    // Background with subtle grid
    let gridUv = uv * 20.0;
    let grid = abs(fract(gridUv) - 0.5) / fwidth(gridUv);
    let gridLine = 1.0 - min(grid.x, grid.y);
    var finalColor = vec3<f32>(0.02, 0.05, 0.1) * smoothstep(0.0, 1.0, gridLine) * 0.1;
    
    // Audio-reactive background pulse
    let bgPulse = sin(time * 2.0) * 0.5 + 0.5;
    finalColor += vec3<f32>(0.05, 0.1, 0.15) * audioData.x * bgPulse * 0.3;
    
    // Generate waveform with chromatic aberration
    let waveformColor = chromaticAberration(uv, time, audioData);
    finalColor += waveformColor;
    
    // Add glow effect
    if (uniforms.glow > 0.0) {
        let glowSamples = 8.0;
        var glow = vec3<f32>(0.0);
        
        for (var i = 0.0; i < glowSamples; i += 1.0) {
            let angle = (i / glowSamples) * 6.28318;
            let offset = vec2<f32>(cos(angle), sin(angle)) * uniforms.glow * 0.02;
            glow += chromaticAberration(uv + offset, time, audioData) * 0.125;
        }
        
        finalColor += glow * 0.5;
    }
    
    // Add particles for high frequencies
    let particles = generateParticles(uv, time);
    finalColor += vec3<f32>(1.0, 0.9, 0.7) * particles * uniforms.audio_high;
    
    // Post-processing
    // Tone mapping for HDR-like appearance
    finalColor = finalColor / (finalColor + vec3<f32>(1.0));
    
    // Subtle vignette
    let vignette = 1.0 - length(uv * 0.7);
    finalColor *= vignette;
    
    // Final gamma correction
    finalColor = pow(finalColor, vec3<f32>(0.8));
    
    return vec4<f32>(finalColor * uniforms.opacity, uniforms.opacity);
}