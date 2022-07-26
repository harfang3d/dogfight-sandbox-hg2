$input vWorldPos, vNormal, vTangent, vBinormal, vTexCoord0, vTexCoord1, vLinearShadowCoord0, vLinearShadowCoord1, vLinearShadowCoord2, vLinearShadowCoord3, vSpotShadowCoord, vProjPos, vPrevProjPos

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

// Surface attributes
uniform vec4 uDiffuseColor;
uniform vec4 uSpecularColor;
uniform vec4 uSelfColor;

// Texture slots
SAMPLER2D(uDiffuseMap, 0); // PBR metalness in alpha
SAMPLER2D(uSpecularMap, 1); // PBR roughness in alpha
SAMPLER2D(uNormalMap, 2); // Parallax mapping elevation in alpha
SAMPLER2D(uLightMap, 3);
SAMPLER2D(uSelfMap, 4);
SAMPLER2D(uOpacityMap, 5);
SAMPLER2D(uAmbientMap, 6);
SAMPLER2D(uReflectionMap, 7);

//
struct LightModelOut {
	float i_diff;
	float i_spec;
};

// Forward Phong
LightModelOut PhongLightModel(vec3 V, vec3 N, vec3 R, vec3 L, float gloss) {
	LightModelOut m;
	m.i_diff = max(-dot(L, N), 0.0);
	m.i_spec = pow(max(-dot(L, R), 0.0), gloss);
	return m;
}

float LightAttenuation(vec3 L, vec3 D, float dist, float attn, float inner_rim, float outer_rim) {
	float k = 1.0;
	if (attn > 0.0)
		k = max(1.0 - dist * attn, 0.0); // distance attenuation

	if (outer_rim > 0.0) {
		float c = dot(L, D);
		k *= clamp(1.0 - (c - inner_rim) / (outer_rim - inner_rim), 0.0, 1.0); // spot attenuation
	}
	return k;
}

//
vec3 DistanceFog(vec3 pos, vec3 color) {
	if (uFogState.y == 0.0)
		return color;

	float k = clamp((pos.z - uFogState.x) * uFogState.y, 0.0, 1.0);
	return mix(color, uFogColor.xyz, k);
}

float SampleHardShadow(sampler2DShadow map, vec4 coord, float bias) {
	vec3 uv = coord.xyz / coord.w;
	return shadow2D(map, vec3(uv.xy, uv.z - bias));
}

float SampleShadowPCF(sampler2DShadow map, vec4 coord, float inv_pixel_size, float bias) {
	float k_pixel_size = inv_pixel_size * coord.w;

	float k = 0.0;

	k += SampleHardShadow(map, coord + vec4(vec2(-0.5, -0.5) * k_pixel_size, 0.0, 0.0), bias);
	k += SampleHardShadow(map, coord + vec4(vec2( 0.5, -0.5) * k_pixel_size, 0.0, 0.0), bias);
	k += SampleHardShadow(map, coord + vec4(vec2(-0.5,  0.5) * k_pixel_size, 0.0, 0.0), bias);
	k += SampleHardShadow(map, coord + vec4(vec2( 0.5,  0.5) * k_pixel_size, 0.0, 0.0), bias);

	return k / 4.0;
}

