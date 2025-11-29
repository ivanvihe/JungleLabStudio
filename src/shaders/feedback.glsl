#version 330
uniform sampler2D tex0;
uniform sampler2D tex1;
uniform float feedback;
in vec2 uv;
out vec4 fragColor;

void main() {
    vec3 a = texture(tex0, uv).rgb;
    vec3 b = texture(tex1, uv).rgb;
    vec3 c = mix(a, b, feedback);
    fragColor = vec4(c, 1.0);
}
