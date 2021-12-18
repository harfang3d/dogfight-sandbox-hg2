$input v_texcoord0

#include <forward_pipeline.sh>

SAMPLER2D(u_source, 0);

void main() {
	vec2 uv = v_texcoord0.xy;
	vec4 offset = vec4(-1., 1., 1., 0.) / uResolution.xxyy;

	vec4 s0 = texture2D(u_source, uv - offset.yz);
	vec4 s1 = texture2D(u_source, uv - offset.wz);
	vec4 s2 = texture2D(u_source, uv - offset.xz);

	vec4 s3 = texture2D(u_source, uv + offset.xw);
	vec4 s4 = texture2D(u_source, uv);
	vec4 s5 = texture2D(u_source, uv + offset.yw);

	vec4 s6 = texture2D(u_source, uv + offset.xz);
	vec4 s7 = texture2D(u_source, uv + offset.wz);
	vec4 s8 = texture2D(u_source, uv + offset.yz);

	offset = 0.5 * offset;

	vec4 t0 = texture2D(u_source, uv - offset.yz);
	vec4 t1 = texture2D(u_source, uv - offset.xz);
	vec4 t2 = texture2D(u_source, uv + offset.xz);
	vec4 t3 = texture2D(u_source, uv + offset.yz);

	vec4 v0 = s0 + s1 + s3 + s4;
	vec4 v1 = s1 + s2 + s4 + s5;
	vec4 v2 = s3 + s4 + s6 + s7;
	vec4 v3 = s4 + s5 + s7 + s8;
	vec4 v4 = t0 + t1 + t2 + t3;

	gl_FragColor = (((v0 + v1 + v2 + v3) / 4.) + v4) / 8.;
}
