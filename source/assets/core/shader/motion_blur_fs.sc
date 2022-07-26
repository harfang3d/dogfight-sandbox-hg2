// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

SAMPLER2D(u_color, 0);
SAMPLER2D(u_attr0, 1);
SAMPLER2D(u_attr1, 2);
SAMPLER2D(u_noise, 3);

#include <aaa_utils.sh>

void main() {
	vec4 jitter = texture2D(u_noise, mod(gl_FragCoord.xy, vec2(64, 64)) / vec2(64, 64));

	float strength = uAAAParams[0].w;

	vec2 uv = gl_FragCoord.xy / uResolution.xy;
	vec2 dt = GetVelocityVector(uv);

	vec4 blur_out = vec4(0., 0., 0., 0.);
	for (int i = 0; i < 8; ++i) {
		float k = (((float(i) + jitter.x) / 8.) - 0.5) * strength;
 		blur_out += texture2D(u_color, uv + dt * k);
	}

	gl_FragColor = blur_out / 8.;
}
