struct Uniforms {
    time: f32,
    audio_low: f32,
    audio_mid: f32,
    audio_high: f32,
    opacity: f32,
}

@group(0) @binding(0) var<uniform> uniforms: Uniforms;

// Función para generar ruido pseudo-aleatorio
fn hash(p: vec2<f32>) -> f32 {
    let h = dot(p, vec2<f32>(127.1, 311.7));
    return fract(sin(h) * 43758.5453123);
}

// Función para interpolar suavemente
fn smoothstep_custom(edge0: f32, edge1: f32, x: f32) -> f32 {
    let t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

// Función para crear nodos de la red neuronal
fn draw_node(uv: vec2<f32>, center: vec2<f32>, size: f32, activity: f32) -> f32 {
    let d = distance(uv, center);
    let pulse = 0.5 + 0.5 * sin(uniforms.time * 3.0 + activity * 10.0);
    let node_size = size * (0.8 + 0.4 * pulse * activity);
    return 1.0 - smoothstep_custom(node_size - 0.01, node_size + 0.01, d);
}

// Función para crear conexiones entre nodos
fn draw_connection(uv: vec2<f32>, start: vec2<f32>, end: vec2<f32>, strength: f32) -> f32 {
    let line_vec = end - start;
    let point_vec = uv - start;
    let line_len = length(line_vec);
    let line_dir = line_vec / line_len;
    
    let projection = dot(point_vec, line_dir);
    let closest_point = start + clamp(projection, 0.0, line_len) * line_dir;
    let distance_to_line = distance(uv, closest_point);
    
    let line_width = 0.002 + strength * 0.008;
    let line_alpha = 1.0 - smoothstep_custom(0.0, line_width, distance_to_line);
    
    // Animación de flujo de datos a lo largo de las conexiones
    let flow_pos = fract(uniforms.time * 0.5 + strength * 2.0);
    let flow_distance = abs(projection / line_len - flow_pos);
    let flow_pulse = 1.0 - smoothstep_custom(0.0, 0.1, flow_distance);
    
    return line_alpha * (0.3 + 0.7 * flow_pulse * strength);
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
    let resolution = vec2<f32>(800.0, 600.0);
    let uv = (frag_coord.xy / resolution) * 2.0 - 1.0;
    let aspect = resolution.x / resolution.y;
    let corrected_uv = vec2<f32>(uv.x * aspect, uv.y);
    
    var color = vec3<f32>(0.0);
    
    // Definir posiciones de nodos para 4 capas de la red neuronal
    // Capa de entrada (4 nodos)
    let input_nodes = array<vec2<f32>, 4>(
        vec2<f32>(-1.2, 0.6),
        vec2<f32>(-1.2, 0.2),
        vec2<f32>(-1.2, -0.2),
        vec2<f32>(-1.2, -0.6)
    );
    
    // Capa oculta 1 (6 nodos)
    let hidden1_nodes = array<vec2<f32>, 6>(
        vec2<f32>(-0.4, 0.8),
        vec2<f32>(-0.4, 0.48),
        vec2<f32>(-0.4, 0.16),
        vec2<f32>(-0.4, -0.16),
        vec2<f32>(-0.4, -0.48),
        vec2<f32>(-0.4, -0.8)
    );
    
    // Capa oculta 2 (4 nodos)
    let hidden2_nodes = array<vec2<f32>, 4>(
        vec2<f32>(0.4, 0.6),
        vec2<f32>(0.4, 0.2),
        vec2<f32>(0.4, -0.2),
        vec2<f32>(0.4, -0.6)
    );
    
    // Capa de salida (2 nodos)
    let output_nodes = array<vec2<f32>, 2>(
        vec2<f32>(1.2, 0.3),
        vec2<f32>(1.2, -0.3)
    );
    
    // Calcular activación de nodos basada en audio
    let base_time = uniforms.time * 0.5;
    
    // Dibujar conexiones de entrada a oculta1
    for (var i = 0; i < 4; i = i + 1) {
        for (var j = 0; j < 6; j = j + 1) {
            let strength = 0.3 + 0.7 * uniforms.audio_low * (0.5 + 0.5 * sin(base_time + f32(i * j)));
            let connection_color = draw_connection(corrected_uv, input_nodes[i], hidden1_nodes[j], strength);
            color += connection_color * vec3<f32>(0.3, 0.7, 1.0) * strength;
        }
    }
    
    // Dibujar conexiones de oculta1 a oculta2
    for (var i = 0; i < 6; i = i + 1) {
        for (var j = 0; j < 4; j = j + 1) {
            let strength = 0.3 + 0.7 * uniforms.audio_mid * (0.5 + 0.5 * sin(base_time * 1.3 + f32(i * j)));
            let connection_color = draw_connection(corrected_uv, hidden1_nodes[i], hidden2_nodes[j], strength);
            color += connection_color * vec3<f32>(0.7, 1.0, 0.3) * strength;
        }
    }
    
    // Dibujar conexiones de oculta2 a salida
    for (var i = 0; i < 4; i = i + 1) {
        for (var j = 0; j < 2; j = j + 1) {
            let strength = 0.3 + 0.7 * uniforms.audio_high * (0.5 + 0.5 * sin(base_time * 1.7 + f32(i * j)));
            let connection_color = draw_connection(corrected_uv, hidden2_nodes[i], output_nodes[j], strength);
            color += connection_color * vec3<f32>(1.0, 0.3, 0.7) * strength;
        }
    }
    
    // Dibujar nodos de entrada
    for (var i = 0; i < 4; i = i + 1) {
        let activity = 0.2 + 0.8 * uniforms.audio_low * (0.5 + 0.5 * sin(base_time * 2.0 + f32(i)));
        let node_color = draw_node(corrected_uv, input_nodes[i], 0.05, activity);
        color += node_color * vec3<f32>(0.2, 0.6, 1.0) * activity;
    }
    
    // Dibujar nodos ocultos 1
    for (var i = 0; i < 6; i = i + 1) {
        let activity = 0.2 + 0.8 * uniforms.audio_mid * (0.5 + 0.5 * sin(base_time * 1.5 + f32(i)));
        let node_color = draw_node(corrected_uv, hidden1_nodes[i], 0.045, activity);
        color += node_color * vec3<f32>(0.6, 1.0, 0.2) * activity;
    }
    
    // Dibujar nodos ocultos 2
    for (var i = 0; i < 4; i = i + 1) {
        let activity = 0.2 + 0.8 * uniforms.audio_high * (0.5 + 0.5 * sin(base_time * 1.8 + f32(i)));
        let node_color = draw_node(corrected_uv, hidden2_nodes[i], 0.04, activity);
        color += node_color * vec3<f32>(1.0, 0.6, 0.2) * activity;
    }
    
    // Dibujar nodos de salida
    for (var i = 0; i < 2; i = i + 1) {
        let activity = 0.3 + 0.7 * (uniforms.audio_low + uniforms.audio_mid + uniforms.audio_high) / 3.0 * (0.5 + 0.5 * sin(base_time * 2.2 + f32(i)));
        let node_color = draw_node(corrected_uv, output_nodes[i], 0.06, activity);
        color += node_color * vec3<f32>(1.0, 0.2, 0.6) * activity;
    }
    
    // Añadir un fondo sutil con patrón de cuadrícula
    let grid_uv = corrected_uv * 10.0;
    let grid = abs(fract(grid_uv) - 0.5) / fwidth(grid_uv);
    let grid_line = 1.0 - min(grid.x, grid.y);
    color += vec3<f32>(0.02, 0.05, 0.08) * smoothstep_custom(0.0, 1.0, grid_line) * 0.3;
    
    // Aplicar gamma correction y saturación
    color = pow(color, vec3<f32>(0.8));
    
    return vec4<f32>(color * uniforms.opacity, uniforms.opacity);
}