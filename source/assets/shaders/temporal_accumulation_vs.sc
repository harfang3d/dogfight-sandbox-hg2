$input a_position, a_texcoord0 
$output vTexCoord0,

#include <forward_pipeline.sh>

void main() {
	gl_Position = mul(u_viewProj, vec4(a_position.xy, 0.0, 1.0));
	vTexCoord0 = a_texcoord0;
}
