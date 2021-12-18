#ifndef HIZ_TRACE_SH_HEADER_GUARD
#define HIZ_TRACE_SH_HEADER_GUARD

// SAMPLER2D(u_depthTex, X); // input: minimum depth pyramid  <= Must be declared by the user.

uniform vec4 u_depthTexInfos; // width(x) heigh(y) start mipmap level(z) max mipmap level(w)

vec3 intersect_cell_boundary(vec3 pos, vec3 dir, vec2 cell, vec2 cell_count, vec4 cross_step) {
	vec2 planes = (cell + cross_step.xy) / cell_count;
	vec3 intersection;
	if(dir.x == 0.0) {
		float delta = (planes.y - pos.y) / dir.y;
		intersection = pos + dir * delta;
		intersection.y += cross_step.w;
	}
	else if(dir.y == 0.0) {
		float delta = (planes.x - pos.x) / dir.x;
		intersection = pos + dir * delta;
		intersection.x += cross_step.z;
	}
	else {
		vec2 delta = (planes - pos.xy) / dir.xy;
		intersection = pos + dir * min(delta.x, delta.y);
		intersection.xy += (delta.x < delta.y) ? vec2(cross_step.z, 0.0) : vec2(0.0, cross_step.w);
	}  
	return intersection;
}

// returns the texture size in pixels for a given pyramid level.
// textureSize(sampler, level) should be used.
// Unfortunately bgfx directx implementation always returns the size of level 0.
vec2 mip_size(int level) {
	return floor(u_depthTexInfos.xy / ((level != 0) ? exp2(level) : 1.0));
}

bool hiz_trace(vec3 ray_o, vec3 ray_d, mat4 proj, float z_near, int max_iterations, out vec3 ray) {
	vec2 viewport_scale = uv_ratio.xy / u_depthTexInfos.xy;
	vec3 viewport_min = vec3(u_viewRect.xy * viewport_scale, 0.);
	vec3 viewport_max = vec3((u_viewRect.xy + u_viewRect.zw) * viewport_scale, 1.);

	int level_max = int(u_depthTexInfos.w);
	int level_min = int(u_depthTexInfos.z);
	ivec2 iterations = ivec2(0, level_min);
	
	vec2 cell_count = mip_size(level_min);

	// clip to the near plane
	float ray_len = ((ray_o.z + ray_d.z * 1000.0) < z_near) ? (z_near - ray_o.z) / ray_d.z : 1000.0;
	vec3 end_point = ray_o + ray_d * ray_len;

	// project into homogeneous clip space
	vec4 h0 = mul(proj, vec4(ray_o, 1.));
	vec4 h1 = mul(proj, vec4(end_point, 1.));

	// screen-space endpoints
	vec3 p0 = h0.xyz / h0.w;
	p0.y *= -1.;
	p0.xy = NDCToViewRect(p0.xy) / cell_count.xy;

	vec3 p1 = h1.xyz / h1.w;
	p1.y *= -1.;
	p1.xy = NDCToViewRect(p1.xy) / cell_count.xy;

	// compute ray start position and direction in screen space
	vec3 pos = p0;
	vec3 dir = normalize(p1 - p0);

	if(dir.z == 0) {
		ray = vec3(-1., -1., 0.);
		return false;
	}

	vec4 cross_step;
	cross_step.xy = step(vec2_splat(0.0), dir.xy);
	cross_step.zw = (2.0 * cross_step.xy - vec2_splat(1.0)) * vec2_splat(0.5) / cell_count.xy;
	
	vec2 cell = floor(pos.xy * cell_count);
	pos.xy = cell / cell_count + vec2_splat(0.25) / cell_count.xy;

	ray = intersect_cell_boundary(pos, dir, cell, cell_count, cross_step);

    for(iterations.x = 0; (iterations.x < max_iterations) && (iterations.y >= 0); ++iterations.x, --iterations.y) {
        // check if the ray goes out of the viewport.      
        if(any(lessThan(ray, viewport_min))) {
            return false;
        }
        if(any(greaterThanEqual(ray, viewport_max))) {
            return false;
        }
        cell_count = mip_size(iterations.y);
        cell = floor(ray.xy * cell_count);
         
        vec2 z_interval = texelFetch(u_depthTex, ivec2(cell), iterations.y).xy;

        vec3 tmp = ray;
        float dz = z_interval.x - ray.z;
        if (dz > 0) {
        	tmp = ray + dz * sign(dir.z) * dir / dir.z;
        }
        else {
            dz = ray.z - z_interval.y;
            if (dz > 0) {
                tmp = ray + dz * sign(dir.z) * dir / dir.z;
            }
        }
        vec2 new_cell = floor(tmp.xy * cell_count);
  		if (any(notEqual(new_cell, cell))) {
			tmp = intersect_cell_boundary(ray, dir, cell, cell_count, cross_step);
			iterations.y = min(level_max, iterations.y + 2);
		}
		else if ((iterations.y == (level_min+1)) && (dz > 0.00001)) {
			tmp = intersect_cell_boundary(ray, dir, cell, cell_count, cross_step);
			iterations.y = 2;
		}

		ray = tmp;
	}

	return iterations.y < 0 && iterations.x < max_iterations;
}

bool TraceScreenRay(vec3 ray_o, vec3 ray_d, mat4 proj, float z_near, int max_iterations, out vec2 hit_pixel, out vec3 hit_point) {
	vec3 ray;
	
	if (hiz_trace(ray_o, ray_d, proj, z_near, max_iterations, ray)) {
		// compute screen position of the hit pixel
#if BGFX_SHADER_LANGUAGE_GLSL
		hit_pixel = vec2(ray.x, 1.0 - ray.y) * floor(uResolution.xy / uv_ratio);
#else
		hit_pixel = ray.xy * floor(uResolution.xy / uv_ratio);
#endif

		// and its world space coordinates
		hit_point = ray;
		hit_point.xy = 2. * hit_point.xy - 1.;
		hit_point.y *= -1.;

		vec4 p = mul(uMainInvProjection, vec4(hit_point, 1.));
		hit_point.xyz = p.xyz / p.w;
		return true;
	} else {
		hit_pixel = vec2_splat(0.);
		hit_point = vec3_splat(0.);
		return false;
	}
}

#endif // HIZ_TRACE_SH_HEADER_GUARD
