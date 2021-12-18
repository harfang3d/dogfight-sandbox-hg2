$input a_position, a_normal, a_texcoord0, a_texcoord1, a_tangent
$output vWorldPos, vNormal, vTexCoord0, vTexCoord1, vTangent, vBinormal //, camPos

#include <bgfx_shader.sh>

void main() {
	vWorldPos = mul(u_model[0], vec4(a_position, 1.0)).xyz;
	vNormal = mul(u_model[0], vec4(a_normal * 2.0 - 1.0, 0.0)).xyz;

#if (USE_DIFFUSE_MAP || USE_SPECULAR_MAP|| USE_NORMAL_MAP || USE_SELF_MAP || USE_OPACITY_MAP)
	vTexCoord0 = a_texcoord0;
#endif

#if (USE_LIGHT_MAP || USE_AMBIENT_MAP)
	vTexCoord1 = a_texcoord1;
#endif

#if (USE_NORMAL_MAP)
	vTangent = mul(u_model[0], vec4(a_tangent * 2.0 - 1.0, 0.0)).xyz;
	vBinormal = normalize(cross(vNormal, vTangent));
#endif

	//camPos=vec4(u_invView[3][0],u_invView[3][1],u_invView[3][2],1.);

	gl_Position = mul(u_modelViewProj, vec4(a_position, 1.0));
}
