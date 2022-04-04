// Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

$input vNormal, uv, position, screen_ray, pos_test

#include <bgfx_shader.sh>

SAMPLER2D(sea_noises, 0);
SAMPLER2D(stream_texture, 1);
SAMPLER2D(clouds_map, 2);
SAMPLER2D(tex_sky, 3);
SAMPLER2D(tex_space, 4);
SAMPLER2D(reflect_map, 5);
SAMPLER2D(reflect_map_depth, 6);
SAMPLER2D(terrain_map, 7);

uniform vec4 atmosphere_params; //x = Thickness, y=falloff, z=luminosity_falloff, w = atmosphere angle
uniform vec4 planet_radius;

uniform vec4 horizon_angle;
uniform vec4 clouds_scale;
uniform vec4 clouds_altitude;
uniform vec4 clouds_absorption;

uniform vec4 tex_sky_intensity;
uniform vec4 tex_space_intensity;
uniform vec4 resolution;

uniform vec4 cam_position; // x,y,z = position, w = normalized altitude in atmosphere thickness
uniform mat3 cam_normal;

uniform vec4 sea_scale;
uniform vec4 terrain_scale;
uniform vec4 terrain_position;
uniform vec4 terrain_edges; //coast min, coast max, clamp edge

uniform vec4 ambient_color;
uniform vec4 space_color;
uniform vec4 high_atmosphere_color;
uniform vec4 low_atmosphere_color;
uniform vec4 horizon_line_color;

uniform vec4 high_atmosphere_pos;
uniform vec4 low_atmosphere_pos;
uniform vec4 horizon_line_params; //x = pos, y = falloff

uniform vec4 horizon_low_line_params;

uniform vec4 sea_color;
uniform vec4 underwater_color;
uniform vec4 reflect_color;
uniform vec4 sea_reflection;
uniform vec4 reflect_offset;
uniform vec4 scene_reflect;

uniform vec4 sun_params; //size, smooth, in-atm glow intensity, in-space glow intensity

uniform vec4 z_Frustum;
uniform vec4 sun_dir;
uniform vec4 sun_color;

uniform vec4 uClock;
uniform vec4 uFogState;
uniform vec4 uFogColor;

//#define M_PI 3.141592653
#define LUM_R 0.2126
#define LUM_G 0.7152
#define LUM_B 0.0722

vec3 GetT(mat4 m)
{
	return vec3(m[0][3], m[1][3], m[2][3]);
}
vec3 GetX(mat4 m) { return vec3(m[0][0], m[0][1], m[0][2]); }
vec3 GetY(mat4 m) { return vec3(m[1][0], m[1][1], m[1][2]); }
vec3 GetZ(mat4 m) { return vec3(m[2][0], m[2][1], m[2][2]); }

vec3 DistanceFog(vec3 pos, vec3 color)
{
	if (uFogState.y == 0.0)
		return color;

	float k = clamp((pos.z - uFogState.x) * uFogState.y, 0.0, 1.0);
	return mix(color, uFogColor.xyz, k);
}

#if BGFX_SHADER_LANGUAGE_GLSL
#define ZBUFMIN 0.0
#define ZBUFMAX 1.0
#else
#define ZBUFMIN -1.0
#define ZBUFMAX 1.0
#endif

float get_zDepth(float near, float far)
{
	float a, b, z;
	z = far * near;
	const float zb_amplitude = ZBUFMAX - ZBUFMIN;
	a = z_Frustum.y / (z_Frustum.y - z_Frustum.x * zb_amplitude);
	b = z_Frustum.y * z_Frustum.x * zb_amplitude / (z_Frustum.x * zb_amplitude - z_Frustum.y);
	return ((a + b / z) - ZBUFMIN) / zb_amplitude;
}

float get_zFromDepth(float near, float zDepth)
{
	float a, b;
	const float zb_amplitude = ZBUFMAX - ZBUFMIN;
	a = z_Frustum.y / (z_Frustum.y - z_Frustum.x * zb_amplitude);
	b = z_Frustum.y * z_Frustum.x * zb_amplitude / (z_Frustum.x * zb_amplitude - z_Frustum.y);
	return b / ((zDepth * zb_amplitude + ZBUFMIN - a) * near);
}

