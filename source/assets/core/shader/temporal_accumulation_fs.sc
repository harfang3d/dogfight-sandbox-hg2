$input vTexCoord0

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

SAMPLER2D(u_current, 0);
SAMPLER2D(u_previous, 1);
SAMPLER2D(u_attr1, 2);

#include <aaa_utils.sh>

vec2 GetVelocityVector(in vec2 uv, vec2 ratio) {
#if BGFX_SHADER_LANGUAGE_GLSL
	const vec2 offset = vec2(0.5, 0.5);
#else
	const vec2 offset = vec2(0.5, -0.5);
#endif
	return texture2D(u_attr1, uv).xy * offset * ratio / (uResolution.xy / u_viewRect.zw);
}

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);

    vec2 input_size = vec2(textureSize(u_previous, 0));
	vec2 uv = gl_FragCoord.xy / input_size;
	vec2 dt = GetVelocityVector(uv, uResolution.xy / input_size.xy);

	vec2 uv_curr = GetAttributeTexCoord(vTexCoord0, vec2(textureSize(u_current, 0).xy));
	vec4 current = texture2D(u_current, uv_curr);
	 
    vec4 c0 = texture2DLodOffset(u_current, uv_curr, 0, ivec2(0, 1));
	vec4 c1 = texture2DLodOffset(u_current, uv_curr, 0, ivec2(0, -1));
	vec4 c2 = texture2DLodOffset(u_current, uv_curr, 0, ivec2(1, 0));
	vec4 c3 = texture2DLodOffset(u_current, uv_curr, 0, ivec2(-1, 0));
    vec4 neighbour_min = min(min(c0, c1), min(c2, c3));
    vec4 neighbour_max = max(max(c0, c1), max(c2, c3));

    vec4 previous = clamp(texture2D(u_previous, uv - dt, 0), neighbour_min, neighbour_max);
    gl_FragColor = mix(previous, current, uAAAParams[0].z);
}
