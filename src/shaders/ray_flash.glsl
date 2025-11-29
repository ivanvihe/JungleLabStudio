#version 330
uniform float time;
uniform float seed;
in vec2 uv;
out vec4 fragColor;

float hash(float n){ return fract(sin(n)*43758.5453); }

void main(){
    vec2 p = uv*2.0-1.0;
    float ang = seed*6.2831;
    float c = cos(ang), s = sin(ang);
    mat2 r = mat2(c,-s,s,c);
    p = r*p;
    float d = abs(p.y - 0.0);
    float beam = smoothstep(0.12, 0.0, d) * smoothstep(1.0, 0.4, abs(p.x));
    float pulse = smoothstep(0.0, 0.2, 1.0 - fract(time*0.5 + seed));
    float alpha = beam * pulse;
    fragColor = vec4(vec3(1.0), alpha * 0.9);
}
