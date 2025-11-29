#version 330
uniform sampler2D tex0;
uniform vec2 resolution;
uniform float time;
uniform float chromatic;
uniform float pixelate;
uniform float vhs;
uniform float datamosh;
uniform float crt;
uniform float bloom_pulse;
uniform float shockwave;
uniform float color_glitch;
uniform float blur;
uniform float smear;
uniform float heat;
in vec2 uv;
out vec4 fragColor;

float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }

vec3 sample(vec2 p){
    if(pixelate>0.0){
        float scale = mix(1.0, 200.0, clamp(pixelate,0.0,1.0));
        p = floor(p*scale)/scale;
    }
    return texture(tex0, p).rgb;
}

void main(){
    vec2 p = uv;
    vec3 col = sample(p);

    if(chromatic>0.0){
        vec2 off = (p-0.5)*0.005*chromatic;
        col.r = sample(p+off).r;
        col.b = sample(p-off).b;
    }

    if(blur>0.0){
        vec2 step = vec2(1.0)/resolution;
        vec3 b = vec3(0.0);
        float wsum=0.0;
        for(int x=-2;x<=2;x++){
            for(int y=-2;y<=2;y++){
                float w = exp(-float(x*x+y*y)*0.5);
                b += sample(p+vec2(x,y)*step)*w;
                wsum+=w;
            }
        }
        b/=wsum;
        col = mix(col,b,clamp(blur,0.0,0.8));
    }

    if(smear>0.0){
        vec2 dir = vec2(sin(time*0.7), cos(time*0.5))*0.003*smear;
        col = mix(col, sample(p-dir), 0.5*smear);
    }

    if(color_glitch>0.0){
        float n = hash(vec2(floor(p.y*80.0), time*2.0));
        if(n>0.7){
            col.g = sample(p+vec2(0.01*color_glitch,0.0)).g;
        }
    }

    if(vhs>0.0){
        float jitter = (hash(vec2(time*3.0, p.y))-0.5)*0.01*vhs;
        col = sample(p+vec2(jitter,0.0));
    }

    if(datamosh>0.0){
        float stripe = step(0.9, fract(p.y*25.0 + time*0.5));
        if(stripe>0.0){
            col = sample(vec2(p.x+0.05*datamosh, p.y));
        }
    }

    if(crt>0.0){
        float vign = smoothstep(0.9, 0.6, length(p-0.5));
        col *= mix(1.0, vign, crt*0.8);
        col *= 0.95 + 0.05*sin((p.y+time*0.2)*1200.0);
    }

    if(bloom_pulse>0.0){
        col += bloom_pulse * 0.15;
    }

    if(shockwave>0.0){
        float r = length(p-0.5);
        float wave = exp(-pow((r - fract(time*0.4))*20.0,2.0))*shockwave;
        col += wave;
    }

    if(heat>0.0){
        vec2 wobble = vec2(sin(p.y*80.0+time*2.0), cos(p.x*80.0+time*1.5))*0.002*heat;
        col = sample(p+wobble);
    }

    fragColor = vec4(col,1.0);
}
