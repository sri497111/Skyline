#version 330 core

layout (location = 0) in vec2 positionAttr;
layout (location = 1) in vec2 uvAttr;

out vec2 fragCoord;

void main()
{
    fragCoord = uvAttr;
    gl_Position = vec4(positionAttr, 0.0, 1.0);
}