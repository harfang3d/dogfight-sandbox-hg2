$input v_texcoord0

#include <bgfx_shader.sh>

uniform vec4 color;

SAMPLER2D(s_tex, 0);

void main() {
	//float d_color = texture2D(s_tex, v_texcoord0).r * color.r;
	//gl_FragColor = vec4(d_color, d_color, d_color, 1.0);
	gl_FragColor = texture2D(s_tex, v_texcoord0) * color;
}