// Entry point of the forward pipeline default shader
void main() {
#if DEPTH_ONLY != 1
#if USE_DIFFUSE_MAP
#if DIFFUSE_UV_CHANNEL == 1
	vec3 diff = texture2D(uDiffuseMap, vTexCoord1).xyz;
#else // DIFFUSE_UV_CHANNEL == 1
	vec3 diff = texture2D(uDiffuseMap, vTexCoord0).xyz;
#endif // DIFFUSE_UV_CHANNEL == 1
#else // USE_DIFFUSE_MAP
	vec3 diff = uDiffuseColor.xyz;
#endif // USE_DIFFUSE_MAP

#if USE_SPECULAR_MAP
#if SPECULAR_UV_CHANNEL == 1
	vec3 spec = texture2D(uSpecularMap, vTexCoord1).xyz;
#else // SPECULAR_UV_CHANNEL == 1
	vec3 spec = texture2D(uSpecularMap, vTexCoord0).xyz;
#endif // SPECULAR_UV_CHANNEL == 1
#else // USE_SPECULAR_MAP
	vec3 spec = uSpecularColor.xyz;
#endif // USE_SPECULAR_MAP

#if USE_SELF_MAP
	vec3 self = texture2D(uSelfMap, vTexCoord0).xyz;
#else // USE_SELF_MAP
	vec3 self = uSelfColor.xyz;
#endif // USE_SELF_MAP

#if USE_AMBIENT_MAP
#if AMBIENT_UV_CHANNEL == 1
	vec3 ao = texture2D(uAmbientMap, vTexCoord1).xyz;
#else // AMBIENT_UV_CHANNEL == 1
	vec3 ao = texture2D(uAmbientMap, vTexCoord0).xyz;
#endif // AMBIENT_UV_CHANNEL == 1
#else // USE_AMBIENT_MAP
	vec3 ao = vec3_splat(1.0);
#endif // USE_AMBIENT_MAP

#if USE_ADVANCED_BUFFERS
	ao *= texture2D(uAmbientOcclusion, gl_FragCoord.xy / uResolution.xy).x;
#endif // USE_ADVANCED_BUFFERS

#if USE_LIGHT_MAP
	vec3 light = texture2D(uLightMap, vTexCoord1).xyz;
#else // USE_LIGHT_MAP
	vec3 light = vec3_splat(0.0);
#endif // USE_LIGHT_MAP

	//
	vec3 view = mul(u_view, vec4(vWorldPos,1.0)).xyz; // fragment view space pos
	vec3 P = vWorldPos; // fragment world pos
	vec3 V = normalize(GetT(u_invView) - P); // view vector
	vec3 N = normalize(vNormal); // geometry normal

#if USE_NORMAL_MAP
	vec3 T = normalize(vTangent);
	vec3 B = normalize(vBinormal);

	mat3 TBN = MakeMat3(T, B, N);

	N.xy = texture2D(uNormalMap, vTexCoord0).xy * 2.0 - 1.0;
	N.z = sqrt(1.0 - dot(N.xy, N.xy));
	N = normalize(mul(N, TBN));
#endif // USE_NORMAL_MAP

	vec3 R = reflect(-V, N); // view reflection vector around normal

	float gloss = 64.0 / uSpecularColor.w;

	// SLOT 0: linear light
	vec3 c_diff, c_spec;

	{
		LightModelOut m = PhongLightModel(V, N, R, uLightDir[0].xyz, gloss);

		float k = 1.0;
#if SLOT0_SHADOWS
		if(view.z < uLinearShadowSlice.x) {
			k *= SampleShadowPCF(uLinearShadowMap, vLinearShadowCoord0, uShadowState.y * 0.5, uShadowState.z);
		}
		else if(view.z < uLinearShadowSlice.y) {
			k *= SampleShadowPCF(uLinearShadowMap, vLinearShadowCoord1, uShadowState.y * 0.5, uShadowState.z);
		}
		else if(view.z < uLinearShadowSlice.z) {
			k *= SampleShadowPCF(uLinearShadowMap, vLinearShadowCoord2, uShadowState.y * 0.5, uShadowState.z);
		}
		else if(view.z < uLinearShadowSlice.w) {
			float pcf = SampleShadowPCF(uLinearShadowMap, vLinearShadowCoord3, uShadowState.y * 0.5, uShadowState.z);
			float ramp_len = (uLinearShadowSlice.w - uLinearShadowSlice.z) * 0.25;
			float ramp_k = clamp((view.z - (uLinearShadowSlice.w - ramp_len)) / ramp_len, 0.0, 1.0);
			k *= pcf * (1.0 - ramp_k) + ramp_k; 
		}
#endif // SLOT0_SHADOWS
		c_diff = uLightDiffuse[0].xyz * m.i_diff * k;
		c_spec = uLightSpecular[0].xyz * m.i_spec * k;
	}

	// SLOT 1: point/spot light (with optional shadows)
	{
		vec3 L = P - uLightPos[1].xyz; // incident

		float D = length(L);
		L /= D; // normalize

		LightModelOut m = PhongLightModel(V, N, R, L, gloss);
		float k = LightAttenuation(L, uLightDir[1].xyz, D, uLightPos[1].w, uLightDir[1].w, uLightDiffuse[1].w);

#if SLOT1_SHADOWS
		k *= SampleShadowPCF(uSpotShadowMap, vSpotShadowCoord, uShadowState.y, uShadowState.w);
#endif // SLOT1_SHADOWS

		c_diff += uLightDiffuse[1].xyz * m.i_diff * k;
		c_spec += uLightSpecular[1].xyz * m.i_spec * k;
	}

	// SLOT 2-N: point/spot light (no shadows)
	for (int i = 2; i < 8; ++i) {
		vec3 L = P - uLightPos[i].xyz; // incident

		float D = length(L);
		L /= D; // normalize

		LightModelOut m = PhongLightModel(V, N, R, L, gloss);
		float k = LightAttenuation(L, uLightDir[i].xyz, D, uLightPos[i].w, uLightDir[i].w, uLightDiffuse[i].w);

		c_diff += uLightDiffuse[i].xyz * m.i_diff * k;
		c_spec += uLightSpecular[i].xyz * m.i_spec * k;
	}

	c_diff += uAmbientColor.xyz * ao.xyz;

	vec3 color = diff * (c_diff + light) + spec * c_spec + self;

#if USE_REFLECTION_MAP
	vec4 reflection = texture2D(uReflectionMap, R.xy);
	color += reflection.xyz;
#endif // USE_REFLECTION_MAP

	color = DistanceFog(view, color);
#endif // DEPTH_ONLY != 1

#if USE_OPACITY_MAP
	float opacity = texture2D(uOpacityMap, vTexCoord0).x;

#if ENABLE_ALPHA_CUT
	if (opacity < 0.8)
		discard;
#endif // ENABLE_ALPHA_CUT
#else // USE_OPACITY_MAP
	float opacity = 1.0;
#endif // USE_OPACITY_MAP

#if DEPTH_ONLY != 1
#if FORWARD_PIPELINE_AAA_PREPASS
	vec3 N_view = mul(u_view, vec4(N, 0)).xyz;
	vec2 velocity = vec2(vProjPos.xy / vProjPos.w - vPrevProjPos.xy / vPrevProjPos.w);
	gl_FragData[0] = vec4(N_view.xyz, vProjPos.z);
	gl_FragData[1] = vec4(velocity.xy, gloss, 0.); //
#else // FORWARD_PIPELINE_AAA_PREPASS
	// incorrectly apply gamma correction at fragment shader level in the non-AAA pipeline
#if FORWARD_PIPELINE_AAA != 1
	float gamma = 2.2;
	color = pow(color, vec3_splat(1. / gamma));
#endif // FORWARD_PIPELINE_AAA != 1

	gl_FragColor = vec4(color, opacity);
#endif // FORWARD_PIPELINE_AAA_PREPASS
#else
	gl_FragColor = vec4_splat(0.0); // note: fix required to stop glsl-optimizer from removing the whole function body
#endif // DEPTH_ONLY
}
