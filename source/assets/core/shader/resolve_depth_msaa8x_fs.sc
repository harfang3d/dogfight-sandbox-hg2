$input v_texcoord0

#include <bgfx_shader.sh>

uniform Texture2DMS<vec4, 8> u_copyDepth : REGISTER(t, 0);

void main() {
	int w, h, c;
	u_copyDepth.GetDimensions(w, h, c);
	gl_FragDepth = u_copyDepth.Load(ivec2(v_texcoord0 * vec2(w, h)), 0);
}
