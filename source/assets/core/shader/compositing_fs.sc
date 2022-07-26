$input v_texcoord0

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

SAMPLER2D(u_copyColor, 0);
SAMPLER2D(u_copyDepth, 1);

/*
	tone-mapping operators implementation taken from https://www.shadertoy.com/view/lslGzl
*/

vec3 LinearToneMapping(vec3 color, float exposure) { // 1.
	color = clamp(exposure * color, 0., 1.);
	return color;
}

vec3 SimpleReinhardToneMapping(vec3 color, float exposure) { // 1.5
	color *= exposure / (1. + color / exposure);
	return color;
}

vec3 LumaBasedReinhardToneMapping(vec3 color) {
	float luma = dot(color, vec3(0.2126, 0.7152, 0.0722));
	float toneMappedLuma = luma / (1. + luma);
	color *= toneMappedLuma / luma;
	return color;
}

vec3 WhitePreservingLumaBasedReinhardToneMapping(vec3 color, float white) { // 2.
	float luma = dot(color, vec3(0.2126, 0.7152, 0.0722));
	float toneMappedLuma = luma * (1. + luma / (white * white)) / (1. + luma);
	color *= toneMappedLuma / luma;
	return color;
}

vec3 RomBinDaHouseToneMapping(vec3 color) {
	color = exp(-1. / (2.72 * color + 0.15));
	return color;
}

vec3 FilmicToneMapping(vec3 color) {
	color = max(vec3(0., 0., 0.), color - vec3(0.004, 0.004, 0.004));
	color = (color * (6.2 * color + .5)) / (color * (6.2 * color + 1.7) + 0.06);
	return color;
}

vec3 Uncharted2ToneMapping(vec3 color, float exposure) {
	float A = 0.15;
	float B = 0.50;
	float C = 0.10;
	float D = 0.20;
	float E = 0.02;
	float F = 0.30;
	float W = 11.2;
	color *= exposure;
	color = ((color * (A * color + C * B) + D * E) / (color * (A * color + B) + D * F)) - E / F;
	float white = ((W * (A * W + C * B) + D * E) / (W * (A * W + B) + D * F)) - E / F;
	color /= white;
	return color;
}

vec4 Sharpen(vec2 uv, float strength) {
	vec4 up = texture2D(u_copyColor, uv + vec2(0, 1) / uResolution.xy);
	vec4 left = texture2D(u_copyColor, uv + vec2(-1, 0) / uResolution.xy);
	vec4 center = texture2D(u_copyColor, uv);
	vec4 right = texture2D(u_copyColor, uv + vec2(1, 0) / uResolution.xy);
	vec4 down = texture2D(u_copyColor, uv + vec2(0, -1) / uResolution.xy);

	float exposure = uAAAParams[1].x;
	up.xyz = SimpleReinhardToneMapping(up.xyz, exposure);
	left.xyz = SimpleReinhardToneMapping(left.xyz, exposure);
	center.xyz = SimpleReinhardToneMapping(center.xyz, exposure);
	right.xyz = SimpleReinhardToneMapping(right.xyz, exposure);
	down.xyz = SimpleReinhardToneMapping(down.xyz, exposure);

	vec4 res = (1.0 + 4.0 * strength) * center - strength * (up + left + right + down);
	return vec4(res.xyz, center.w);
}

void main() {
#if 1
	vec4 in_sample = Sharpen(v_texcoord0, uAAAParams[2].y);

	vec3 color = in_sample.xyz;
	float alpha = in_sample.w;
#else
	vec4 in_sample = texture2D(u_copyColor, v_texcoord0);

	vec3 color = in_sample.xyz;
	float alpha = in_sample.w;

	float exposure = uAAAParams[1].x;
	color = SimpleReinhardToneMapping(color, exposure);
	//color = lumaBasedReinhardToneMapping(color);
	//color = FilmicToneMapping(color);
	//color = Uncharted2ToneMapping(color, exposure);
#endif

	// gamma correction
	float inv_gamma = uAAAParams[1].y;
	color = pow(color, vec3_splat(inv_gamma));

	gl_FragColor = vec4(color, alpha);
	gl_FragDepth = texture2D(u_copyDepth, v_texcoord0).r;
}
