$input v_texcoord0

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

SAMPLER2D(u_source, 0);
SAMPLER2D(u_input, 1);

void main() {
	vec2 uv = gl_FragCoord.xy / uResolution.xy;

	vec3 color = texture2D(u_source, uv).rgb;
	color += texture2D(u_input, uv).rgb;

	gl_FragColor = vec4(color, 1.);
}
