$input a_position, a_normal, a_texcoord0, a_texcoord1, a_tangent
$output vWorldPos, vNormal, vTexCoord0, vTexCoord1, vTangent, vBinormal

#include <forward_pipeline.sh>

uniform vec4 uZRange;

void main() {
	vec3 normal = a_normal;

	vWorldPos = mul(u_model[0], vec4(a_position, 1.0)).xyz;
	vNormal = mul(u_model[0], vec4(normal * 2.0 - 1.0, 0.0)).xyz;

	vTexCoord0 = vec2(clamp((a_position.z - uZRange.x) / (uZRange.y - uZRange.x), 0.0, 1.0), 0.0);
	vTexCoord1 = a_texcoord1;

	gl_Position = mul(u_modelViewProj, vec4(a_position, 1.0));
}
