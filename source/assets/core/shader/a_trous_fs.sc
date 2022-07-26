// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

SAMPLER2D(u_color, 0);
SAMPLER2D(u_attr0, 1);

uniform vec4 u_dir;
uniform vec4 u_sigma; // x: pos, y: normal, z: depth, w: depth weight cutoff

void main() {
    const float epsilon = 1.e-6;

    ivec2 p0 = ivec2(gl_FragCoord.xy);
    ivec2 offset = ivec2(u_dir.xy);

    vec4 c0 = texelFetch(u_color, p0, 0);
    vec4 v0 = texelFetch(u_attr0, p0, 0);

    float w = 3.0 / 8.0;
    vec4 c = w * c0;

    float falloff = 1.0 / (sqrt(2.0) * u_sigma.x);

    int i;
    float ws;
    
    ws = 1.0 / 4.0;
    for(i=1; i<=2; i++) {
        ivec2 p1;
        vec4 v1;
        float wn, dz, wz, wp, w1, d;

        ivec2 delta = offset * i;
        float d2 = dot(vec2(delta), vec2(delta));
        wp = exp(-d2 * falloff);

        // right
        p1 = p0 + delta;
        v1 = texelFetch(u_attr0, p1, 0);

        dz = abs(v1.w - v0.w);
        wz = exp(-dz / u_sigma.z);
        wz *= step(u_sigma.w, wz);

        wn = pow(max(0.0, dot(v1.xyz, v0.xyz)), u_sigma.y);
        w1 = ws * wn * wz * wp;

        w += w1;
        c += w1 * texelFetch(u_color, p1, 0);

        // left
        p1 = p0 - delta;
        v1 = texelFetch(u_attr0, p1, 0);

        dz = abs(v1.w - v0.w);
        wz = exp(-dz / u_sigma.z);
        wz *= step(u_sigma.w, wz);

        wn = pow(max(0.0, dot(v1.xyz, v0.xyz)), u_sigma.y);
        w1 = ws * wn * wz * wp;

        w += w1;
        c += w1 * texelFetch(u_color, p1, 0);

        ws *= ws;
    } 

    gl_FragColor = c / w;
}