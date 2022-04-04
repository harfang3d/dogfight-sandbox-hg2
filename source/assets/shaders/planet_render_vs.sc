$input a_position, a_normal
$output vNormal, uv, position, screen_ray, pos_test

#include <bgfx_shader.sh>

uniform vec4 resolution;
uniform vec4 focal_distance;

void main() {
#if BGFX_SHADER_LANGUAGE_GLSL
	uv = vec2(clamp(a_position.x ,0.0, 1.0), 1.0 - clamp(a_position.z, 0.0, 1.0));
#else
	uv = vec2(clamp(a_position.x, 0.0, 1.0), clamp(a_position.z, 0.0, 1.0));
#endif
	pos_test = a_position;
	position = uv * 2.0 - 1.0;
	position.y *= -1.0;
	float ratio = resolution.x / resolution.y;
	screen_ray = vec3(a_position.x , a_position.z, focal_distance.x);
	
	vNormal = mul(u_model[0], vec4(a_normal * 2.0 - 1.0, 0.0)).xyz;
	gl_Position = mul(u_modelViewProj, vec4(a_position, 1.0));;
}
