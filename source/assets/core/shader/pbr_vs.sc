$input a_position, a_normal, a_texcoord0, a_texcoord1, a_tangent, a_bitangent, a_indices, a_weight
$output vWorldPos, vNormal, vTexCoord0, vTexCoord1, vTangent, vBinormal, vLinearShadowCoord0, vLinearShadowCoord1, vLinearShadowCoord2, vLinearShadowCoord3, vSpotShadowCoord, vProjPos, vPrevProjPos

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

mat3 normal_mat(mat4 m) {
#if BGFX_SHADER_LANGUAGE_GLSL
	vec3 u = normalize(vec3(m[0].x, m[1].x, m[2].x));
	vec3 v = normalize(vec3(m[0].y, m[1].y, m[2].y));
	vec3 w = normalize(vec3(m[0].z, m[1].z, m[2].z));
#else
	vec3 u = normalize(m[0].xyz);
	vec3 v = normalize(m[1].xyz);
	vec3 w = normalize(m[2].xyz);
#endif

	return mtxFromRows(u, v, w);
}

void main() {
	// position
	vec4 vtx = vec4(a_position, 1.0);

#if ENABLE_SKINNING
	vec4 world_pos =
		mul(u_model[int(a_indices.x * 256.0)], vtx) * a_weight.x +
		mul(u_model[int(a_indices.y * 256.0)], vtx) * a_weight.y +
		mul(u_model[int(a_indices.z * 256.0)], vtx) * a_weight.z +
		mul(u_model[int(a_indices.w * 256.0)], vtx) * a_weight.w;

#if FORWARD_PIPELINE_AAA_PREPASS
	vec4 prv_world_pos =
		mul(uPreviousModel[int(a_indices.x * 256.0)], vtx) * a_weight.x +
		mul(uPreviousModel[int(a_indices.y * 256.0)], vtx) * a_weight.y +
		mul(uPreviousModel[int(a_indices.z * 256.0)], vtx) * a_weight.z +
		mul(uPreviousModel[int(a_indices.w * 256.0)], vtx) * a_weight.w;
#endif // FORWARD_PIPELINE_AAA_PREPASS
#else // ENABLE_SKINNING
	vec4 world_pos = mul(u_model[0], vtx);

#if FORWARD_PIPELINE_AAA_PREPASS
	vec4 prv_world_pos = mul(uPreviousModel[0], vtx);
#endif // FORWARD_PIPELINE_AAA_PREPASS
#endif // ENABLE_SKINNING

#if DEPTH_ONLY != 1
	// normal
	vec4 normal = vec4(a_normal * 2. - 1., 0.);

#if ENABLE_SKINNING
	vec4 skinned_normal =
		mul(u_model[int(a_indices.x * 256.0)], normal) * a_weight.x +
		mul(u_model[int(a_indices.y * 256.0)], normal) * a_weight.y +
		mul(u_model[int(a_indices.z * 256.0)], normal) * a_weight.z +
		mul(u_model[int(a_indices.w * 256.0)], normal) * a_weight.w;

	skinned_normal = normalize(skinned_normal);

	vNormal = skinned_normal.xyz;
#else // ENABLE_SKINNING
	vNormal = mul(normal_mat(u_model[0]), normal.xyz);
#endif // ENABLE_SKINNING

	// tangent frame
#if USE_NORMAL_MAP // [EJ] FIXME this probably won't be the only condition to compute the tangent frame for long
	vec4 tangent = vec4(a_tangent * 2.0 - 1.0, 0.0);
	vec4 binormal = vec4(a_bitangent * 2.0 - 1.0, 0.0);

#if ENABLE_SKINNING
	vec4 skinned_tangent =
		mul(u_model[int(a_indices.x * 256.0)], tangent) * a_weight.x +
		mul(u_model[int(a_indices.y * 256.0)], tangent) * a_weight.y +
		mul(u_model[int(a_indices.z * 256.0)], tangent) * a_weight.z +
		mul(u_model[int(a_indices.w * 256.0)], tangent) * a_weight.w;

	vec4 skinned_binormal =
		mul(u_model[int(a_indices.x * 256.0)], binormal) * a_weight.x +
		mul(u_model[int(a_indices.y * 256.0)], binormal) * a_weight.y +
		mul(u_model[int(a_indices.z * 256.0)], binormal) * a_weight.z +
		mul(u_model[int(a_indices.w * 256.0)], binormal) * a_weight.w;

	vTangent = skinned_tangent.xyz;
	vBinormal = skinned_binormal.xyz;
#else // ENABLE_SKINNING
	vTangent = mul(u_model[0], tangent).xyz;
	vBinormal = mul(u_model[0], binormal).xyz;
#endif // ENABLE_SKINNING
#endif // USE_NORMAL_MAP

	// shadow data
#if SLOT0_SHADOWS || SLOT1_SHADOWS
	float shadowMapShrinkOffset = 0.01;
	vec3 shadowVertexShrinkOffset = vNormal * shadowMapShrinkOffset;
#endif

#if SLOT0_SHADOWS
	vLinearShadowCoord0 = mul(uLinearShadowMatrix[0], vec4(world_pos.xyz + shadowVertexShrinkOffset, 1.0));
	vLinearShadowCoord1 = mul(uLinearShadowMatrix[1], vec4(world_pos.xyz + shadowVertexShrinkOffset, 1.0));
	vLinearShadowCoord2 = mul(uLinearShadowMatrix[2], vec4(world_pos.xyz + shadowVertexShrinkOffset, 1.0));
	vLinearShadowCoord3 = mul(uLinearShadowMatrix[3], vec4(world_pos.xyz + shadowVertexShrinkOffset, 1.0));
#endif

#if SLOT1_SHADOWS
	vSpotShadowCoord = mul(uSpotShadowMatrix, vec4(world_pos.xyz + shadowVertexShrinkOffset, 1.0));
#endif
#endif // DEPTH_ONLY

	//
	vWorldPos = world_pos.xyz;

#if USE_BASE_COLOR_OPACITY_MAP || USE_OCCLUSION_ROUGHNESS_METALNESS_MAP || USE_DIFFUSE_MAP || USE_SPECULAR_MAP|| USE_NORMAL_MAP || USE_SELF_MAP || USE_OPACITY_MAP
	vTexCoord0 = a_texcoord0;
#endif

#if DEPTH_ONLY != 1
#if USE_LIGHT_MAP || USE_AMBIENT_MAP
	vTexCoord1 = a_texcoord1;
#endif
#endif // DEPTH_ONLY != 1

	//
	vec4 proj_pos = mul(uViewProjUnjittered, world_pos);
#if FORWARD_PIPELINE_AAA_PREPASS
	vProjPos = proj_pos;
	vPrevProjPos = mul(uPreviousViewProjection, prv_world_pos);
#endif

	//
	gl_Position = mul(u_viewProj, world_pos);
}
