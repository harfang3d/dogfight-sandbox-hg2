// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

SAMPLER2D(u_color, 0);
SAMPLER2D(u_prv_color, 1);
SAMPLER2D(u_attr0, 2);
SAMPLER2D(u_attr1, 3);

#include <aaa_utils.sh>

#define AABB_CLAMPING 0
#define AABB_CLAMPING_FAST 1
#define VARIANCE_CLIPPING_GAMMA 0 // https://community.arm.com/developer/tools-software/graphics/b/blog/posts/temporal-anti-aliasing
#define LUMINANCE_AJDUST 1

void main() {
	vec2 uv = gl_FragCoord.xy / uResolution.xy;

	// current contribution
	vec3 color = texture2D(u_color, uv).xyz;

	// fetch velocity to reproject history onto the current frame
	vec2 dt = GetVelocityVector(uv);

	// fetch history contribution
	vec3 prv_color = texture2D(u_prv_color, uv - dt).xyz;

	// reject invalid sample
#if AABB_CLAMPING
	vec3 neighbors[9];

	neighbors[0] = texture2D(u_color, uv + vec2(-1, -1) / uResolution.xy).xyz;
	neighbors[1] = texture2D(u_color, uv + vec2( 0, -1) / uResolution.xy).xyz;
	neighbors[2] = texture2D(u_color, uv + vec2( 1, -1) / uResolution.xy).xyz;
	neighbors[3] = texture2D(u_color, uv + vec2(-1,  0) / uResolution.xy).xyz;
	neighbors[4] = color;
	neighbors[5] = texture2D(u_color, uv + vec2( 1,  0) / uResolution.xy).xyz;
	neighbors[6] = texture2D(u_color, uv + vec2(-1,  1) / uResolution.xy).xyz;
	neighbors[7] = texture2D(u_color, uv + vec2( 0,  1) / uResolution.xy).xyz;
	neighbors[8] = texture2D(u_color, uv + vec2( 1,  1) / uResolution.xy).xyz;

	vec3 nmin = neighbors[0];
	vec3 nmax = neighbors[0];

	for(int i = 1; i < 9; ++i) {
		nmin = min(nmin, neighbors[i]);
		nmax = max(nmax, neighbors[i]);
	}

	prv_color = clamp(prv_color, nmin, nmax);
#endif

#if AABB_CLAMPING_FAST
	vec3 c0 = texture2D(u_color, uv + vec2( 1,  0) / uResolution.xy).xyz;
	vec3 c1 = texture2D(u_color, uv + vec2( 0,  1) / uResolution.xy).xyz;
	vec3 c2 = texture2D(u_color, uv + vec2(-1,  0) / uResolution.xy).xyz;
	vec3 c3 = texture2D(u_color, uv + vec2( 0, -1) / uResolution.xy).xyz;

	vec3 box_min = min(color, min(c0, min(c1, min(c2, c3))));
	vec3 box_max = max(color, max(c0, max(c1, max(c2, c3))));;

	prv_color = clamp(prv_color, box_min, box_max);
#endif

#if VARIANCE_CLIPPING_GAMMA
	float clipping_gamma = 2.2;

	vec3 c0 = texture2D(u_color, uv + vec2( 1,  0) / uResolution.xy).xyz;
	vec3 c1 = texture2D(u_color, uv + vec2( 0,  1) / uResolution.xy).xyz;
	vec3 c2 = texture2D(u_color, uv + vec2(-1,  0) / uResolution.xy).xyz;
	vec3 c3 = texture2D(u_color, uv + vec2( 0, -1) / uResolution.xy).xyz;

	// Compute the two moments
	vec3 M1 = color + c0 + c1 + c2 + c3;
	vec3 M2 = color * color + c0 * c0 + c1 * c1 + c2 * c2 + c3 * c3;

	vec3 MU = M1 / 5.;
	vec3 Sigma = sqrt(M2 / 5. - MU * MU);

	vec3 box_min = MU - clipping_gamma * Sigma;
	vec3 box_max = MU + clipping_gamma * Sigma;

	prv_color = clamp(prv_color, box_min, box_max);
#endif

#if LUMINANCE_AJDUST
	const vec3 luminance = vec3(0.2127, 0.7152, 0.0722);

	float l0 = dot(luminance, prv_color);
	float l1 = dot(luminance, color);

	float w1 = (uAAAParams[0].z) / (1.0 + l1);
	float w0 = (1.0 - uAAAParams[0].z) / (1.0 + l0);

	vec3 taa_out = (w1 * color + w0 * prv_color) / max(w0 + w1, 0.00001);
	gl_FragColor = vec4(taa_out, 1.);
#else
	// TAA
	vec3 taa_out = color * uAAAParams[0].z + prv_color * (1. - uAAAParams[0].z);
	gl_FragColor = vec4(taa_out, 1.);
#endif
}
