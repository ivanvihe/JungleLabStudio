#version 330
uniform float time;
uniform sampler2D audio_tex;
uniform vec2 resolution;
uniform int vertical;
out vec4 fragColor;
in vec2 uv;

float hash(vec2 p){return fract(sin(dot(p,vec2(41.0,289.0)))*43758.5453);}

float filament(vec2 p, float seed){
    float a = seed*6.2831 + time*0.08;
    vec2 c = vec2(cos(a), sin(a)) * 0.4;
    float w = mix(0.004, 0.012, hash(p+seed));
    float d = abs((p.x*c.x + p.y*c.y) - 0.0) + length(p-c)*0.2;
    return smoothstep(w*8.0, w, d);
}

void main(){
    vec2 p = uv*2.0-1.0;
    float aspect = resolution.x / resolution.y;
    p.x *= aspect;
    if (vertical==1) p = p.yx;
    float audio = texture(audio_tex, vec2(0.6,0.0)).r;
    float f = 0.0;
    for(int i=0;i<8;i++){
        float seed = float(i)/8.0;
        f += filament(p, seed + audio*0.2);
    }
    f = clamp(f,0.0,1.0);
    vec3 col = vec3(1.0) * pow(f,0.8) * (0.5+audio*0.6);
    fragColor = vec4(col, f*0.8);
}
