$input vWorldPos, vNormal, vTangent, vBinormal, vTexCoord0, vTexCoord1, vLinearShadowCoord0, vLinearShadowCoord1, vLinearShadowCoord2, vLinearShadowCoord3, vSpotShadowCoord, vProjPos, vPrevProjPos

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

// Surface attributes
uniform vec4 uBaseOpacityColor;
uniform vec4 uOcclusionRoughnessMetalnessColor;
uniform vec4 uSelfColor;

// Texture slots
SAMPLER2D(uBaseOpacityMap, 0);
SAMPLER2D(uOcclusionRoughnessMetalnessMap, 1);
SAMPLER2D(uNormalMap, 2);
SAMPLER2D(uSelfMap, 4);

//
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

float SampleHardShadow(sampler2DShadow map, vec4 coord, float bias) {
	vec3 uv = coord.xyz / coord.w;
	return shadow2D(map, vec3(uv.xy, uv.z - bias));
}

float SampleShadowPCF(sampler2DShadow map, vec4 coord, float inv_pixel_size, float bias, vec4 jitter) {
	float k_pixel_size = inv_pixel_size * coord.w;

	float k = 0.0;

#if FORWARD_PIPELINE_AAA
	#define PCF_SAMPLE_COUNT 2 // 3x3

//	ARRAY_BEGIN(float, weights, 9) 0.024879, 0.107973, 0.024879, 0.107973, 0.468592, 0.107973, 0.024879, 0.107973, 0.024879 ARRAY_END();
	ARRAY_BEGIN(float, weights, 9) 0.011147, 0.083286, 0.011147, 0.083286, 0.622269, 0.083286, 0.011147, 0.083286, 0.011147 ARRAY_END();

	for (int j = 0; j <= PCF_SAMPLE_COUNT; ++j) {
		float v = 6.0 * (float(j) + jitter.y) / float(PCF_SAMPLE_COUNT) - 1.0;
		for (int i = 0; i <= PCF_SAMPLE_COUNT; ++i) {
			float u = 6.0 * (float(i) + jitter.x) / float(PCF_SAMPLE_COUNT) - 1.0;
			k += SampleHardShadow(map, coord + vec4(vec2(u, v) * k_pixel_size, 0.0, 0.0), bias) * weights[j * 3 + i];
		}
	}
#else // FORWARD_PIPELINE_AAA
	// 2x2
	k += SampleHardShadow(map, coord + vec4(vec2(-0.5, -0.5) * k_pixel_size, 0.0, 0.0), bias);
	k += SampleHardShadow(map, coord + vec4(vec2( 0.5, -0.5) * k_pixel_size, 0.0, 0.0), bias);
	k += SampleHardShadow(map, coord + vec4(vec2(-0.5,  0.5) * k_pixel_size, 0.0, 0.0), bias);
	k += SampleHardShadow(map, coord + vec4(vec2( 0.5,  0.5) * k_pixel_size, 0.0, 0.0), bias);

	k /= 4.0;
#endif // FORWARD_PIPELINE_AAA

	return k;
}

// Forward PBR GGX
float DistributionGGX(float NdotH, float roughness) {
	float a = roughness * roughness;
	float a2 = a * a;

	float divisor = NdotH * NdotH * (a2 - 1.0) + 1.0;
	return a2 / max(PI * divisor * divisor, 1e-8); 
}

float GeometrySchlickGGX(float NdotW, float k) {
	float div = NdotW * (1.0 - k) + k;
	return NdotW / ((abs(div) > 1e-8) ? div : 1e-8);
}

float GeometrySmith(float NdotV, float NdotL, float roughness) {
	float r = roughness + 1.0;
	float k = (r * r) / 8.0;
	float ggx2 = GeometrySchlickGGX(NdotV, k);
	float ggx1 = GeometrySchlickGGX(NdotL, k);
	return ggx1 * ggx2;
}

vec3 FresnelSchlick(float cosTheta, vec3 F0) {
	return F0 + (1.0 - F0) * pow(max(1.0 - cosTheta, 0.0), 5.0);
}

vec3 FresnelSchlickRoughness(float cosTheta, vec3 F0, float roughness) {
	return F0 + (max(vec3_splat(1.0 - roughness), F0) - F0) * pow(max(1.0 - cosTheta, 0.0), 5.0);
}

vec3 GGX(vec3 V, vec3 N, float NdotV, vec3 L, vec3 albedo, float roughness, float metalness, vec3 F0, vec3 diffuse_color, vec3 specular_color) {
	vec3 H = normalize(V - L);

	float NdotH = max(dot(N, H), 0.0);
	float NdotL = max(-dot(N, L), 0.0);
	float HdotV = max(dot(H, V), 0.0);

	float D = DistributionGGX(NdotH, roughness);
	float G = GeometrySmith(NdotV, NdotL, roughness);
	vec3 F = FresnelSchlick(HdotV, F0);

	vec3 specularBRDF = (F * D * G) / max(4.0 * NdotV * NdotL, 0.001);

	vec3 kD = (vec3_splat(1.0) - F) * (1.0 - metalness); // metallic materials have no diffuse (NOTE: mimics mental ray and 3DX Max ART renderers behavior)
	vec3 diffuseBRDF = kD * albedo;

	return (diffuse_color * diffuseBRDF + specular_color * specularBRDF) * NdotL;
}

