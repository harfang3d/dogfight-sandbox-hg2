$input a_position

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <forward_pipeline.sh>

void main() {
	gl_Position = mul(u_viewProj, vec4(a_position.xy, 0.0, 1.0));
}
