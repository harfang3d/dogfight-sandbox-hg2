$input front_face,vWorldPos, vNormal, vTangent, vBinormal, vTexCoord0

#include <forward_pipeline.sh>

// Surface attributes
uniform vec4 uColor;

// Texture slots

SAMPLER2D(uColorMap, 0);

//
vec3 DistanceFog(vec3 pos, vec3 color) {
	if (uFogState.y == 0.0)
		return color;

	float k = clamp((pos.z - uFogState.x) * uFogState.y, 0.0, 1.0);
	return mix(color, uFogColor.xyz, k);
}


// Entry point of the forward pipeline default uber shader (Phong and PBR)
void main() {
	vec4 self = texture2D(uColorMap, vTexCoord0) * uColor;

	vec3 color = self.xyz;
	
	color = DistanceFog(vWorldPos, color);

	gl_FragColor = vec4(color, self.w * front_face.x);
}
