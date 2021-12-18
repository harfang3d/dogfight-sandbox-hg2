$input v_texcoord0

#include <bgfx_shader.sh>

uniform vec4 u_color;
SAMPLER2D(u_tex, 0);

void main() {
	float opacity = texture2D(u_tex, v_texcoord0).a * u_color.a;
	gl_FragColor = vec4(u_color.rgb, opacity); 
}
