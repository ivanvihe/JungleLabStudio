// Volumetric shader with 3D noise and ray marching

// 3D Simplex Noise
fn mod289_3(x: vec3<f32>) -> vec3<f32> {
    return x - floor(x * (1.0 / 289.0)) * 289.0;
}

fn permute_3(x: vec3<f32>) -> vec3<f32> {
    return mod289_3(((x*34.0)+1.0)*x);
}

fn snoise_3d(v: vec3<f32>) -> f32 {
    let C = vec2<f32>(1.0/6.0, 1.0/3.0) ;
    let D = vec4<f32>(0.0, 0.5, 1.0, 2.0);

    let i  = floor(v + dot(v, C.yyy) );
    let x0 =   v - i + dot(i, C.xxx) ;

    let g = step(x0.yzx, x0.xyz);
    let l = 1.0 - g;
    let i1 = min( g.xyz, l.zxy );
    let i2 = max( g.xyz, l.zxy );

    let x1 = x0 - i1 + C.xxx;
    let x2 = x0 - i2 + C.yyy;
    let x3 = x0 - D.yyy;

    let i_mod289 = mod289_3(i);
    let p = permute_3( permute_3( i_mod289.z + vec3<f32>(0.0, i1.z, i2.z) ) + i_mod289.y + vec3<f32>(0.0, i1.y, i2.y) ) + i_mod289.x + vec3<f32>(0.0, i1.x, i2.x);

    var m = max(0.5 - vec4<f32>(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), vec4<f32>(0.0));
    m = m*m;
    m = m*m;

    let x_ = 2.0 * fract(p * C.www) - 1.0;
    let h = abs(x_) - 0.5;
    let ox = floor(x_ + 0.5);
    let a0 = x_ - ox;

    m = m * (1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h ));

    let g_ = vec3<f32>(a0.x  * x0.x, a0.y  * x1.y, a0.z  * x2.z);
    g_ = g_ + vec3<f32>(h.x   * x0.y, h.y   * x1.z, h.z   * x2.x);
    g_ = g_ + vec3<f32>(ox.x  * x0.z, ox.y  * x1.x, ox.z  * x2.y);
    g_ = g_ + vec3<f32>(a0.x  * x0.x, a0.y  * x1.y, a0.z  * x2.z);

    return 130.0 * dot(m, vec4<f32>( dot(g_,x0), dot(g_,x1), dot(g_,x2), dot(g_,x3) ));
}

struct Uniforms {
    u_time: f32,
    u_resolution: vec2<f32>,
    u_audioLow: f32,
    u_audioMid: f32,
    u_audioHigh: f32,
    u_burst: f32,
    u_color1: vec3<f32>,
    u_color2: vec3<f32>,
    u_color3: vec3<f32>,
};

@group(0) @binding(0) var<uniform> uniforms: Uniforms;

fn map(p: vec3<f32>) -> f32 {
    var d = 1000.0;
    let s = sin(p * 0.5 + uniforms.u_time) * 0.5 + 0.5;
    d = min(d, snoise_3d(p * s) * 2.0);
    return d;
}

@fragment
fn fs_main(@builtin(position) fragCoord: vec4<f32>) -> @location(0) vec4<f32> {
    let uv = (fragCoord.xy - 0.5 * uniforms.u_resolution.xy) / uniforms.u_resolution.y;
    let ro = vec3<f32>(0.0, 0.0, -5.0);
    let rd = normalize(vec3<f32>(uv, 1.0));

    var t = 0.0;
    var col = vec3<f32>(0.0);

    for (var i = 0; i < 64; i = i + 1) {
        let p = ro + rd * t;
        let d = map(p);
        if (d < 0.01) {
            let density = smoothstep(0.0, 0.2, d);
            var c = mix(uniforms.u_color1, uniforms.u_color2, density);
            c = mix(c, uniforms.u_color3, uniforms.u_audioHigh);
            col += c * density * 0.1;
        }
        t += 0.1;
    }
    
    if (uniforms.u_burst > 0.0) {
        let burst_intensity = sin(uniforms.u_burst * 3.14159);
        col += vec3<f32>(burst_intensity * 0.5);
    }

    return vec4<f32>(col, 1.0);
}