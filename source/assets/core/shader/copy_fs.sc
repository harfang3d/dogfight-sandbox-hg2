$input v_texcoord0

#include <bgfx_shader.sh>

SAMPLER2D(u_copyColor, 0);
SAMPLER2D(u_copyDepth, 1);

void main() {
	gl_FragColor = texture2D(u_copyColor, v_texcoord0);
	gl_FragDepth = texture2D(u_copyDepth, v_texcoord0).r;
}