//
vec3 DistanceFog(vec3 pos, vec3 color) {
	if (uFogState.y == 0.0)
		return color;

	float k = clamp((pos.z - uFogState.x) * uFogState.y, 0.0, 1.0);
	return mix(color, uFogColor.xyz, k);
}

// Entry point of the forward pipeline default uber shader (Phong and PBR)
void main() {
	//
#if USE_BASE_COLOR_OPACITY_MAP
	vec4 base_opacity = texture2D(uBaseOpacityMap, vTexCoord0);
	base_opacity.xyz = sRGB2linear(base_opacity.xyz);
#else // USE_BASE_COLOR_OPACITY_MAP
	vec4 base_opacity = uBaseOpacityColor;
#endif // USE_BASE_COLOR_OPACITY_MAP

#if DEPTH_ONLY != 1
#if USE_OCCLUSION_ROUGHNESS_METALNESS_MAP
	vec4 occ_rough_metal = texture2D(uOcclusionRoughnessMetalnessMap, vTexCoord0);
#else // USE_OCCLUSION_ROUGHNESS_METALNESS_MAP
	vec4 occ_rough_metal = uOcclusionRoughnessMetalnessColor;
#endif // USE_OCCLUSION_ROUGHNESS_METALNESS_MAP

	//
#if USE_SELF_MAP
	vec4 self = texture2D(uSelfMap, vTexCoord0);
#else // USE_SELF_MAP
	vec4 self = uSelfColor;
#endif // USE_SELF_MAP

	//
	vec3 view = mul(u_view, vec4(vWorldPos, 1.0)).xyz;
	vec3 P = vWorldPos; // fragment world pos
	vec3 V = normalize(GetT(u_invView) - P); // world space view vector
	vec3 N = sign(dot(V, vNormal)) * normalize(vNormal); // geometry normal

#if USE_NORMAL_MAP
	vec3 T = normalize(vTangent);
	vec3 B = normalize(vBinormal);

	mat3 TBN = mtxFromRows(T, B, N);

	N.xy = texture2D(uNormalMap, vTexCoord0).xy * 2.0 - 1.0;
	N.z = sqrt(1.0 - dot(N.xy, N.xy));
	N = normalize(mul(N, TBN));
#endif // USE_NORMAL_MAP

	vec3 R = reflect(-V, N); // view reflection vector around normal

	float NdotV = clamp(dot(N, V), 0.0, 0.99);

	vec3 F0 = vec3(0.04, 0.04, 0.04);
	F0 = mix(F0, base_opacity.xyz, occ_rough_metal.b);

	vec3 color = vec3(0.0, 0.0, 0.0);

	// jitter
#if FORWARD_PIPELINE_AAA
	vec4 jitter = texture2D(uNoiseMap, mod(gl_FragCoord.xy, vec2(64, 64)) / vec2(64, 64));
#else // FORWARD_PIPELINE_AAA
	vec4 jitter = vec4_splat(0.);
#endif // FORWARD_PIPELINE_AAA

	// SLOT 0: linear light
	{
		float k_shadow = 1.0;
#if SLOT0_SHADOWS
		float k_fade_split = 1.0 - jitter.z * 0.3;

		if(view.z < uLinearShadowSlice.x * k_fade_split) {
			k_shadow *= SampleShadowPCF(uLinearShadowMap, vLinearShadowCoord0, uShadowState.y * 0.5, uShadowState.z, jitter);
		} else if(view.z < uLinearShadowSlice.y * k_fade_split) {
			k_shadow *= SampleShadowPCF(uLinearShadowMap, vLinearShadowCoord1, uShadowState.y * 0.5, uShadowState.z, jitter);
		} else if(view.z < uLinearShadowSlice.z * k_fade_split) {
			k_shadow *= SampleShadowPCF(uLinearShadowMap, vLinearShadowCoord2, uShadowState.y * 0.5, uShadowState.z, jitter);
		} else if(view.z < uLinearShadowSlice.w * k_fade_split) {
#if FORWARD_PIPELINE_AAA
			k_shadow *= SampleShadowPCF(uLinearShadowMap, vLinearShadowCoord3, uShadowState.y * 0.5, uShadowState.z, jitter);
#else // FORWARD_PIPELINE_AAA
			float pcf = SampleShadowPCF(uLinearShadowMap, vLinearShadowCoord3, uShadowState.y * 0.5, uShadowState.z, jitter);
			float ramp_len = (uLinearShadowSlice.w - uLinearShadowSlice.z) * 0.25;
			float ramp_k = clamp((view.z - (uLinearShadowSlice.w - ramp_len)) / max(ramp_len, 1e-8), 0.0, 1.0);
			k_shadow *= pcf * (1.0 - ramp_k) + ramp_k; 
#endif // FORWARD_PIPELINE_AAA
		}
#endif // SLOT0_SHADOWS
		color += GGX(V, N, NdotV, uLightDir[0].xyz, base_opacity.xyz, occ_rough_metal.g, occ_rough_metal.b, F0, uLightDiffuse[0].xyz * k_shadow, uLightSpecular[0].xyz * k_shadow);
	}
	// SLOT 1: point/spot light (with optional shadows)
	{
		vec3 L = P - uLightPos[1].xyz;
		float distance = length(L);
		L /= max(distance, 1e-8);
		float attenuation = LightAttenuation(L, uLightDir[1].xyz, distance, uLightPos[1].w, uLightDir[1].w, uLightDiffuse[1].w);

#if SLOT1_SHADOWS
		attenuation *=SampleShadowPCF(uSpotShadowMap, vSpotShadowCoord, uShadowState.y, uShadowState.w, jitter);
#endif // SLOT1_SHADOWS
		color += GGX(V, N, NdotV, L, base_opacity.xyz, occ_rough_metal.g, occ_rough_metal.b, F0, uLightDiffuse[1].xyz * attenuation, uLightSpecular[1].xyz * attenuation);
	}
	// SLOT 2-N: point/spot light (no shadows) [todo]
	{
		for (int i = 2; i < 8; ++i) {
			vec3 L = P - uLightPos[i].xyz;
			float distance = length(L);
			L /= max(distance, 1e-8);
			float attenuation = LightAttenuation(L, uLightDir[i].xyz, distance, uLightPos[i].w, uLightDir[i].w, uLightDiffuse[i].w);

			color += GGX(V, N, NdotV, L, base_opacity.xyz, occ_rough_metal.g, occ_rough_metal.b, F0, uLightDiffuse[i].xyz * attenuation, uLightSpecular[i].xyz * attenuation);
		}
	}

	// IBL
	float MAX_REFLECTION_LOD = 10.;
#if 0 // LOD selection
	vec3 Ndx = normalize(N + ddx(N));
	float dx = length(Ndx.xy / Ndx.z - N.xy / N.z) * 256.0;
	vec3 Ndy = normalize(N + ddy(N));
	float dy = length(Ndy.xy / Ndy.z - N.xy / N.z) * 256.0;

	float dd = max(dx, dy);
	float lod_level = log2(dd);
#endif

	vec3 irradiance = textureCube(uIrradianceMap, ReprojectProbe(P, N)).xyz;
	vec3 radiance = textureCubeLod(uRadianceMap, ReprojectProbe(P, R), occ_rough_metal.y * MAX_REFLECTION_LOD).xyz;

#if FORWARD_PIPELINE_AAA
	vec4 ss_irradiance = texture2D(uSSIrradianceMap, gl_FragCoord.xy / uResolution.xy);
	vec4 ss_radiance = texture2D(uSSRadianceMap, gl_FragCoord.xy / uResolution.xy);

	irradiance = ss_irradiance.xyz; // mix(irradiance, ss_irradiance, ss_irradiance.w);
	radiance = mix(radiance, ss_radiance.xyz, ss_radiance.w);
#endif

	vec3 diffuse = irradiance * base_opacity.xyz;
	vec3 F = FresnelSchlickRoughness(NdotV, F0, occ_rough_metal.y);
	vec2 brdf = texture2D(uBrdfMap, vec2(NdotV, occ_rough_metal.y)).xy;
	vec3 specular = radiance * (F * brdf.x + brdf.y);
#if FORWARD_PIPELINE_AAA
	specular *= uAAAParams[2].x; // * specular weight
#endif

	vec3 kS = specular;
	vec3 kD = vec3_splat(1.) - kS;
	kD *= 1. - occ_rough_metal.z;

	color += kD * diffuse;
	color += specular;
	color += uAmbientColor.xyz;
	color *= occ_rough_metal.x;
	color += self.xyz;

	color = DistanceFog(view, color);
#endif // DEPTH_ONLY != 1

	float opacity = base_opacity.w;

#if ENABLE_ALPHA_CUT
	if (opacity < 0.8)
		discard;
#endif // ENABLE_ALPHA_CUT

#if DEPTH_ONLY != 1
#if FORWARD_PIPELINE_AAA_PREPASS
	vec3 N_view = mul(u_view, vec4(N, 0)).xyz;
	vec2 velocity = vec2(vProjPos.xy / vProjPos.w - vPrevProjPos.xy / vPrevProjPos.w);
	gl_FragData[0] = vec4(N_view.xyz, vProjPos.z);
	gl_FragData[1] = vec4(velocity.xy, occ_rough_metal.y, 0.);
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
