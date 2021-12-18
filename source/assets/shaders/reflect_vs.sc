$input a_position, a_normal, a_texcoord0
$output vWorldPos, vNormal, vTexCoord0

#include <forward_pipeline.sh>

void main() {
	vec3 normal = a_normal;

	vWorldPos = mul(u_model[0], vec4(a_position, 1.0)).xyz;
	vNormal = mul(u_model[0], vec4(normal * 2.0 - 1.0, 0.0)).xyz;
	vTexCoord0 = a_texcoord0;

	gl_Position = mul(u_modelViewProj, vec4(a_position, 1.0));
}
