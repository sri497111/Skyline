#version 330 core

in vec2 fragCoord;
out vec4 finalPixelColor;

uniform vec2  u_resolution;
uniform float u_time;

float randomFloat(vec2 coordinate)
{
    return fract(sin(dot(coordinate, vec2(12.9898, 78.233))) * 43758.5453);
}

void main()
{
    float totalSnow = 0.0;
    float skyGrad   = (1.0 - (fragCoord.y / u_resolution.x)) * 0.4;
    float grain     = randomFloat(fragCoord) * 0.01;

    for(int layerIndex = 0; layerIndex < 6; layerIndex++)
    {
        for(int flakeIndex = 0; flakeIndex < 12; flakeIndex++)
        {
            float fLayer = float(layerIndex);
            float fFlake = float(flakeIndex);

            float cellSize = 2.0 + (fFlake * 3.0);
            float fallRate = 0.3 + (sin(u_time * 0.4 + fLayer + fFlake * 20.0) + 1.0) * 0.00008;

            vec2 baseUV = (fragCoord / u_resolution.x);
            vec2 offsetUV = vec2(
                0.01 * sin((u_time + fLayer * 6185.0) * 0.6 + fFlake) * (5.0 / fFlake),
                fallRate * (u_time + fLayer * 1352.0) * (1.0 / fFlake)
            );

            vec2 uvCoord  = baseUV + offsetUV;
            vec2 gridStep = floor(uvCoord * cellSize + vec2(0.5)) / cellSize;

            vec2 seedA = vec2(12.9898 + fLayer * 12.0, 78.233 + fLayer * 315.156);
            vec2 seedB = vec2(62.2364 + fLayer * 23.0, 94.674 + fLayer * 95.0);

            float randX = fract(sin(dot(gridStep, seedA)) * 43758.5453 + fLayer * 12.0) - 0.5;
            float randY = fract(sin(dot(gridStep, seedB)) * 62159.8432 + fLayer * 12.0) - 0.5;

            float mag1 = sin(u_time * 2.5) * 0.7 / cellSize;
            float mag2 = cos(u_time * 2.5) * 0.7 / cellSize;

            vec2 particleCenter = gridStep + vec2(randX * sin(randY), randY) * mag1 + vec2(randY, randX) * mag2;
            float distVal = 5.0 * distance(particleCenter, uvCoord);

            vec2 omitSeed = vec2(32.4691, 94.615);
            float presence = fract(sin(dot(gridStep, omitSeed)) * 31572.1684);

            if(presence < 0.08)
            {
                float flakeBrightness = (randX + 1.0) * 0.4 * clamp(1.9 - distVal * (15.0 + randX * 6.3) * (cellSize / 1.4), 0.0, 1.0);
                totalSnow += flakeBrightness;
            }
        }
    }

    vec4 snowColor = vec4(totalSnow);
    vec4 tintColor = vec4(0.4, 0.8, 1.0, 0.0);

    finalPixelColor = snowColor + skyGrad * tintColor + grain;
}