#version 330
uniform mat4 mvp;
uniform float point_scale;
uniform vec3 tint;
uniform sampler2D audio_tex;
in vec3 in_position;
out vec3 v_color;

void main() {
    float idx = float(gl_VertexID);
    float audio = texture(audio_tex, vec2(fract(idx * 0.002), 0.0)).r;
    float size = mix(2.5, 9.0, audio);
    v_color = mix(vec3(0.2, 0.6, 1.0), tint, audio);
    gl_Position = mvp * vec4(in_position, 1.0);
    gl_PointSize = size * point_scale;
}

// Fragment
#ifdef FRAGMENT_SHADER
in vec3 v_color;
out vec4 fragColor;
void main() {
    vec2 uv = gl_PointCoord.xy * 2.0 - 1.0;
    float d = clamp(1.0 - dot(uv, uv), 0.0, 1.0);
    fragColor = vec4(v_color * d * 1.5, d);
}
#endif
