$input vWorldPos, vNormal, vTexCoord0

#include <forward_pipeline.sh>

// Surface attributes
uniform vec4 t;

// Texture slots
SAMPLER2D(uReflectMap, 0);


// Entry point of the forward pipeline default uber shader (Phong and PBR)
void main() {

	vec3 view = mul(u_view, vec4(vWorldPos,1.0)).xyz; // fragment view space pos
	vec4 fragCoords = mul(u_proj, vec4(view,1.0)); // fragment view space pos
	fragCoords/=fragCoords.w;
	vec2 uv = (fragCoords.xy+1.)*0.5;

	vec3 color = mix(texture2D(uReflectMap,uv ).xyz ,vec3(1.,0.5,0.2),0.5);
	//color.r = uv.x;
	//color.g = uv.y;
	//color.b = 0.;
	
    gl_FragColor = vec4(color, 1.0);
}