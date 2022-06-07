#include "bgfx_compute.sh"

// Build the remaining levels of the minimum depth pyramid.

IMAGE2D_RO(u_depthTexIn, rg32f, 0);     //  input: level i of the min depth pyramid
IMAGE2D_WR(u_depthTexOut, rg32f, 1);    // output: level i+1 of the min depth pyramid

NUM_THREADS(16, 16, 1)
void main() {
	ivec2 sizeOut = imageSize(u_depthTexOut);
	ivec2 coordOut = ivec2(gl_GlobalInvocationID.xy);

	ivec2 sizeIn = imageSize(u_depthTexIn);
	ivec2 coordIn = coordOut * 2;     

	vec2 z = vec2(1.0, 0.0);

	// The computation is applied on all the texture area.
	// It's not restricted to the actual viewport so we don't need to perform any extra check.
	vec2 z0 = imageLoad(u_depthTexIn, coordIn).xy;
	vec2 z2 = imageLoad(u_depthTexIn, coordIn + ivec2(0, 1)).xy;
	vec2 z1 = imageLoad(u_depthTexIn, coordIn + ivec2(1, 0)).xy;            
	vec2 z3 = imageLoad(u_depthTexIn, coordIn + ivec2(1, 1)).xy;

	z.x = min(min(z0.x, z1.x), min(z2.x, z3.x));
	z.y = max(max(z0.y, z1.y), max(z2.y, z3.y));

	// Here we handle the case where the size of the previous level is odd and we are on the boundaries
	// of the output texture.
	// In this case, we will need to sample an extra row or column.
	bvec4 odd_last = bvec4(greaterThan(sizeIn.xy, 2*sizeOut.xy), equal(coordOut, sizeOut-ivec2(1,1)));
	bvec2 extra_fetch = bvec2(all(odd_last.xz), all(odd_last.yw));
	if(extra_fetch.x) {
		vec2 z4 = imageLoad(u_depthTexIn, coordIn + ivec2(2,0)).xy;
		vec2 z5 = imageLoad(u_depthTexIn, coordIn + ivec2(2,1)).xy;
		z.x = min(z.x, min(z4.x, z5.x));
		z.y = max(z.y, max(z4.y, z5.y));
	}
	if(extra_fetch.y) {
		vec2 z6 = imageLoad(u_depthTexIn, coordIn + ivec2(0,2)).xy;
		vec2 z7 = imageLoad(u_depthTexIn, coordIn + ivec2(1,2)).xy;
		z.x = min(z.x, min(z6.x, z7.x));
		z.y = max(z.y, max(z6.y, z7.y));

		if(extra_fetch.x) {
			vec2 z8 = imageLoad(u_depthTexIn, coordIn + ivec2(2,2)).xy;
			z.x = min(z.x, z8.x);
			z.y = max(z.y, z8.y);
		}
	}

	imageStore(u_depthTexOut, coordOut, vec4(z.x, z.y, 0, 1));
}