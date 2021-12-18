$input vWorldPos, vNormal, vTexCoord0, vTexCoord1, vTangent, vBinormal

#include <bgfx_shader.sh>

#define PI 3.14159265359


// Ocean
vec4 sea_scale;
vec4 zenith_color;
vec4 zenith_falloff;
vec4 horizonH_color;
vec4 horizonL_color;
vec4 horizon_line_color;
vec4 horizon_line_size;
vec4 sea_color;
vec4 reflect_color;
vec4 sea_reflection;
vec4 reflect_offset;
vec4 stream_scale;


uniform vec4 uClock;

// Lighting environment

uniform vec4 uLightPos[8]; // pos.xyz, 1.0/radius
uniform vec4 uLightDir[8]; // dir.xyz, inner_rim
uniform vec4 uLightDiffuse[8]; // diffuse.xyz, outer_rim
uniform vec4 uLightSpecular[8]; // specular.xyz, pssm_bias

// Surface attributes
uniform vec4 uDiffuseColor;
uniform vec4 uSpecularColor;

// Texture slots
SAMPLER2D(uDiffuseMap, 0); // PBR metalness in alpha
SAMPLER2D(uSpecularMap, 1); // PBR roughness in alpha

//

vec3 GetT(mat4 m) { return vec3(m[0][3], m[1][3], m[2][3]); }

//----------------------------------------------------------------------------------

float noise_2d_textures (vec2 pa)
{
	float time=uClock.r;
	vec2 p = vec2(pa.x,pa.y)*sea_scale.xz;
	float disp = texture2D(uDiffuseMap, p/4.+vec2(time*0.01,time*0.004)).b;
	vec2 p_disp = p+vec2(disp*0.06,disp*0.07);
	vec2 noise_2_disp = vec2(time*0.025,time*0.001);
	float a = texture2D(uDiffuseMap, p_disp/2.).r;
	a += texture2D(uDiffuseMap, p_disp+noise_2_disp).g;
	a+=texture2D(uDiffuseMap, p/10.).r;
	a/=3.;
	//a=texture2D(noise_texture, p).r;
	return a;
}


float get_wave_altitude(vec2 p)
{
	float a=noise_2d_textures(p);
	return a*sea_scale.y;
}
	
vec3 get_normale(vec2 pos)
{
	float f=0.5;//0.02 for rt noise
	vec2 xd=vec2(f,0);
	vec2 zd=vec2(0,f);
	return normalize(vec3(
							get_wave_altitude(pos-xd) - get_wave_altitude(pos+xd),
							2.*f,
							get_wave_altitude(pos-zd) - get_wave_altitude(pos+zd)
						  ));
}

float get_sun_intensity(vec3 dir, vec3 sun_dir)
{
	float prod_scal = max(dot(sun_dir,-dir),0);
	return min(0.4*pow(prod_scal,7000) + 0.5 * pow(prod_scal,50) + 0.4 *pow(prod_scal,2),1);
}

vec3 get_atmosphere_color(vec3 dir)
{
	vec3 c_atmosphere;
	if (dir.y<-1e-4)c_atmosphere=mix(sea_color.rgb,horizonL_color.rgb,pow(min(1.,1+dir.y),1.));
	else if(dir.y>=-1e-4 && dir.y<1e-4) c_atmosphere=horizonH_color.rgb;
	else c_atmosphere=mix(zenith_color.rgb,horizonH_color.rgb,pow(min(1.,1-dir.y),zenith_falloff.x));
	return c_atmosphere;
}

vec3 get_sea_color(vec3 pos, vec3 dir, vec3 sun_dir, vec3 sun_color)
{
	
	vec3 water_color;
	vec3 n = get_normale(pos.xz);
	vec2 coordsTexReflect=vec2(pos.x+n.x*reflect_offset.x,pos.z+n.z*reflect_offset.x);
	
	//vec4 scene_reflect_color;
				
	//if (scene_reflect==1) scene_reflect_color = texture2D(reflect_map, coordsTexReflect);
	//else
	vec4 scene_reflect_color = reflect_color;
	
	vec3 dir_r=reflect(dir,n);
	vec3 c_water=get_atmosphere_color(dir);
	vec3 c_sky;
	float sun_lum = get_sun_intensity(dir_r,sun_dir);
	
	c_sky=scene_reflect_color.rgb;
	
	float fresnel = (0.04 + (1.0-0.04)*(pow(1.0 - max(0.0, dot(dir,-n)), 5.0)));
	vec3 c_sea=mix(c_sky,c_water,((1.-fresnel)*sea_reflection.x + (1-sea_reflection.x)));
	vec3 c_stream = texture2D(uSpecularMap, pos.xz/stream_scale.x).rgb*0.1;
	sun_lum=min(sun_lum+c_stream.r,1.);
	c_sea=mix(c_sea,sun_color,sun_lum);
	c_sea = min(c_sea + c_stream,vec3(1.,1.,1.));
	
	//float a=noise_2d_textures(pos.xz);
	
	return c_sea;
}


//--------------------------------------------------------------------------------


// Entry point of the forward pipeline default uber shader (Phong and PBR)
void main() {
#if USE_DIFFUSE_MAP
	vec4 diff = texture2D(uDiffuseMap, vTexCoord0);
#else
	vec4 diff = uDiffuseColor;
#endif

#if USE_SPECULAR_MAP
	vec4 spec = texture2D(uSpecularMap, vTexCoord0);
#else
	vec4 spec = uSpecularColor;
#endif

	//
	vec3 P = vWorldPos; // fragment world pos
	vec3 V = normalize(GetT(u_invView) - P); // view vector

	vec3 color = get_sea_color(P, -V, uLightDir[0].xyz, uLightDiffuse[0].xyz);

	float opacity = 1.0;

	gl_FragColor = vec4(color, opacity);
}
