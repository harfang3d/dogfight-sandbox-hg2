$input a_position, a_texcoord0
$output vTexCoord0, v_viewRay

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

void main() {
	gl_Position = mul(u_viewProj, vec4(a_position.xy, 0.0, 1.0));

	vec2 sp = a_position.xy * 2. - 1.;
	sp.y *= -1.;

	vec4 ndc = mul(uMainInvProjection, vec4(sp, 1., 1.)); // far ndc frustum plane
	ndc /= ndc.w;
	ndc /= ndc.z;

	v_viewRay = ndc.xyz;

	vTexCoord0 = a_texcoord0;
}
