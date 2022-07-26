$input v_texcoord0

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

SAMPLER2D(u_source, 0);
uniform vec4 u_source_rect;
uniform vec4 u_params;

vec2 compute_texel(vec2 uv, vec2 center, vec4 bounds) {
	vec4 w = vec4(step(bounds.xy, uv), step(uv, bounds.zw));
	return mix(center, uv, vec2(w.x*w.z, w.y*w.w));
}

void main() {
	vec2 uv = v_texcoord0.xy;
	vec4 offset = vec4(-1., 1., 1., 0.) / uResolution.xxyy;

	vec2 center = (floor(v_texcoord0.xy * uResolution.xy) + vec2_splat(0.5)) / uResolution.xy;
	vec4 bounds = (floor(u_source_rect.xyzw) + vec4(1.,1.,-1.,-1.)) / uResolution.xyxy;

	vec4 t0 = texture2D(u_source, compute_texel(uv - offset.yz, center, bounds)); // -1,-1
	vec4 t1 = texture2D(u_source, compute_texel(uv - offset.wz, center, bounds)); //  0,-1
	vec4 t2 = texture2D(u_source, compute_texel(uv - offset.xz, center, bounds)); //  1,-1

	vec4 t3 = texture2D(u_source, compute_texel(uv + offset.xw, center, bounds)); // -1, 0
	vec4 t4 = texture2D(u_source, compute_texel(uv, center, bounds));
	vec4 t5 = texture2D(u_source, compute_texel(uv + offset.yw, center, bounds)); //  1, 0

	vec4 t6 = texture2D(u_source, compute_texel(uv + offset.xz, center, bounds)); // -1, 1
	vec4 t7 = texture2D(u_source, compute_texel(uv + offset.wz, center, bounds)); //  0, 1
	vec4 t8 = texture2D(u_source, compute_texel(uv + offset.yz, center, bounds)); //  1, 1

	gl_FragColor = u_params.z * (t0 + t2 + t6 + t8 + 2. * (t1 + t3 + t5 + t7) + 4. * t4) / 16.;
}
