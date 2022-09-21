// HARFANG(R) Copyright (C) 2022 Emmanuel Julien, NWNC HARFANG. Released under GPL/LGPL/Commercial Licence, see licence.txt for details.
#ifndef HIZ_TRACE_SH_HEADER_GUARD
#define HIZ_TRACE_SH_HEADER_GUARD

// SAMPLER2D(u_depthTex, X); // input: minimum depth pyramid  <= Must be declared by the user.

uniform vec4 u_depthTexInfos; // width(x) heigh(y) start mipmap level(z) max mipmap level(w)

//
vec3 ray_step_cell(vec3 ray, vec3 dir, float step, vec2 z_range) {
	float t = 100000000.0; // [EJ] any large value is ok

	if (dir.x > 0.0)
		t = min(t, (floor(ray.x / step + 1.0) * step - ray.x) / dir.x);
	else if (dir.x < 0.0)
		t = min(t, (ceil(ray.x / step - 1.0) * step - ray.x) / dir.x);

	if (dir.y > 0.0)
		t = min(t, (floor(ray.y / step + 1.0) * step - ray.y) / dir.y);
	else if (dir.y < 0.0)
		t = min(t, (ceil(ray.y / step - 1.0) * step - ray.y) / dir.y);

	if (dir.z > 0.0) {
		if (ray.z < z_range.x)
			t = min(t, (z_range.x - ray.z) / dir.z);
	} else if (dir.z < 0.0) {
		if (ray.z > z_range.y)
			t = min(t, (z_range.y - ray.z) / dir.z);
	}

	return ray + dir * t;
}

float hiz_trace(vec3 ray_o, vec3 ray_d, mat4 proj, float z_near, int max_iterations, out vec3 ray) {
	vec3 viewport_min = vec3(u_viewRect.xy, 0.);
	vec3 viewport_max = vec3(u_viewRect.xy + u_viewRect.zw, 1.);

	int level_min = int(u_depthTexInfos.z);
	int level_max = int(u_depthTexInfos.w);

	// clip to the near plane
	float ray_len = ((ray_o.z + ray_d.z * 1000.0) < z_near) ? (z_near - ray_o.z) / ray_d.z : 1000.0;
	vec3 end_point = ray_o + ray_d * ray_len;

	// project into homogeneous clip space
	vec4 h0 = mul(proj, vec4(ray_o, 1.));
	vec4 h1 = mul(proj, vec4(end_point, 1.));

	// endpoints in screen space
	vec3 p0 = h0.xyz / h0.w;
	p0.y *= -1.0;
	p0.xy = NDCToViewRect(p0.xy);

	vec3 p1 = h1.xyz / h1.w;
	p1.y *= -1.0;
	p1.xy = NDCToViewRect(p1.xy);

	//
	ray = p0;
	vec3 dir = normalize(p1 - p0);

	vec2 uv_offset = sign(dir.xy) * 0.0001; // slight nudge to sample the correct cell

#if 1
	int level = level_min;

	int iterations = 0;

	while (level > -1) {
		if (++iterations == max_iterations)
			return -1.0;

		if (any(lessThan(ray, viewport_min)))
			return 0.0; // TODO ramp out
		if (any(greaterThanEqual(ray, viewport_max)))
			return 0.0; // TODO ramp out

		float step = pow(2.0, level);
		vec2 z_range = texelFetch(u_depthTex, ivec2(ray.xy / step + uv_offset), level).xy;

		if (ray.z >= z_range.x && ray.z <= z_range.y) {
			--level;
		} else {
			ray = ray_step_cell(ray, dir, step, z_range);
			if (level < level_max - 2)
				++level;
		}
	}

	vec2 k_fade = saturate((ray.xy - viewport_min.xy) / (u_viewRect.zw * 0.1));
	k_fade *= saturate(vec2(1.0, 1.0) - (ray.xy - viewport_max.xy * 0.9) / (u_viewRect.zw * 0.1));

	ray.xy /= u_depthTexInfos.xy;

	return k_fade.x * k_fade.y; // hit
#else
	int level = 0; // reference implementation (works on any mip level)

	for (int i = 0; i < 4096; ++i) {
		if (any(lessThan(ray, viewport_min)))
			return false;
		if (any(greaterThanEqual(ray, viewport_max)))
			return false;

		float step = pow(2.0, level);
		vec2 z_range = texelFetch(u_depthTex, ivec2(ray.xy / step), level).xy;

		if (ray.z >= z_range.x && ray.z <= z_range.y) {
			ray.xy = ray.xy / u_depthTexInfos.xy;
			return true;
		}

		ray = ray_step_cell(ray, dir, step, z_range);
	}

	return 0.0;
#endif
}

float TraceScreenRay(vec3 ray_o, vec3 ray_d, mat4 proj, float z_near, int max_iterations, out vec2 hit_pixel, out vec3 hit_point) {
	vec3 ray;
	
	float hit = hiz_trace(ray_o, ray_d, proj, z_near, max_iterations, ray);

	if (hit > 0.0) {
		// compute screen position of the hit pixel
#if BGFX_SHADER_LANGUAGE_GLSL
		hit_pixel = vec2(ray.x, 1.0 - ray.y) * floor(uResolution.xy / uv_ratio);
#else
		hit_pixel = ray.xy * floor(uResolution.xy / uv_ratio);
#endif
		hit_point = ray;
	} else {
		hit_pixel = vec2_splat(0.);
		hit_point = vec3_splat(0.);
	}

	return hit;
}

float ComputeRayLogDepth(in mat4 projection, in vec3 ray) {
	const float z_epsilon = 0.1; // [todo] parameter?

	float za = texelFetch(u_depthTex, ivec2(floor(ray.xy * u_depthTexInfos.xy)), 0).x;
	float zb = z_epsilon * (za - projection[2].z);
#if BGFX_SHADER_LANGUAGE_GLSL
	return (zb + projection[3].z * za) / (zb + projection[3].z);
#else
	return (zb + projection[2].w * za) / (zb + projection[2].w);
#endif
}

#endif // HIZ_TRACE_SH_HEADER_GUARD
