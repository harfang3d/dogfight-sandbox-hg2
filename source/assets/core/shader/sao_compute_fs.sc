$input v_viewRay

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

SAMPLER2D(u_attr0, 0);
SAMPLER2D(u_attr1, 1);
SAMPLER2D(u_noise, 2);

uniform vec4 u_params[2];

#define u_radius u_params[1].x
#define u_sample_count floatBitsToUint(u_params[1].w)
#define u_distance_scale u_params[1].y
#define u_bias u_params[1].z

vec3 pick(int index, vec4 jitter) {
	float alpha = (float(index) + jitter.x) / float(u_sample_count);
	float theta = (3.141592 * 2.) * (float(index) + jitter.y) / float(u_sample_count);
	return vec3(cos(theta) * jitter.z, sin(theta) * jitter.z, alpha);
}

void main() {
	//
	ivec2 pos = ivec2(gl_FragCoord.xy);

	vec4 jitter = texture2D(u_noise, mod(gl_FragCoord.xy, vec2(64, 64)) / vec2(64, 64));

	vec2 attr0_size = vec2(textureSize(u_attr0, 0).xy);

	// view space fragment coord
	vec2 uv = gl_FragCoord.xy / attr0_size;
	vec4 attr0 = texture2D(u_attr0, uv);

	vec3 c = v_viewRay * attr0.w;
	vec3 n = attr0.xyz;

	//
	float epsilon = 0.001;
	float radius2 = u_radius * u_radius;
	float projected_disc_radius = u_radius * u_distance_scale / c.z;

	float ao = 0.;

	for(int i = 0; i < u_sample_count; ++i) {
		vec3 q_offset = pick(i, jitter);
		q_offset.z = max(1., q_offset.z * projected_disc_radius);

		vec2 q_coord = gl_FragCoord.xy + q_offset.xy * q_offset.z;

		if (any(lessThan(q_coord, u_viewRect.xy)) || any(greaterThan(q_coord, u_viewRect.xy + u_viewRect.zw))) {
			ao += 1.;
		} else {
			vec2 q_uv = q_coord / attr0_size;
			float q_z = texture2D(u_attr0, q_uv).w;

			vec3 q = ComputeFragCoordViewRay(q_coord) * q_z;

			//
			vec3 v = q - c;

			float vv = dot(v, v);
			float vn = dot(v, n);

			float falloff = max(radius2 - vv, 0.);

			ao += falloff * falloff * falloff * max(0., (vn - u_bias) / (epsilon + vv));
		}
	}

	ao = max(0., 1. - 0.7 * ao * (5. / float(u_sample_count)) / (radius2 * radius2 * radius2));

	gl_FragColor = vec4(ao, ao, ao, ao);
}