vec3 normalize_color(vec3 in_color)
{
	float mx = max(max(in_color.r, in_color.g), in_color.b);
	return in_color / max(1.0, mx);
}

//Clouds texture ======================================================

float get_cloudTex_altitude(vec2 p)
{
	float a = texture2D(clouds_map, p).r;
	return a * clouds_scale.y;
}

vec3 get_cloudTex_normale(vec2 pos)
{
	float f = 0.02; //0.02 for rt noise
	vec2 xd = vec2(f, 0);
	vec2 zd = vec2(0, f);
	return normalize(vec3(
		get_cloudTex_altitude(pos - xd) - get_cloudTex_altitude(pos + xd),
		2.0 * f,
		get_cloudTex_altitude(pos - zd) - get_cloudTex_altitude(pos + zd)));
}

vec4 get_clouds_color(vec3 sun_c, vec3 pos, vec3 dir)
{
	float distance;
	vec4 c_cloud = vec4(0., 0., 0., 0.);
	if (pos.y > clouds_altitude.x && dir.y < -1e-4 || pos.y < clouds_altitude.x && dir.y > 1e-4)
	{
		distance = (clouds_altitude.x - pos.y) / dot(vec3(0.0, 1.0, 0.0), dir);
		vec2 p = (pos + distance * dir).xz * clouds_scale.xz;
		vec3 n_cloud = get_cloudTex_normale(p);
		c_cloud = vec4(1.0, 1.0, 1.0, texture2D(clouds_map, p).r);

		if (pos.y < clouds_altitude.x)
			n_cloud.y *= -1.0;

		float light_cloud = dot(sun_dir.xyz, -n_cloud);
		vec3 dark_color = mix(sun_c.xyz, ambient_color.xyz, clouds_absorption.x);

		if (light_cloud < 0.0)
			c_cloud.xyz = mix(dark_color, sun_c.xyz, (1.0 - c_cloud.a) * -1.0 * light_cloud);
		else
			c_cloud.xyz = mix(dark_color, sun_c.xyz, light_cloud);
	}
	return c_cloud;
}

//========================================




float get_geodesic_distance(float angle, float distance)
{
	return planet_radius.x * asin(distance * sin(angle) / planet_radius.x);
}

float get_geodesic_distance_far(float angle, float altitude, float distance_far)
{
	return planet_radius.x * acos(1 + (altitude - distance_far * cos(angle)) / planet_radius.x);
}

float get_distance(float r, float a, float h)
{
	return  (r + h) * cos(a) - r * sin(acos(sin(a) * (r + h) / r));
}

float get_distance_far(float r, float a, float h)
{
	return  -get_distance(r,a - M_PI, h);
}

// Get spherical coordinate texel:


vec4 get_sky_texel(vec3 dir, float angle_a_f, float atm_f)
{

	float t = mix(0.0, clamp(pow(angle_a_f / atmosphere_params.w, atmosphere_params.z), 0.0, 1.0), atm_f);

	float phi = M_PI / 2.0 - acos(abs(dir.y));
	if (dir.y<0.0) phi = -phi;

	float theta = atan2(dir.z,dir.x);

	vec2 uv_s = vec2(theta / (2*M_PI), -phi / M_PI ) + vec2(0.5,0.5);

	vec4 t_sky = texture2DLod(tex_sky, uv_s, 0) * tex_sky_intensity.x;
	vec4 t_space = texture2DLod(tex_space, uv_s, 0) * tex_space_intensity.x;
	return mix(t_sky, t_space, t);
}


float get_sun_intensity(vec3 dir, vec3 sun_dir, float alt_f)
{
	float glow_f = mix(sun_params.z, sun_params.w, alt_f);
	float prod_scal = max(dot(sun_dir, -dir), 0);
	float angle = acos(prod_scal) / M_PI * 180.0;
	float sun = 1.0 - smoothstep(sun_params.x, sun_params.x + sun_params.y, angle);
	return min(sun +  glow_f * 0.5 * pow(prod_scal,7000.0) + pow(glow_f, 2.0) * 0.4 * pow(prod_scal, 50.0) + pow(glow_f, 3.0) * 0.3 * pow(prod_scal, 2.0), 1.0);
}

