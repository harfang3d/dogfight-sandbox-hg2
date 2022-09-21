$input v_texcoord0

// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#include <bgfx_shader.sh>

uniform vec4 u_color;
SAMPLER2D(u_tex, 0);

void main() {
	float opacity = texture2D(u_tex, v_texcoord0).w * u_color.w;
	gl_FragColor = vec4(u_color.xyz, opacity); 
}
