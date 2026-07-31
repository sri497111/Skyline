#version 120

uniform sampler2D iChannel0;
uniform vec2 iResolution;
uniform vec2 iChannelResolution;
uniform float iTime;

#define S(a, b, t) smoothstep(a, b, t)

vec3 N13(float p) {
    vec3 p3 = fract(vec3(p) * vec3(.1031, .11369, .13787));
    p3 += dot(p3, p3.yzx + 19.19);
    return fract(vec3((p3.x + p3.y)*p3.z, (p3.x+p3.z)*p3.y, (p3.y+p3.z)*p3.x));
}

float N(float t) {
    return fract(sin(t*12345.564)*7658.76);
}

float Saw(float b, float t) {
    return S(0., b, t)*S(1., b, t);
}

vec2 DropLayer2(vec2 uv, float t) {
    vec2 UV = uv;
    uv.y += t*0.75;
    vec2 a = vec2(6., 1.);
    vec2 grid = a*2.;
    vec2 id = floor(uv*grid);
    
    float colShift = N(id.x); 
    uv.y += colShift;
    
    id = floor(uv*grid);
    vec3 n = N13(id.x*35.2+id.y*2376.1);
    vec2 st = fract(uv*grid)-vec2(.5, 0);
    
    float x = n.x-.5;
    float y = UV.y*20.;
    float wiggle = sin(y+sin(y));
    x += wiggle*(.5-abs(x))*(n.z-.5);
    x *= .7;
    float ti = fract(t+n.z);
    y = (Saw(.85, ti)-.5)*.9+.5;
    vec2 p = vec2(x, y);
    
    float d = length((st-p)*a.yx);
    float mainDrop = S(.4, .0, d);
    
    float r = sqrt(S(1., y, st.y));
    float cd = abs(st.x-x);
    float trail = S(.23*r, .15*r*r, cd);
    float trailFront = S(-.02, .02, st.y-y);
    trail *= trailFront*r*r;
    
    y = UV.y;
    float trail2 = S(.2*r, .0, cd);
    float droplets = max(0., (sin(y*(1.-y)*120.)-st.y))*trail2*trailFront*n.z;
    y = fract(y*10.)+(st.y-.5);
    float dd = length(st-vec2(x, y));
    droplets = S(.3, 0., dd);
    float m = mainDrop+droplets*r*trailFront;
    
    return vec2(m, trail);
}

float StaticDrops(vec2 uv, float t) {
    uv *= 40.;
    vec2 id = floor(uv);
    uv = fract(uv)-.5;
    vec3 n = N13(id.x*107.45+id.y*3543.654);
    vec2 p = (n.xy-.5)*.7;
    float d = length(uv-p);
    
    float fade = Saw(.025, fract(t+n.z));
    float c = S(.3, 0., d)*fract(n.z*10.)*fade;
    return c;
}

vec2 Drops(vec2 uv, float t) {
    float s = StaticDrops(uv, t)*2.0; 
    vec2 m1 = DropLayer2(uv, t);
    vec2 m2 = DropLayer2(uv*1.85, t)*0.5;
    
    s *= S(0.2, 0.0, m1.x + m2.x);
    
    float c = s + m1.x + m2.x;
    c = S(.3, 1., c);
    
    return vec2(c, max(m1.y*2.0, m2.y));
}

void main() {
    vec2 uv = gl_FragCoord.xy / 250.0;
    float t = iTime * 0.15;
    
    vec2 c = Drops(uv, t);
    vec2 e = vec2(.001, 0.);
    vec2 n = vec2(Drops(uv + e, t).x - c.x, Drops(uv + e.yx, t).x - c.x);
    
    // Background coordinates
    vec2 bgCoord = vec2(gl_FragCoord.x, iResolution.y - gl_FragCoord.y);
    vec2 bgUV = bgCoord / iChannelResolution;
    
    // Apply lens distortion (refraction) over the background UV
    if (c.x > 0.0) {
        bgUV -= n * 1.2;
    }
    
    gl_FragColor = vec4(texture2D(iChannel0, bgUV).rgb, 1.0);
}