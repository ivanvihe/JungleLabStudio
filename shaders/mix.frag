#version 330 core
out vec4 FragColor;

in vec2 TexCoords;

uniform sampler2D texture1;
uniform sampler2D texture2;
uniform float mixValue;

void main()
{             
    vec4 texColor1 = texture(texture1, TexCoords);
    vec4 texColor2 = texture(texture2, TexCoords);
    FragColor = mix(texColor1, texColor2, mixValue);
}
