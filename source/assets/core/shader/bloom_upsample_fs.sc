$input v_texcoord0

#include <forward_pipeline.sh>

SAMPLER2D(u_source, 0);

uniform vec4 u_params;

void main() {
	vec2 uv = v_texcoord0.xy;
	vec4 offset = vec4(-1., 1., 1., 0.) / uResolution.xxyy;

	vec4 t0 = texture2D(u_source, uv - offset.yz);
	vec4 t1 = texture2D(u_source, uv - offset.wz);
	vec4 t2 = texture2D(u_source, uv - offset.xz);

	vec4 t3 = texture2D(u_source, uv + offset.xw);
	vec4 t4 = texture2D(u_source, uv);
	vec4 t5 = texture2D(u_source, uv + offset.yw);

	vec4 t6 = texture2D(u_source, uv + offset.xz);
	vec4 t7 = texture2D(u_source, uv + offset.wz);
	vec4 t8 = texture2D(u_source, uv + offset.yz);

	gl_FragColor = u_params.z * (t0 + t2 + t6 + t8 + 2. * (t1 + t3 + t5 + t7) + 4. * t4) / 16.;
}
