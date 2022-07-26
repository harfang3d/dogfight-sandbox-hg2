// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.

// DO NOT MODIFY THIS FILE!

#include <bgfx_shader.sh>

#define PI 3.14159265359

uniform vec4 uClock; // clock

// Environment
uniform vec4 uFogColor;
uniform vec4 uFogState; // fog_near, 1.0/fog_range

// Lighting environment
uniform vec4 uAmbientColor;

uniform vec4 uLightPos[8]; // pos.xyz, 1.0/radius
uniform vec4 uLightDir[8]; // dir.xyz, inner_rim
uniform vec4 uLightDiffuse[8]; // diffuse.xyz, outer_rim
uniform vec4 uLightSpecular[8]; // specular.xyz, pssm_bias

uniform mat4 uLinearShadowMatrix[4]; // slot 0: linear PSSM shadow matrices
uniform vec4 uLinearShadowSlice; // slot 0: PSSM slice distances linear light
uniform mat4 uSpotShadowMatrix; // slot 1: spot shadow matrix
uniform vec4 uShadowState; // slot 0: inverse resolution, slot1: inverse resolution, slot0: bias, slot1: bias

uniform vec4 uResolution; // xy: backbuffer resolution
uniform vec4 uProjection;
uniform mat4 uMainProjection; // projection for the main render (used by screenspace post-processes)
uniform mat4 uMainInvProjection; // inverse projection for the main render (used by screenspace post-processes)

uniform mat4 uPreviousViewProjection;
uniform mat4 uPreviousModel[BGFX_CONFIG_MAX_BONES];
uniform mat4 uViewProjUnjittered;
uniform vec4 uAAAParams[3]; // [0].x: ssgi ratio, [0].y: ssr ratio, [0].z: temporal AA weight, [0].w: motion blur strength,
							// [1].x: exposure, [1].y: 1/gamma, [1].z: sample count, [1].w: screenspace ray max length
							// [2].x: specular weight, [2].y: sharpen

uniform mat4 uMainInvView; // inversion view matrix
uniform mat4 uProbeMatrix;
uniform mat4 uInvProbeMatrix;
uniform vec4 uProbeData;

/*
	Reserved texture units for the AAA forward pipeline.
	Do not modify these slots, they are hardcoded on the C++ side.

	If reserving new slots for the pipeline please keep in mind WebGL limitations: https://webglreport.com/?v=2
	At the moment it is not advisable to use texture units beyond 16 for embedded platforms.
*/
SAMPLERCUBE(uIrradianceMap, 8);
SAMPLERCUBE(uRadianceMap, 9);
SAMPLER2D(uSSIrradianceMap, 10);
SAMPLER2D(uSSRadianceMap, 11);
SAMPLER2D(uBrdfMap, 12);
SAMPLER2D(uNoiseMap, 13);
SAMPLER2DSHADOW(uLinearShadowMap, 14);
SAMPLER2DSHADOW(uSpotShadowMap, 15);

//
float sRGB2linear(float v) {
	return (v < 0.04045) ? (v * 0.0773993808) : pow((v + 0.055) / 1.055, 2.4);
}

vec3 sRGB2linear(vec3 v) {
	return vec3(sRGB2linear(v.x), sRGB2linear(v.y), sRGB2linear(v.z));
}

//
mat3 MakeMat3(vec3 c0, vec3 c1, vec3 c2) {
	return mat3(c0, c1, c2);
}

vec3 GetT(mat4 m) { 
#if BGFX_SHADER_LANGUAGE_GLSL
	return vec3(m[3][0], m[3][1], m[3][2]);
#else
	return vec3(m[0][3], m[1][3], m[2][3]);
#endif
}

float LinearDepth(float z) {
	return uProjection.w / (z - uProjection.z);
}

// from screen space to view space
vec3 Unproject(vec3 frag_coord) {
	vec4 clip = vec4(((frag_coord.xy - u_viewRect.xy) / u_viewRect.zw) * 2. - 1., frag_coord.z, 1.);
	vec4 ndc = mul(clip, uMainInvProjection);
	return ndc.xyz / ndc.w;
}

vec3 ComputeFragCoordViewRay(vec2 frag_coord) {
	vec2 sp = ((frag_coord - u_viewRect.xy) / u_viewRect.zw) * 2. - 1.;
	sp.y *= -1.;

	vec4 ndc = mul(uMainInvProjection, vec4(sp, 1., 1.)); // far ndc frustum plane
	ndc /= ndc.w;
	ndc /= ndc.z;

	return ndc.xyz;
}

bool isNan(float val) { return (val <= 0.0 || 0.0 <= val) ? false : true; }

//
vec2 RaySphere(vec3 r0, vec3 rd, vec3 s0, float sr) {
	float a = dot(rd, rd);
	vec3 s0_r0 = r0 - s0;

	float b = 2.0 * dot(rd, s0_r0);
	float c = dot(s0_r0, s0_r0) - (sr * sr);
	float disc = b * b - 4.0 * a* c;

	if (disc < 0.0)
		return vec2(-1.0, -1.0);

	return vec2(-b - sqrt(disc), -b + sqrt(disc)) / (2.0 * a);
}

vec3 RayBox(vec3 ray_origin, vec3 ray_dir, vec3 minpos, vec3 maxpos) {
	vec3 inverse_dir = 1.0 / ray_dir;
	vec3 tbot = inverse_dir * (minpos - ray_origin);
	vec3 ttop = inverse_dir * (maxpos - ray_origin);
	vec3 tmin = min(ttop, tbot);
	vec3 tmax = max(ttop, tbot);
	vec2 traverse = max(tmin.xx, tmin.yz);
	float traverselow = max(traverse.x, traverse.y);
	traverse = min(tmax.xx, tmax.yz);
	float traversehi = min(traverse.x, traverse.y);
	return vec3(float(traversehi > max(traverselow, 0.0)), traversehi, traverselow);
}

vec3 ReprojectProbe(vec3 O, vec3 V) {
	vec3 W;

	if (uProbeData.x == 0.0) {
		vec3 local_O = mul(uInvProbeMatrix, vec4(O, 1.0)).xyz; // move ray to probe volume space
		vec3 local_V = mul(uInvProbeMatrix, vec4(V, 0.0)).xyz;
		local_V = normalize(local_V);

		vec2 T = RaySphere(local_O, local_V, vec3(0.0, 0.0, 0.0), 0.5);

		if (T.y > -1.0) {
			vec3 local_I = local_O + local_V * T.y;
			W = normalize(mul(uProbeMatrix, vec4(local_I, 0.0)).xyz);
		} else {
			return V;
		}
	} else if (uProbeData.x == 1.0) {
		vec3 local_O = mul(uInvProbeMatrix, vec4(O, 1.0)).xyz; // move ray to probe volume space
		vec3 local_V = mul(uInvProbeMatrix, vec4(V, 0.0)).xyz;
		local_V = normalize(local_V);

		vec3 T = RayBox(local_O, local_V, vec3(-0.5, -0.5, -0.5), vec3(0.5, 0.5, 0.5)); // intersect with volume

		if (T.x == 0.0) {
			return V;
		} else {
			vec3 local_I = local_O + local_V * T.y;
			W = normalize(mul(uProbeMatrix, vec4(local_I, 0.0)).xyz); // move intersection back to world space
		}
	}

	return normalize(mix(V, W, uProbeData.y));
}
