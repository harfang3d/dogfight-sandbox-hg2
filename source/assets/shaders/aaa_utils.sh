// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#ifndef AAA_UTILS_SH_HEADER_GUARD
#define AAA_UTILS_SH_HEADER_GUARD

#	if !defined(uv_ratio)
#		define uv_ratio vec2_splat(uAAAParams[0].x)
#	endif

vec2 NDCToViewRect(vec2 xy) { return ((xy * 0.5 + 0.5) * u_viewRect.zw + u_viewRect.xy); }

vec2 GetVelocityVector(in vec2 uv) {
#if BGFX_SHADER_LANGUAGE_GLSL
	const vec2 offset = vec2(0.5, 0.5);
#else
	const vec2 offset = vec2(0.5,-0.5);
#endif
	return texture2D(u_attr1, uv).xy * offset / (uResolution.xy / u_viewRect.zw);
}

vec2 GetAttributeTexCoord(vec2 coord, vec2 size) {
#if BGFX_SHADER_LANGUAGE_GLSL
	vec2 uv = vec2(coord.x, 1.0 - coord.y) * u_viewRect.zw / size;
	uv.y = 1.0 - uv.y;
	return uv;
#else
	return coord * u_viewRect.zw / size;
#endif
}

vec3 GetRayOrigin(mat4 projection, vec3 viewRay, float depth) {
#if BGFX_SHADER_LANGUAGE_GLSL
	float z = (depth - projection[3].z) / projection[2].z;
#else
	float z = (depth - projection[2].w) / projection[2].z;
#endif
	return viewRay * z;
}

#endif // AAA_UTILS_SH_HEADER_GUARD
