$input a_position

#include <forward_pipeline.sh>

void main() {
	gl_Position = mul(u_viewProj, vec4(a_position.xy, 0.0, 1.0));
}
