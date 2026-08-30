#version 120

uniform sampler2D iChannel0;
uniform vec2 iResolution;
uniform vec2 iChannelResolution;
uniform float iTime;

void main() {
    float snow = 0.0;
    vec2 fragCoord = gl_FragCoord.xy;

    for(int k = 0; k < 6; k++) {
        for(int i = 0; i < 12; i++) {
            float floatI = float(i + 1);
            float floatK = float(k);

            float cellSize = 2.0 + (floatI * 3.0);
            float downSpeed = 0.3 + (sin(iTime * 0.4 + floatK + floatI * 20.0) + 1.0) * 0.00008;

            vec2 uv = (fragCoord / iResolution.x) + vec2(
                0.01 * sin((iTime + floatK * 6185.0) * 0.6 + floatI) * (5.0 / floatI),
                downSpeed * (iTime + floatK * 1352.0) * (1.0 / floatI)
            );

            vec2 uvStep = ceil(uv * cellSize - vec2(0.5, 0.5)) / cellSize;

            float x = fract(sin(dot(uvStep, vec2(12.9898 + floatK * 12.0, 78.233 + floatK * 315.156))) * 43758.5453 + floatK * 12.0) - 0.5;
            float y = fract(sin(dot(uvStep, vec2(62.2364 + floatK * 23.0, 94.674 + floatK * 95.0))) * 62159.8432 + floatK * 12.0) - 0.5;

            float randomMagnitude1 = sin(iTime * 2.5) * 0.7 / cellSize;
            float randomMagnitude2 = cos(iTime * 2.5) * 0.7 / cellSize;

            float d = 5.0 * distance((uvStep + vec2(x * sin(y), y) * randomMagnitude1 + vec2(y, x) * randomMagnitude2), uv);

            float omiVal = fract(sin(dot(uvStep, vec2(32.4691, 94.615))) * 31572.1684);
            if(omiVal < 0.08) {
                float newd = (x + 1.0) * 0.4 * clamp(1.9 - d * (15.0 + (x * 6.3)) * (cellSize / 1.4), 0.0, 1.0);
                snow += newd;
            }
        }
    }

    vec2 bgCoord = vec2(fragCoord.x, iResolution.y - fragCoord.y);
    vec2 bgUV = bgCoord / iChannelResolution;
    vec4 texColor = texture2D(iChannel0, bgUV);

    float cornerRadius = 55.0; 
    
    vec2 halfRes = iResolution.xy * 0.5;
    vec2 p = fragCoord - halfRes;
    vec2 d_box = abs(p) - halfRes + vec2(cornerRadius);
    float dist = min(max(d_box.x, d_box.y), 0.0) + length(max(d_box, 0.0)) - cornerRadius;
    
    float mask = clamp(1.0 - dist, 0.0, 1.0);

    float snowVisibility = clamp(snow, 0.0, 0.85) * mask;

    vec3 finalColor = mix(texColor.rgb, vec3(1.0), snowVisibility);
    gl_FragColor = vec4(finalColor, texColor.a);
}