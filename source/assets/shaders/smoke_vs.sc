$input a_position, a_normal, a_texcoord0, a_tangent
$output front_face, vWorldPos, vNormal, vTexCoord0, vTangent, vBinormal

#include <forward_pipeline.sh>

void main() {
	vec3 normal = a_normal;

	vWorldPos = mul(u_model[0], vec4(a_position, 1.0)).xyz;
	vNormal = mul(u_model[0], vec4(normal * 2.0 - 1.0, 0.0)).xyz;
	vec3 nv_normal = normalize(mul(u_modelView, vec4(normal * 2.0 - 1.0, 0.0)).xyz);
	vec3 model_pos = mul(u_modelView, vec4(0,0,0, 1.0)).xyz;
	front_face.x = abs(dot(nv_normal,normalize(model_pos)));

	vTexCoord0 = a_texcoord0;

	gl_Position = mul(u_modelViewProj, vec4(a_position, 1.0));
}
