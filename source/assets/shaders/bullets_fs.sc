$input vWorldPos, vNormal, vTexCoord0, vTexCoord1, vTangent, vBinormal

#include <forward_pipeline.sh>

// Surface attributes
uniform vec4 uColor0;
uniform vec4 uColor1;

void main() {
	gl_FragColor = mix(uColor0, uColor1, vTexCoord0.x);
}
