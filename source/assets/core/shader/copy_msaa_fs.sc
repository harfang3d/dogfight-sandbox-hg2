$input v_texcoord0

#include <bgfx_shader.sh>

SAMPLER2DMS(u_copyColor, 0);
SAMPLER2DMS(u_copyDepth, 1);

void main() {
	gl_FragDepth = texelFetch(u_copyDepth, v_texcoord0, 0);
}
