#version 330
uniform float time;
uniform sampler2D audio_tex;
uniform vec2 resolution;
uniform int vertical;
in vec2 uv;
out vec4 fragColor;

float hash(vec3 p){return fract(sin(dot(p,vec3(53.1,91.7,121.1)))*43758.5453);}
float noise(vec3 p){
    vec3 i=floor(p); vec3 f=fract(p);
    f=f*f*(3.0-2.0*f);
    float n=mix(mix(mix(hash(i+vec3(0,0,0)),hash(i+vec3(1,0,0)),f.x),
                   mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),
                 mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),
                     mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);
    return n;
}
float fbm(vec3 p){
    float v=0.0; float a=0.6;
    for(int i=0;i<5;i++){v+=a*noise(p); p*=1.9; a*=0.55;}
    return v;
}

void main(){
    vec2 p = uv*2.0-1.0;
    float aspect = resolution.x/resolution.y;
    p.x *= aspect;
    if(vertical==1) p=p.yx;
    vec3 ro=vec3(0.0,0.0,-4.5);
    vec3 rd=normalize(vec3(p,1.4));
    float t=0.0; float accum=0.0; vec3 col=vec3(0.0);
    float audio = texture(audio_tex, vec2(0.2,0.0)).r;
    for(int i=0;i<80;i++){
        vec3 pos=ro+rd*t;
        float band=fbm(pos*0.8 + vec3(0,time*0.15,0));
        float sheet=smoothstep(0.35,0.8, band + sin(pos.y*2.0+time*0.3)*0.1 + audio*0.3);
        vec3 c=mix(vec3(0.05,0.2,0.4), vec3(0.8,0.2,0.9), band);
        col += (1.0-accum) * c * sheet * 0.08;
        accum += sheet*0.04;
        t += 0.07;
        if(accum>0.95) break;
    }
    float vig = smoothstep(1.15,0.4,length(p));
    col *= vig;
    fragColor = vec4(col,1.0);
}
