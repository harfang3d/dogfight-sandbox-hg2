$input v_texcoord0

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

uniform vec4 u_params;
SAMPLER2D(u_source, 0);

void main() {
	float threshold = u_params.x;
	float knee = u_params.y;

	vec4 color = texture2D(u_source, gl_FragCoord.xy / uResolution.xy);
	float lum = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));
	float r = clamp(lum - threshold + knee, 0, 2. * knee);
	r = (r * r) / (4. * knee);

	gl_FragColor = color * max(r , lum - threshold) / max(lum, 0.00001);
}
