$input a_position
$output v_texcoord0

#include <bgfx_shader.sh>

uniform vec4 uv_scale;

void main() {
	gl_Position = mul(u_modelViewProj, vec4(a_position, 1.0));
#if BGFX_SHADER_LANGUAGE_GLSL
	v_texcoord0 = vec2(a_position.x+0.5, 1.0 - (a_position.z + 0.5)) * uv_scale.xy;
#else
	v_texcoord0 = vec2(a_position.x + 0.5, a_position.z + 0.5) * uv_scale.xy;
#endif
}
