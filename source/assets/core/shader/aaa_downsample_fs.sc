// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

SAMPLER2D(u_color, 0);
SAMPLER2D(u_attr0, 1);
SAMPLER2D(u_depth, 2);

void main() {
    ivec2 pos = ivec2(gl_FragCoord.xy) * 2;
    
    vec4 v0 = texelFetchOffset(u_attr0, pos, 0, ivec2(0,0));
    vec4 v1 = texelFetchOffset(u_attr0, pos, 0, ivec2(1,0));
    vec4 v2 = texelFetchOffset(u_attr0, pos, 0, ivec2(0,1));
    vec4 v3 = texelFetchOffset(u_attr0, pos, 0, ivec2(1,1));

    vec4 c0 = texelFetchOffset(u_color, pos, 0, ivec2(0,0));
    vec4 c1 = texelFetchOffset(u_color, pos, 0, ivec2(1,0));
    vec4 c2 = texelFetchOffset(u_color, pos, 0, ivec2(0,1));
    vec4 c3 = texelFetchOffset(u_color, pos, 0, ivec2(1,1));

    vec4 z0 = texelFetchOffset(u_depth, pos, 0, ivec2(0,0));
    vec4 z1 = texelFetchOffset(u_depth, pos, 0, ivec2(1,0));
    vec4 z2 = texelFetchOffset(u_depth, pos, 0, ivec2(0,1));
    vec4 z3 = texelFetchOffset(u_depth, pos, 0, ivec2(1,1));

    vec2 tmp = floor(mod(gl_FragCoord.xy, 2.0));
#if AAA_DOWNSAMPLE_CHECKERBOARD
    float checkerboard = tmp.x + tmp.y - 2.0*tmp.x*tmp.y;

    vec4 v_min = (v0.w < v1.w) ? v0 : v1;
    vec4 c_min = (v0.w < v1.w) ? c0 : c1;
    vec4 z_min = (v0.w < v1.w) ? z0 : z1;
    vec4 v_max = (v0.w > v1.w) ? v0 : v1;
    vec4 c_max = (v0.w > v1.w) ? c0 : c1;
    vec4 z_max = (v0.w > v1.w) ? z0 : z1;
    
    v_min = (v_min.w < v2.w) ? v_min : v2;
    c_min = (v_min.w < v2.w) ? c_min : c2;
    z_min = (v_min.w < v2.w) ? z_min : z2;
    v_max = (v_max.w > v2.w) ? v_max : v2;
    c_max = (v_max.w > v2.w) ? c_max : c2;
    z_max = (v_max.w > v2.w) ? z_max : z2;

    v_min = (v_min.w < v3.w) ? v_min : v3; // mix(v_min, v3, step(v_min.w, v3.w));
    c_min = (v_min.w < v3.w) ? c_min : c3;
    z_min = (v_min.w < v3.w) ? z_min : z3;
    v_max = (v_max.w > v3.w) ? v_max : v3; // mix(v_max, v3, step(v3.w, v_max.w));
    c_max = (v_max.w > v3.w) ? c_max : c3;
    z_max = (v_max.w > v3.w) ? z_max : z3;

    gl_FragData[0] = mix(c_min, c_max, checkerboard);
    gl_FragData[1] = mix(v_min, v_max, checkerboard);
    gl_FragData[2] = mix(z_min, z_max, checkerboard);
#else
    vec4 v_min = (v0.w < v1.w) ? v0 : v1;
    vec4 c_min = (v0.w < v1.w) ? c0 : c1;
    vec4 z_min = (v0.w < v1.w) ? z0 : z1;
    
    v_min = (v_min.w < v2.w) ? v_min : v2;
    c_min = (v_min.w < v2.w) ? c_min : c2;
    z_min = (v_min.w < v2.w) ? z_min : z2;
    
    v_min = (v_min.w < v3.w) ? v_min : v3;
    c_min = (v_min.w < v3.w) ? c_min : c3;
    z_min = (v_min.w < v3.w) ? z_min : z3;
    
    gl_FragData[0] = c_min;
    gl_FragData[1] = v_min;
    gl_FragData[2] = z_min;
#endif
}