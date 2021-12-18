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
uniform vec4 uAAAParams[2]; // [0].x: ssgi ratio, [0].y: ssr ratio, [0].z: temporal AA weight, [0].w: motion blur strength, [1].x: exposure, [1].y: 1/gamma, [1].z: sample count, [1].w: max radius

uniform mat4 uMainInvView; // inversion view matrix

#if FORWARD_PIPELINE_AAA
SAMPLER2D(uIrradianceMap, 8);
SAMPLER2D(uRadianceMap, 9);
#else
SAMPLERCUBE(uIrradianceMap, 8);
SAMPLERCUBE(uRadianceMap, 9);
#endif
SAMPLER2D(uBrdfMap, 10);
SAMPLER2D(uNoiseMap, 11);
SAMPLER2D(uAmbientOcclusion, 13);
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

vec3 ComputeFragCoordViewRay(vec2 frag_coord)
{
	vec2 sp = ((frag_coord - u_viewRect.xy) / u_viewRect.zw) * 2. - 1.;
	sp.y *= -1.;

	vec4 ndc = mul(uMainInvProjection, vec4(sp, 1., 1.)); // far ndc frustum plane
	ndc /= ndc.w;
	ndc /= ndc.z;

	return ndc.xyz;
}

bool isNan(float val) { return (val <= 0.0 || 0.0 <= val) ? false : true; }