float linear_smoothstep(float vmin,float vmax,float v)
{
	return clamp((v-vmin) / (vmax-vmin), 0.0, 1.0);
}

vec3 get_atmosphere_color(float angle_a, float alt_f)
{
	float t = pow( angle_a / atmosphere_params.w, atmosphere_params.y);
	vec3 space_c = mix(high_atmosphere_color.xyz, space_color.xyz, alt_f);
	vec3 atm_c = mix(low_atmosphere_color.xyz, high_atmosphere_color.xyz, linear_smoothstep(low_atmosphere_pos.x, high_atmosphere_pos.x, t));
	atm_c = mix(atm_c, space_c.xyz, linear_smoothstep(high_atmosphere_pos.x, 1.0, t));	
	return atm_c;
}

float noise_2d_textures(vec2 pa)
{
	float time = uClock.r;
	vec2 p = vec2(pa.x, pa.y) * sea_scale.xz;
	float disp = texture2D(sea_noises, p / 4.0 + vec2(time * 0.01, time * 0.004)).b;
	vec2 p_disp = p + vec2(disp * 0.06, disp * 0.07);
	vec2 noise_2_disp = vec2(time * 0.025, time * 0.001);
	float a = texture2D(sea_noises, p_disp / 2.0).r;
	a += texture2D(sea_noises, p_disp + noise_2_disp).g;
	a += texture2D(sea_noises, p / 10.0).r;
	a /= 3.0;
	return a;
}

float get_wave_altitude(vec2 p)
{
	float a = noise_2d_textures(p);
	return a * sea_scale.y;
}

vec3 rotate_vector(vec3 v, vec3 axis, float angle)
{
	vec3 axisn = normalize(axis);
	float dot_prod = dot(v, axisn);
	float cos_angle = cos(angle);
	float sin_angle = sin(angle);
	float f1=(1.0 - cos_angle) * dot_prod;

	return vec3(
		cos_angle * v.x + sin_angle * (axisn.y * v.z - axisn.z * v.y) + f1 * axisn.x,
		cos_angle * v.y + sin_angle * (axisn.z * v.x - axisn.x * v.z) + f1 * axisn.y,
		cos_angle * v.z + sin_angle * (axisn.x * v.y - axisn.y * v.x) + f1 * axisn.z
		);
}

vec3 get_normale_plane(vec2 p_surface)
{
	float f = 0.5; //0.02 for rt noise
	vec2 xd = vec2(f, 0.0);
	vec2 zd = vec2(0.0, f);
	return normalize(vec3(
		get_wave_altitude(p_surface - xd) - get_wave_altitude(p_surface + xd),
		4.0 * f,
		get_wave_altitude(p_surface - zd) - get_wave_altitude(p_surface + zd)));
}

vec3 get_normale_sphere(vec3 p_surface, vec3 pos)
{
	return normalize(p_surface - vec3(pos.x, -planet_radius.x, pos.z));
}

vec3 get_perturbed_normale_sphere(vec3 nplane, vec3 nsphere)
{
	vec3 m = cross(vec3(0.0, 1.0, 0.0), nsphere);
	float a = length(m);
	vec3 n;
	if (a > 1e-4) n = rotate_vector(nplane, normalize(m), asin(a));
	else n = nplane;
	return n;
}


vec3 get_sky_color(vec3 dir, vec3 sun_c, float angle_a)
{
	float atm_f = clamp(cam_position.w, 0.0, 1.0);
	vec3 c_atmosphere = get_atmosphere_color(angle_a, atm_f);
	float sky_lum = c_atmosphere.r * LUM_R + c_atmosphere.g * LUM_G + c_atmosphere.b * LUM_B;
	vec3 sky_col = get_sky_texel(dir, angle_a, atm_f).xyz;
	float sun_lum = get_sun_intensity(dir, sun_dir.xyz, atm_f);
	c_atmosphere = mix(c_atmosphere + sky_col * (1 - sky_lum), sun_c, sun_lum);

	vec4 clouds_color = get_clouds_color(sun_c, cam_position.xyz, dir) * (1.0 - step(clouds_altitude.x, cam_position.y));
	c_atmosphere = mix(c_atmosphere, clouds_color.xyz, clouds_color.a * (1.0 - atm_f));

	c_atmosphere = mix(horizon_line_color.xyz, c_atmosphere, linear_smoothstep(0.0, horizon_line_params.x, pow( angle_a / atmosphere_params.w, horizon_line_params.y)));
	return c_atmosphere;
}

