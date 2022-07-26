$input v_texcoord0

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

SAMPLER2D(u_attr0, 0);
SAMPLER2D(u_input, 1);

#define KERNEL_RADIUS 16

uniform vec4 u_params[2];

#define u_offset u_params[0].xy
#define u_direction u_params[0].zw
#define u_sharpness u_params[1].x

float compute_weight(float r, float z0, float z) {
	float sigma = float(KERNEL_RADIUS) * 0.5 + 0.5;
	float falloff = 1.0 / (2.0 * sigma * sigma);
	float delta = (z - z0) *  u_sharpness;
	return exp2(-r*r*falloff - delta*delta);
}

void main() {
	float epsilon = 0.0001;

	vec2 center = vec2(texture2D(u_attr0, v_texcoord0).w, LinearDepth(texture2D(u_input, v_texcoord0).r));
			
	vec2 acc = vec2(center.x, 1.0);
	for(int i=1; i<=KERNEL_RADIUS/2; i++) {
		vec2 p = v_texcoord0 + float(i) * u_direction;
		vec2 current = vec2(texture2D(u_attr0, p).w, LinearDepth(texture2D(u_input, p).r));
		float weight = compute_weight(float(i), current.y, center.y);
		acc += vec2(current.x*weight, weight);

		p = v_texcoord0 - float(i) * u_direction;
		current = vec2(texture2D(u_attr0, p).w, LinearDepth(texture2D(u_input, p).r));
		weight = compute_weight(float(i), current.y, center.y);
		acc += vec2(current.x*weight, weight);
	}
	for(int i=KERNEL_RADIUS/2 + 1; i<=KERNEL_RADIUS; i+=2) {
		vec2 p = v_texcoord0 + float(i) * u_direction;
		vec2 current = vec2(texture2D(u_attr0, p).w, LinearDepth(texture2D(u_input, p).r));
		float weight = compute_weight(float(i), current.y, center.y);
		acc += vec2(current.x*weight, weight);

		p = v_texcoord0 - float(i) * u_direction;
		current = vec2(texture2D(u_attr0, p).w, LinearDepth(texture2D(u_input, p).r));
		weight = compute_weight(float(i), current.y, center.y);
		acc += vec2(current.x*weight, weight);
	}
	float ao = acc.x / (acc.y + epsilon);
	gl_FragColor = vec4(ao, ao, ao, 1.0);
}
