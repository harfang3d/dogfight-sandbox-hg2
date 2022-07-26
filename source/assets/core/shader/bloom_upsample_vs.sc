$input a_position, a_texcoord0
$output v_texcoord0

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

uniform vec4 u_source_rect;

void main() {
	gl_Position = mul(u_viewProj, vec4(a_position.xy, 0., 1.));
#if BGFX_SHADER_LANGUAGE_GLSL
	v_texcoord0 = mix(vec2(u_source_rect.x, uResolution.y - u_source_rect.w), vec2(u_source_rect.z, uResolution.y - u_source_rect.y), a_texcoord0) / uResolution.xy;
#else
	v_texcoord0 = mix(u_source_rect.xy, u_source_rect.zw, a_texcoord0.xy) / uResolution.xy; // interpolate source rect as UV over primitive
#endif
}