vec3 get_sea_color(vec3 sun_c, vec2 screen_coords, vec3 pos, vec3 dir, vec3 screen_dir, float distance_plane, float distance_sphere, float distance_mix, float angle_f, float plane_f, float geodesic_distance)
{	
	vec3 c_sky;
	vec2 plane_pos = (pos + dir * distance_plane).xz;
	vec2 sphere_pos = pos.xz + normalize(dir.xz) * geodesic_distance;
	vec2 p_surface = mix(sphere_pos, plane_pos, plane_f);
	vec3 nplane = get_normale_plane(p_surface);
	vec3 nsphere = get_normale_sphere(pos + dir * distance_sphere, pos);
	vec3 n = mix(get_perturbed_normale_sphere(nplane, nsphere), nplane, plane_f);
	vec3 n0 = mix(nsphere, vec3(0,1,0), plane_f);
	vec3 dir_r = reflect(dir, n);
	float angle_r = acos(dot(dir_r, -n0));
	float angle_a = angle_r - horizon_angle.x;

	vec3 c_sea = mix(sea_color.xyz, underwater_color.xyz, pow(min(1.0, angle_f), 1.0)); // Underwater color
	float sun_lum = get_sun_intensity(dir_r, sun_dir.xyz, 0.0);

	if (scene_reflect.x > 0.5)
	{
		vec2 coordsTexReflect = clamp(vec2(screen_coords.x + n.x * reflect_offset.x / distance_plane, screen_coords.y + n.z * reflect_offset.x / distance_plane), vec2(0.0, 0.0), vec2(1.0, 1.0));
		float zDepth = texture2D(reflect_map_depth, coordsTexReflect).r; //z_Frustum.y*0.98;
		float z = get_zFromDepth(screen_dir.z, zDepth);
		float d = z / length(screen_dir.xz);
		c_sky = texture2D(reflect_map, coordsTexReflect).xyz;
		//if (z > z_Frustum.y * 0.99 || d < distance_plane)
		if (c_sky.r > 0.98 && c_sky.g < 0.1 && c_sky.b < 0.1)
		{
			c_sky = get_atmosphere_color(pow( angle_a / atmosphere_params.w, atmosphere_params.y), 0.0);
			c_sky = mix(c_sky, sun_c.xyz, sun_lum);
			//c_sky = texture2D(reflect_map, coordsTexReflect) * reflect_color.xyz;
		}
		else
		{
			//c_sky = texture2D(reflect_map, coordsTexReflect) * reflect_color.xyz;
			c_sky = c_sky * reflect_color.xyz;
		}
	}
	else
	{
		c_sky = get_atmosphere_color(pow( angle_a / atmosphere_params.w, atmosphere_params.y), 0.0);
		c_sky = mix(c_sky, sun_c.xyz, sun_lum);
	}

	float fresnel = (0.04 + (1.0 - 0.04) * (pow(1.0 - max(0.0, dot(dir, -n)), 5.0)));
	c_sea = mix(c_sky, c_sea, ((1.0 - fresnel) * sea_reflection.x + (1 - sea_reflection.x)));
	float te = texture2D(stream_texture, p_surface / 100000.0).b * 0.1;
	vec3 c_stream = vec3(te, te, te); //stream_texture
	//
	vec2 terrain_uv = (p_surface - terrain_position.xz) / terrain_scale.xz;
	vec4 c_terrain = texture2D(terrain_map, terrain_uv);
	float terrain_coast_height = smoothstep(terrain_edges.x, terrain_edges.y, c_terrain.a);
	vec3 c_terrain_intensity = c_terrain.xyz * terrain_scale.w;
	c_terrain.xyz = mix(c_terrain_intensity, c_terrain.xyz, terrain_coast_height);
	float terrain_clamp = smoothstep(0.0, terrain_edges.z, c_terrain.a) * step(0.0, terrain_uv.x) * (1.0 - step(1.0, terrain_uv.x)) * step(0.0, terrain_uv.y) * (1.0 - step(1., terrain_uv.y));
	float terrain_luminosity = mix(c_terrain.r * LUM_R + c_terrain.g * LUM_G + c_terrain.b * LUM_B, 1., terrain_coast_height);
	c_terrain.xyz = DistanceFog(screen_dir * distance_mix, c_terrain.xyz);
	//

	c_sea = min(c_sea + c_stream, vec3(1.0, 1.0, 1.0));
	c_sea = mix(c_sea, sun_c.xyz, sun_lum);
	c_sea = mix(c_sea, c_terrain.xyz, terrain_luminosity * terrain_clamp);

	c_sea = mix(horizon_line_color.xyz, c_sea, pow(smoothstep(0.0, horizon_low_line_params.x, 1.0 - angle_f),horizon_low_line_params.y));

	return c_sea;
}

