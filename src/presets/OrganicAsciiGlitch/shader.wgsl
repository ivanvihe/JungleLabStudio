struct Uniforms {
    time: f32,
    resolution: vec2<f32>,
    asciiDensity: f32,
    asciiThreshold: f32,
    glitchIntensity: f32,
    pixelSortingAmount: f32,
    rgbShift: f32,
    frameTearProbability: f32,
    burstActive: f32,
    burstTime: f32,
    burstIntensity: f32,
};

@group(0) @binding(0) var<uniform> uniforms: Uniforms;
@group(0) @binding(1) var screenTexture: texture_2d<f32>;
@group(0) @binding(2) var screenSampler: sampler;
@group(0) @binding(3) var fontTexture: texture_2d<f32>;
@group(0) @binding(4) var fontSampler: sampler;

fn luminance(color: vec3<f32>) -> f32 {
    return dot(color, vec3<f32>(0.299, 0.587, 0.114));
}

fn get_char_uv(char_index: i32, font_dim: vec2<f32>) -> vec2<f32> {
    let char_x = f32(char_index % i32(font_dim.x));
    let char_y = f32(char_index / i32(font_dim.x));
    return vec2<f32>(char_x / font_dim.x, char_y / font_dim.y);
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
    var uv = in.uv;

    // --- Burst Effects on UV ---
    if (uniforms.burstActive > 0.5) {
        let burst_progress = uniforms.burstTime / 0.5; // Assuming 500ms burst duration for this effect
        let radial_distort = (sin(burst_progress * 3.14159) * 0.1) * uniforms.burstIntensity;
        let center_dist = distance(uv, vec2<f32>(0.5, 0.5));
        uv += normalize(uv - vec2<f32>(0.5, 0.5)) * radial_distort * (1.0 - center_dist);
    }
    
    // --- ASCII Mapping ---
    let char_set = " .,:;irsXA253hMHGS#9B&@"; // Example from dark to light
    let num_chars = 23.0;
    
    var ascii_density = uniforms.asciiDensity;
    if (uniforms.burstActive > 0.5) {
        ascii_density *= (1.0 + 1.5 * uniforms.burstIntensity);
    }
    
    let font_char_size = vec2<f32>(8.0, 16.0); // Size of one character in pixels
    let ascii_grid_size = floor(uniforms.resolution / font_char_size * ascii_density);
    
    let block_uv = floor(uv * ascii_grid_size) / ascii_grid_size;
    let video_color = textureSample(screenTexture, screenSampler, block_uv);
    
    let lum = luminance(video_color.rgb) * (1.0 + uniforms.asciiThreshold * 2.0 - 1.0);
    var char_index = i32(clamp(floor(lum * num_chars), 0.0, num_chars - 1.0));

    if (uniforms.burstActive > 0.5) {
      char_index = i32(num_chars) - char_index; // Invert characters on burst
    }

    let font_dim = vec2<f32>(16.0, 16.0); // Dimensions of the font texture grid
    let char_uv_start = get_char_uv(char_index, font_dim);
    let char_uv_size = vec2<f32>(1.0 / font_dim.x, 1.0 / font_dim.y);
    
    let sub_uv = fract(uv * ascii_grid_size) * char_uv_size;
    let ascii_color = textureSample(fontTexture, fontSampler, char_uv_start + sub_uv);

    var final_color = ascii_color * video_color; // Modulate ASCII with video color

    // --- Glitch Effects ---
    var rgb_shift = uniforms.rgbShift;
    if (uniforms.burstActive > 0.5) {
        rgb_shift *= (1.0 + 5.0 * uniforms.burstIntensity);
    }
    let r_channel = textureSample(screenTexture, screenSampler, uv + vec2<f32>(rgb_shift, 0.0)).r;
    let b_channel = textureSample(screenTexture, screenSampler, uv - vec2<f32>(rgb_shift, 0.0)).b;
    final_color.r = mix(final_color.r, r_channel, uniforms.glitchIntensity * 0.2);
    final_color.b = mix(final_color.b, b_channel, uniforms.glitchIntensity * 0.2);

    var pixel_sorting_amount = uniforms.pixelSortingAmount;
    if (uniforms.burstActive > 0.5) {
        pixel_sorting_amount *= (1.0 + 2.0 * uniforms.burstIntensity);
    }
    if (pixel_sorting_amount > 0.0) {
        let sort_threshold = 1.0 - pixel_sorting_amount;
        if (lum > sort_threshold) {
            let sorted_uv_x = uv.x - (lum - sort_threshold) * 0.1;
            final_color.rgb = mix(final_color.rgb, textureSample(screenTexture, screenSampler, vec2<f32>(sorted_uv_x, uv.y)).rgb, 0.5);
        }
    }
    
    // Bloom
    if (uniforms.burstActive > 0.5) {
        final_color.rgb *= (1.0 + 1.5 * uniforms.burstIntensity * (sin(uniforms.burstTime * 10.0) * 0.5 + 0.5));
    }
    
    return final_color;
}

struct VertexOutput {
    @builtin(position) position: vec4<f32>,
    @location(0) uv: vec2<f32>,
};

@vertex
fn vs_main(@builtin(vertex_index) in_vertex_index: u32) -> VertexOutput {
    var output: VertexOutput;
    let x = f32(in_vertex_index / 2u) * 2.0 - 1.0;
    let y = f32(in_vertex_index % 2u) * 2.0 - 1.0;
    output.position = vec4<f32>(x, -y, 0.0, 1.0);
    output.uv = vec2<f32>(output.position.x * 0.5 + 0.5, output.position.y * -0.5 + 0.5);
    return output;
}