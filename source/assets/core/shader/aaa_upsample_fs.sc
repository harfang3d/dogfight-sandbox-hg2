// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

SAMPLER2D(u_input, 0);
SAMPLER2D(u_attr_lo, 1);
SAMPLER2D(u_attr_hi, 2);

float gaussian(float v, float sigma) {
    return exp(-(v*v)/(2.0*sigma*sigma));
}

void main() {
    vec2 ratio = round(textureSize(u_attr_hi, 0).xy / textureSize(u_attr_lo, 0).xy);
	vec2 pixel = gl_FragCoord.xy / ratio;
    vec2 tmp = floor(pixel-vec2_splat(0.5)) + vec2_splat(0.5);
    ivec2 coord = ivec2(tmp);
    vec2 f = pixel - tmp;

    vec4 in00 = texelFetch(u_input, coord, 0);
    vec4 in01 = texelFetchOffset(u_input, coord, 0, ivec2(0,1));
    vec4 in10 = texelFetchOffset(u_input, coord, 0, ivec2(1,0));
    vec4 in11 = texelFetchOffset(u_input, coord, 0, ivec2(1,1));

    vec4 attr = texelFetch(u_attr_hi, ivec2(gl_FragCoord.xy), 0);

    vec4 attr00 = texelFetch(u_attr_lo, coord, 0);
    vec4 attr01 = texelFetchOffset(u_attr_lo, coord, 0, ivec2(0,1));
    vec4 attr10 = texelFetchOffset(u_attr_lo, coord, 0, ivec2(1,0));
    vec4 attr11 = texelFetchOffset(u_attr_lo, coord, 0, ivec2(1,1));

    // bilinear weights
    vec4 w_b = vec4(
        (1.0-f.x) * (1.0-f.y),
        (1.0-f.x) * f.y,
        f.x * (1.0-f.y),
        f.x * f.y
    );

    // depth weights
    // [todo] use screen space gradient => gaussian(dz, sigma_z * abs(dot(gradient, vec2(i,j))) + epsilon) ? 
    // [todo] gradient => prewitt ?
    float sigma_z = 0.02;
    vec4 d_z = vec4(
        abs(attr.w - attr00.w),
        abs(attr.w - attr01.w),
        abs(attr.w - attr10.w),
        abs(attr.w - attr11.w)
    );
    vec4 w_z = vec4(
        gaussian(d_z.x, sigma_z),
        gaussian(d_z.y, sigma_z),
        gaussian(d_z.z, sigma_z),
        gaussian(d_z.w, sigma_z)
    );
    
    // normal weights
    float sigma_n = 16.0;
    vec4 w_n = vec4(
        pow(max(0.0, dot(attr.xyz, attr00.xyz)), sigma_n),
        pow(max(0.0, dot(attr.xyz, attr01.xyz)), sigma_n),
        pow(max(0.0, dot(attr.xyz, attr10.xyz)), sigma_n),
        pow(max(0.0, dot(attr.xyz, attr11.xyz)), sigma_n)
    );

    // [todo] luminance variance weights?

    vec4 w = w_b * w_z * w_n;
    float w_sum = max(1e-6, w.x + w.y + w.z + w.w);
    vec4 sum = w.x*in00 + w.y*in01 + w.z*in10 + w.w*in11;

    if(abs(w_sum) > 1.e-6) {
        gl_FragColor = sum / w_sum;
    } else {
        // switch to depth aware sampling when the weight is too small.
        if (all(greaterThan(w_z, vec4_splat(0.5)))) {
            gl_FragColor = mix(mix(in00, in10, f.x), mix(in10, in11, f.x), f.y);
        } else {
            vec4 data = in00;
            float d_z_min = d_z.x;
            if (d_z.y < d_z_min) {
                d_z_min = d_z.y;
                data = in01;
            }
            if (d_z.z < d_z_min) {
                d_z_min = d_z.z;
                data = in10;
            }
            if (d_z.w < d_z_min) {
                d_z_min = d_z.w;
                data = in11;
            }
            gl_FragColor = data;
        }
    }
}