//================================== MAIN

void main()
{

	//--- Get ray direction:
	
	vec3 screen_ray_dir = normalize(screen_ray);
	vec3 dir = normalize(mul(cam_normal, vec4(screen_ray_dir, 1.0).xyz));

	//--- Render Sea / Sky - Raymarch

	

	vec3 normalized_sun_color = normalize_color(sun_color.xyz);
	vec3 color;
	vec4 clouds_color;
	float distance;
	
	
	float ray_angle = acos(-dir.y);
	float alt_f = clamp(cam_position.w,0.0,1.0);

	if (ray_angle > horizon_angle.x)
	{
		distance = z_Frustum.y * 0.99;
		color = get_sky_color(dir, normalized_sun_color, ray_angle - horizon_angle.x);
		
	}
	else
	{
		float angle_f = ray_angle / horizon_angle.x;
		float dist_f = clamp(cam_position.y / planet_radius.x, 0.0,1.0);
		
		// Compute planar / spherical fading
		float ratio = cam_position.y / planet_radius.x;
		float plane_end = 1.0 - smoothstep(1e-3, 1e-2, ratio);
		float plane_smooth_size = 1.0 - smoothstep(1e-2, 5e-2, ratio);
		float plane_f = 1.0 - smoothstep(plane_end,plane_end + plane_smooth_size,angle_f);
		
		// Compute distance
		float distance_plane = cam_position.y / abs(dir.y);
		float distance_sphere = get_distance(planet_radius.x, ray_angle, cam_position.y);
		distance = mix(distance_sphere, distance_plane, plane_f);
		
		// Compute geodesic distance
		float gd = get_geodesic_distance(ray_angle, distance_sphere);
		color = get_sea_color(normalized_sun_color, uv, cam_position.xyz, dir, screen_ray_dir, distance_plane, distance_sphere, distance, angle_f, plane_f, gd);
		clouds_color = get_clouds_color(normalized_sun_color, cam_position.xyz, dir);
		color = mix(color, clouds_color.xyz, clouds_color.a * (1.0-alt_f));

	}
	
	/*
	distance = z_Frustum.y * 0.99;
	if (dir.y < 1e-5)
	{
		distance = cam_position.y / dot(vec3(0.0, -1.0, 0.0), dir);
		vec2 plane_pos = (cam_position + dir * distance).xz;
		vec2 terrain_uv = (plane_pos - terrain_position.xz) / terrain_scale.xz;
		vec4 c_terrain = texture2D(terrain_map, terrain_uv);
		color = vec3(c_terrain.r, c_terrain.g, c_terrain.b);
	}
	else
	{
		color = low_atmosphere_color.xyz;
	}
	*/
	//vec3 vp = screen_ray_dir * distance;
	//float z = min(vp.z, z_Frustum.y * 0.99);
	//gl_FragDepth = (1.0 / z - 1.0 / z_Frustum.x) / (1.0 / z_Frustum.y - 1.0 / z_Frustum.x);
	gl_FragDepth = get_zDepth(screen_ray_dir.z, min(distance, z_Frustum.y * 0.99));
	//color = vec3(clamp(pos_test.x,0.0,1.0), 0.0, 0.0);
	//color = vec3(1.0, 0.0, 0.0);
	gl_FragColor = vec4(color, 1.0);
}
