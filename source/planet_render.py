# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
import data_converter as dc
import json
from math import pi, atan, sqrt, exp, pow, cos, sin, acos, asin
import os

from vr_tools import *


class PlanetRender:
	def __init__(self, scene, resolution: hg.Vec2, terrain_position, terrain_offset):  # , pipeline_resource:hg.PipelineResource):

		# Vertex model:
		vs_decl = hg.VertexLayout()
		vs_decl.Begin()
		vs_decl.Add(hg.A_Position, 3, hg.AT_Float)
		vs_decl.Add(hg.A_Normal, 3, hg.AT_Uint8, True, True)
		vs_decl.End()

		self.uniforms_list = hg.UniformSetValueList()
		self.textures_list = hg.UniformSetTextureList()

		#self.quad_mdl = hg.CreateCubeModel(vs_decl, resolution.x / resolution.y * 2, 2, 0.01)
		self.quad_mdl = hg.CreatePlaneModel(vs_decl,  resolution.x / resolution.y * 2, 2, 1, 1)
		self.quad_matrix = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(hg.Deg(-90), hg.Deg(0), hg.Deg(0)), hg.Vec3(1, 1, 1))
		self.sky_sea_render = hg.LoadProgramFromAssets("shaders/planet_render")

		self.scene = scene

		self.planet_radius = 6000000
		self.atmosphere_thickness = 100000
		self.atmosphere_falloff = 0.2
		self.atmosphere_luminosity_falloff = 0.2
		self.sun_light = scene.GetNode("Sun")

		#Atmosphere
		self.space_color = hg.Color(2 / 255, 2 / 255, 4 / 255, 1)
		self.high_atmosphere_color = hg.Color(17 / 255, 56 / 255, 155 / 255, 1)
		self.low_atmosphere_color = hg.Color(76 / 255, 128 / 255, 255 / 255, 1)
		self.horizon_line_color = hg.Color(1, 1, 1, 1)

		self.high_atmosphere_pos = 0.75
		self.low_atmosphere_pos = 0.5
		self.horizon_line_pos = 0.1
		self.horizon_line_falloff = 0.2

		self.horizon_low_line_size = 0.1
		self.horizon_low_line_falloff = 0.2

		self.tex_sky_intensity = 1
		self.tex_space_intensity = 0

		# clouds
		self.clouds_scale = hg.Vec3(50000., 0.117, 40000.)
		self.clouds_altitude = 3000
		self.clouds_absorption = 0.145

		# Sun

		self.sun_size = 2
		self.sun_smooth = 0.1
		self.sun_glow = 1
		self.sun_space_glow_intensity = 0.25

		# Sea
		self.sea_color = hg.Color(19 / 255, 39 / 255, 89 / 255, 1)
		self.underwater_color = hg.Color(76 / 255, 128 / 255, 255 / 255, 1)
		self.sea_reflection = 0.5
		self.reflect_color = hg.Color(0.464, 0.620, 1, 1)
		self.scene_reflect = 0
		self.sea_scale = hg.Vec3(0.02, 16, 0.005)
		self.render_sea = 1
		self.render_scene_reflection = False
		self.reflect_map = None
		self.reflect_map_depth = None
		self.reflect_offset = 50

		# Terrain
		self.terrain_scale = hg.Vec3(41480, 1000, 19587)
		self.terrain_position = terrain_position + terrain_offset
		self.terrain_intensity = 0.5
		self.terrain_clamp = 0.01
		self.terrain_coast_edges = hg.Vec2(0.1, 0.3)

		# Textures:
		self.sea_texture = hg.LoadTextureFromAssets("textures/ocean_noises.png", 0)[0]
		self.stream_texture = hg.LoadTextureFromAssets("textures/stream.png", 0)[0]
		self.clouds_map = hg.LoadTextureFromAssets("textures/clouds_map.png", 0)[0]
		self.tex_sky = hg.LoadTextureFromAssets("textures/clouds.png", 0)[0]
		self.tex_space = hg.LoadTextureFromAssets("textures/8k_stars_milky_way.jpg", 0)[0]
		self.tex_terrain = hg.LoadTextureFromAssets("island_chain/textureRVBA.png", 0)[0]

	def gui(self, cam_pos):
		if hg.ImGuiBegin("Sea & Sky render Settings"):

			hg.ImGuiSetWindowPos("Sea & Sky render Settings", hg.Vec2(10, 390), hg.ImGuiCond_Once)
			hg.ImGuiSetWindowSize("Sea & Sky render Settings", hg.Vec2(650, 600), hg.ImGuiCond_Once)

			d, f = hg.ImGuiDragVec3("Camera pos", cam_pos, 100)
			if d: cam_pos = f

			if hg.ImGuiButton("Load sea parameters"):
				self.load_json_script()
			hg.ImGuiSameLine()
			if hg.ImGuiButton("Save sea parameters"):
				self.save_json_script()

			hg.ImGuiSeparator()

			d, f = hg.ImGuiSliderFloat("Planet radius", self.planet_radius, 1000, 6000000)
			if d: self.planet_radius = f
			d, f = hg.ImGuiInputFloat("Atmosphere thickness", self.atmosphere_thickness)
			if d: self.atmosphere_thickness = f

			hg.ImGuiSeparator()

			d, f = hg.ImGuiSliderFloat("Sky texture intensity", self.tex_sky_intensity, 0, 1)
			if d: self.tex_sky_intensity = f
			d, f = hg.ImGuiSliderFloat("Space texture intensity", self.tex_space_intensity, 0, 1)
			if d: self.tex_space_intensity = f

			hg.ImGuiSeparator()

			f, c = hg.ImGuiColorEdit("Space color", self.space_color)
			if f: self.space_color = c
			f, c = hg.ImGuiColorEdit("High atmosphere color", self.high_atmosphere_color)
			if f: self.high_atmosphere_color = c
			f, c = hg.ImGuiColorEdit("Low atmosphere color", self.low_atmosphere_color)
			if f: self.low_atmosphere_color = c
			f, c = hg.ImGuiColorEdit("Horizon line color", self.horizon_line_color)
			if f: self.horizon_line_color = c

			hg.ImGuiSeparator()

			d, f = hg.ImGuiSliderFloat("Atmosphere falloff", self.atmosphere_falloff, 0, 2)
			if d: self.atmosphere_falloff = f
			d, f = hg.ImGuiSliderFloat("Atmosphere luminosity falloff", self.atmosphere_luminosity_falloff, 0, 2)
			if d: self.atmosphere_luminosity_falloff = f
			d, f = hg.ImGuiSliderFloat("High atmosphere pos", self.high_atmosphere_pos, 0, 1)
			if d: self.high_atmosphere_pos = f
			d, f = hg.ImGuiSliderFloat("Low atmosphere pos", self.low_atmosphere_pos, 0, 1)
			if d: self.low_atmosphere_pos = f
			d, f = hg.ImGuiSliderFloat("horizon line falloff", self.horizon_line_pos, 0, 1)
			if d: self.horizon_line_pos = f
			d, f = hg.ImGuiSliderFloat("horizon line pos", self.horizon_line_falloff, 0, 2)
			if d: self.horizon_line_falloff = f

			hg.ImGuiSeparator()

			d, f = hg.ImGuiSliderFloat("horizon low line size", self.horizon_low_line_size, 0, 2)
			if d: self.horizon_low_line_size = f
			d, f = hg.ImGuiSliderFloat("horizon low line falloff", self.horizon_low_line_falloff, 0, 2)
			if d: self.horizon_low_line_falloff = f

			hg.ImGuiSeparator()

			d, f = hg.ImGuiSliderFloat("Sun size", self.sun_size, 0.1, 10)
			if d: self.sun_size = f
			d, f = hg.ImGuiSliderFloat("Sun smooth", self.sun_smooth, 0, 10)
			if d: self.sun_smooth = f
			d, f = hg.ImGuiSliderFloat("Sun glow intensity", self.sun_glow, 0, 1)
			if d: self.sun_glow = f
			d, f = hg.ImGuiSliderFloat("Sun space glow intensity", self.sun_space_glow_intensity, 0, 1)
			if d: self.sun_space_glow_intensity = f

			hg.ImGuiSeparator()

			f, c = hg.ImGuiColorEdit("Near water color", self.sea_color)
			if f: self.sea_color = c
			f, c = hg.ImGuiColorEdit("Underwater color", self.underwater_color)
			if f: self.underwater_color = c
			f, c = hg.ImGuiColorEdit("Reflect color", self.reflect_color)
			if f: self.reflect_color = c

			hg.ImGuiSeparator()

			d, f = hg.ImGuiDragVec3("Clouds scale", self.clouds_scale, 1)
			if d: self.clouds_scale = f
			d, f = hg.ImGuiDragFloat("Clouds altitude", self.clouds_altitude, 0.1, 1, 100000)
			if d: self.clouds_altitude = f
			d, f = hg.ImGuiSliderFloat("Clouds absoption", self.clouds_absorption, 0, 1)
			if d: self.clouds_absorption = f

			hg.ImGuiSeparator()

			d, f = hg.ImGuiCheckbox("Water reflection", self.render_scene_reflection)
			if d:
				self.render_scene_reflection = f
				if self.render_scene_reflection:
					self.scene_reflect = 1
				else:
					self.scene_reflect = 0

			d, f = hg.ImGuiDragVec3("sea scale", self.sea_scale, 1)
			if d: self.sea_scale = f
			# Not implemented yet !
			d, f = hg.ImGuiSliderFloat("Sea reflection", self.sea_reflection, 0, 1)
			if d: self.sea_reflection = f
			d, f = hg.ImGuiSliderFloat("Reflect offset", self.reflect_offset, 1, 1000)
			if d: self.reflect_offset = f

			hg.ImGuiSeparator()

			d, f = hg.ImGuiSliderFloat("Terrain texture intensity", self.terrain_intensity, 0, 1)
			if d: self.terrain_intensity = f
			d, f = hg.ImGuiDragVec3("Terrain scale", self.terrain_scale, 1)
			if d: self.terrain_scale = f
			d, f = hg.ImGuiDragVec3("Terrain position", self.terrain_position, 1)
			if d: self.terrain_position = f
			d, f = hg.ImGuiDragVec2("Terrain coast_edges", self.terrain_coast_edges, 0.001)
			if d: self.terrain_coast_edges = f
			d, f = hg.ImGuiSliderFloat("Terrain clamp", self.terrain_clamp, 0, 1)
			if d: self.terrain_clamp = f


		hg.ImGuiEnd()
		return cam_pos

	def load_json_script(self, file_name="scripts/planet_parameters.json"):
		#file = hg.OpenText(file_name)
		file = open(file_name, "r")
		if not file:
			print("ERROR - Can't open json file : " + file_name)
		else:
			#json_script = hg.ReadString(file)
			json_script = file.read()
			#hg.Close(file)
			file.close()
			if json_script != "":
				script_parameters = json.loads(json_script)
				self.low_atmosphere_color = dc.list_to_color(script_parameters["low_atmosphere_color"])
				self.high_atmosphere_color = dc.list_to_color(script_parameters["high_atmosphere_color"])
				self.space_color = dc.list_to_color(script_parameters["space_color"])
				self.horizon_line_color = dc.list_to_color(script_parameters["horizon_line_color"])

				self.sun_size = script_parameters["sun_size"]
				self.sun_smooth = script_parameters["sun_smooth"]
				self.sun_glow = script_parameters["sun_glow"]
				self.sun_space_glow_intensity = script_parameters["sun_space_glow_intensity"]

				self.planet_radius = script_parameters["planet_radius"]
				self.atmosphere_thickness = script_parameters["atmosphere_thickness"]
				self.atmosphere_falloff = script_parameters["atmosphere_falloff"]
				self.atmosphere_luminosity_falloff = script_parameters["atmosphere_luminosity_falloff"]
				self.high_atmosphere_pos = script_parameters["high_atmosphere_pos"]
				self.low_atmosphere_pos = script_parameters["low_atmosphere_pos"]
				self.horizon_line_pos = script_parameters["horizon_line_pos"]
				self.horizon_line_falloff = script_parameters["horizon_line_falloff"]

				self.horizon_low_line_size = script_parameters["horizon_low_line_size"]
				self.horizon_low_line_falloff = script_parameters["horizon_low_line_falloff"]

				self.tex_sky_intensity = script_parameters["tex_sky_intensity"]
				self.tex_space_intensity = script_parameters["tex_space_intensity"]

				self.underwater_color = dc.list_to_color(script_parameters["underwater_color"])
				self.sea_color = dc.list_to_color(script_parameters["sea_color"])
				self.sea_scale = dc.list_to_vec3(script_parameters["sea_scale"])
				self.sea_reflection = script_parameters["sea_reflection"]
				self.reflect_offset = script_parameters["reflect_offset"]
				self.scene_reflect = script_parameters["scene_reflect"]
				self.reflect_color = dc.list_to_color(script_parameters["reflect_color"])

				self.terrain_intensity = script_parameters["terrain_intensity"]
				self.terrain_scale = dc.list_to_vec3(script_parameters["terrain_scale"])
				self.terrain_coast_edges = dc.list_to_vec2(script_parameters["terrain_coast_edges"])
				self.terrain_clamp = script_parameters["terrain_clamp"]
				self.terrain_position = dc.list_to_vec3(script_parameters["terrain_position"])

				self.clouds_scale = dc.list_to_vec3(script_parameters["clouds_scale"])
				self.clouds_altitude = script_parameters["clouds_altitude"]
				self.clouds_absorption = script_parameters["clouds_absorption"]

				if self.scene_reflect > 0.5:
					self.render_scene_reflection = True
				else:
					self.render_scene_reflection = False

	def save_json_script(self, output_filename="scripts/planet_parameters.json"):
		script_parameters = {
							"space_color": dc.color_to_list(self.space_color),
							"high_atmosphere_color": dc.color_to_list(self.high_atmosphere_color),
							"high_atmosphere_pos": self.high_atmosphere_pos,
							"low_atmosphere_color": dc.color_to_list(self.low_atmosphere_color),
							"low_atmosphere_pos": self.low_atmosphere_pos,
							"horizon_line_color": dc.color_to_list(self.horizon_line_color),
							"horizon_line_pos": self.horizon_line_pos,
							"horizon_line_falloff": self.horizon_line_falloff,

							"horizon_low_line_falloff": self.horizon_low_line_falloff,
							"horizon_low_line_size": self.horizon_low_line_size,

							"tex_sky_intensity": self.tex_sky_intensity,
							"tex_space_intensity": self.tex_space_intensity,

							"clouds_scale": dc.vec3_to_list(self.clouds_scale),
							"clouds_altitude": self.clouds_altitude,
							"clouds_absorption": self.clouds_absorption,

							"sea_color": dc.color_to_list(self.sea_color),
							"underwater_color": dc.color_to_list(self.underwater_color),
							"reflect_color": dc.color_to_list(self.reflect_color),
							"sea_reflection": self.sea_reflection,
							"sea_scale": dc.vec3_to_list(self.sea_scale),
							"reflect_offset": self.reflect_offset,
							"scene_reflect": self.scene_reflect,

							"sun_size": self.sun_size,
							"sun_smooth": self.sun_smooth,
							"sun_glow": self.sun_glow,
							"sun_space_glow_intensity": self.sun_space_glow_intensity,

							"terrain_intensity": self.terrain_intensity,
							"terrain_scale": dc.vec3_to_list(self.terrain_scale),
							"terrain_clamp": self.terrain_clamp,
							"terrain_coast_edges": dc.vec2_to_list(self.terrain_coast_edges),
							"terrain_position": dc.vec3_to_list(self.terrain_position),

							"planet_radius": self.planet_radius,
							"atmosphere_thickness": self.atmosphere_thickness,
							"atmosphere_falloff": self.atmosphere_falloff,
							"atmosphere_luminosity_falloff": self.atmosphere_luminosity_falloff
		}
		json_script = json.dumps(script_parameters, indent=4)
		file = open(output_filename, "w")
		
		#file = hg.OpenWrite(output_filename)
		if file:
			file.write(json_script)
			file.close()
			#hg.WriteString(file, json_script)
			#hg.Close(file)
			return True
		else:
			print("ERROR - Can't open json file : " + output_filename)
			return False

	def get_distance(self, r, altitude, angle):
		return (r + altitude) * cos(angle) - r * sin(acos(sin(angle) * (r + altitude) / r))

	def get_distance_far(self, r, altitude, angle):
		return -self.get_distance(r, altitude, angle - pi)

	def get_horizon_angle(self,r , altitude):
		alt = max(0, altitude)
		return (pi / 2.0) - atan(sqrt(alt * (alt + 2.0 * r)) / r)

	def get_atmosphere_view_thickness_max(self, horizon_angle, altitude):
		dmin = self.get_distance(self.planet_radius + self.atmosphere_thickness, altitude - self.atmosphere_thickness, horizon_angle)
		dmax = self.get_distance_far(self.planet_radius + self.atmosphere_thickness, altitude - self.atmosphere_thickness, horizon_angle)
		#print("dmin %f, dmax %f" % (dmin,dmax))
		if dmin <= 0:
			return dmax
		else:
			return dmax - dmin

	def get_atmosphere_angle(self, altitude, horizon_angle):
		f = altitude / max(1,self.atmosphere_thickness)
		if f<=1:
			return pi * (1 - f) + (pi / 2 * f) - horizon_angle
		else:
			return self.get_horizon_angle(self.planet_radius + self.atmosphere_thickness, altitude - self.atmosphere_thickness) - horizon_angle

	def get_atmosphere_size(self,altitude, size):
		return size * exp(-pow(altitude/self.atmosphere_thickness * 0.888, 2))

	def render_vr(self, view_id, vr_state: hg.OpenVRState, vs_left: hg.ViewState, vs_right: hg.ViewState, vr_left_fb, vr_right_fb, reflect_texture_left: hg.Texture = None, reflect_depth_texture_left: hg.Texture = None, reflect_texture_right: hg.Texture = None, reflect_depth_texture_right: hg.Texture = None):

		vr_resolution = hg.Vec2(vr_state.width, vr_state.height)
		eye_left = vr_state.head * vr_state.left.offset
		eye_right = vr_state.head * vr_state.right.offset

		focal_distance_left = hg.ExtractZoomFactorFromProjectionMatrix(vs_left.proj, hg.Vec2(1.0, 0.75))
		focal_distance_right = hg.ExtractZoomFactorFromProjectionMatrix(vs_right.proj, hg.Vec2(1.0, 0.75))

		cam_normal_left = hg.GetRotationMatrix(eye_left)
		cam_normal_right = hg.GetRotationMatrix(eye_right)
		cam_pos_left = hg.GetT(eye_left)
		cam_pos_right = hg.GetT(eye_right)

		# Left:
		z_near, z_far = hg.ExtractZRangeFromProjectionMatrix(vs_left.proj)
		z_ratio = (z_near + 0.01) / focal_distance_left
		self.update_shader(cam_pos_left, cam_normal_left, focal_distance_left, z_near, z_far, vr_resolution, reflect_texture_left, reflect_depth_texture_left)
		hg.SetViewFrameBuffer(view_id, vr_left_fb.GetHandle())
		hg.SetViewRect(view_id, 0, 0, int(vr_resolution.x), int(vr_resolution.y))
		hg.SetViewClear(view_id, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
		hg.SetViewTransform(view_id, hg.InverseFast(vr_state.left.offset), vs_left.proj)
		matrx = vr_state.left.offset * hg.TransformationMat4(hg.Vec3(0, 0, focal_distance_left * z_ratio), hg.Vec3(hg.Deg(-90), hg.Deg(0), hg.Deg(0)), hg.Vec3(1, 1, 1) * z_ratio)
		hg.DrawModel(view_id, self.quad_mdl, self.sky_sea_render, self.uniforms_list, self.textures_list, matrx)
		view_id += 1

		#Right
		z_near, z_far = hg.ExtractZRangeFromProjectionMatrix(vs_right.proj)
		z_ratio = (z_near + 0.01) / focal_distance_right
		self.update_shader(cam_pos_right, cam_normal_right, focal_distance_right, z_near, z_far, vr_resolution, reflect_texture_right, reflect_depth_texture_right)
		hg.SetViewFrameBuffer(view_id, vr_right_fb.GetHandle())
		hg.SetViewRect(view_id, 0, 0, int(vr_resolution.x), int(vr_resolution.y))
		hg.SetViewClear(view_id, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
		hg.SetViewTransform(view_id, hg.InverseFast(vr_state.right.offset), vs_right.proj)
		matrx = vr_state.right.offset * hg.TransformationMat4(hg.Vec3(0, 0, focal_distance_right * z_ratio), hg.Vec3(hg.Deg(-90), hg.Deg(0), hg.Deg(0)), hg.Vec3(1, 1, 1) * z_ratio)
		hg.DrawModel(view_id, self.quad_mdl, self.sky_sea_render, self.uniforms_list, self.textures_list, matrx)

		return view_id + 1

	def update_shader(self, cam_pos, cam_normal, focal_distance, z_near, z_far, resolution, reflect_texture: hg.Texture = None, reflect_depth_texture: hg.Texture = None):

		horizon_angle = self.get_horizon_angle(self.planet_radius, cam_pos.y)
		atmosphere_angle = self.get_atmosphere_angle(cam_pos.y, horizon_angle)

		self.uniforms_list.clear()

		self.uniforms_list.push_back(hg.MakeUniformSetValue("resolution", hg.Vec4(resolution.x, resolution.y, 0, 0)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("focal_distance", hg.Vec4(focal_distance, 0, 0, 0)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("cam_position", hg.Vec4(cam_pos.x, cam_pos.y, cam_pos.z, cam_pos.y / max(1,self.atmosphere_thickness))))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("cam_normal", cam_normal))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("z_Frustum", hg.Vec4(z_near, z_far, 0, 0)))

		self.uniforms_list.push_back(hg.MakeUniformSetValue("horizon_angle", hg.Vec4(horizon_angle, 0, 0, 0)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("planet_radius", hg.Vec4(self.planet_radius, 0, 0, 0)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("atmosphere_params", hg.Vec4(self.atmosphere_thickness, self.atmosphere_falloff, self.atmosphere_luminosity_falloff, atmosphere_angle)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("high_atmosphere_pos", hg.Vec4(self.high_atmosphere_pos, 0, 0, 0)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("low_atmosphere_pos", hg.Vec4(self.low_atmosphere_pos, 0, 0, 0)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("horizon_line_params", hg.Vec4(self.horizon_line_pos, self.horizon_line_falloff, 0, 0)))

		self.uniforms_list.push_back(hg.MakeUniformSetValue("horizon_low_line_params", hg.Vec4(self.horizon_low_line_size, self.horizon_low_line_falloff,0,0)))

		self.uniforms_list.push_back(hg.MakeUniformSetValue("clouds_scale", hg.Vec4(1 / self.clouds_scale.x, self.clouds_scale.y, 1 / self.clouds_scale.z, 0)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("clouds_altitude", hg.Vec4(self.clouds_altitude, 0, 0, 0)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("clouds_absorption", hg.Vec4(self.clouds_absorption, 0, 0, 0)))

		self.uniforms_list.push_back(hg.MakeUniformSetValue("tex_sky_intensity", hg.Vec4(self.tex_sky_intensity, 0, 0, 0)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("tex_space_intensity", hg.Vec4(self.tex_space_intensity, 0, 0, 0)))

		self.uniforms_list.push_back(hg.MakeUniformSetValue("sea_scale", hg.Vec4(self.sea_scale.x, self.sea_scale.y, self.sea_scale.z, 0)))

		self.uniforms_list.push_back(hg.MakeUniformSetValue("terrain_scale", hg.Vec4(self.terrain_scale.x, self.terrain_scale.y, -self.terrain_scale.z, self.terrain_intensity)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("terrain_position", hg.Vec4(self.terrain_position.x, self.terrain_position.y, self.terrain_position.z, 0)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("terrain_edges", hg.Vec4(self.terrain_coast_edges.x, self.terrain_coast_edges.y, self.terrain_clamp, 0)))

		# Colors:
		colors_uniforms = {"space_color", "high_atmosphere_color", "low_atmosphere_color", "horizon_line_color", "sea_color", "underwater_color", "reflect_color"}
		for cn in colors_uniforms:
			self.uniforms_list.push_back(hg.MakeUniformSetValue(cn, hg.Vec4(getattr(self, cn).r, getattr(self, cn).g, getattr(self, cn).b, getattr(self, cn).a)))

		amb = self.scene.environment.ambient
		self.uniforms_list.push_back(hg.MakeUniformSetValue("ambient_color", hg.Vec4(amb.r, amb.g, amb.b, amb.a)))

		sun_color = self.sun_light.GetLight().GetDiffuseColor()
		sun_dir = hg.GetZ(self.sun_light.GetTransform().GetWorld())
		self.uniforms_list.push_back(hg.MakeUniformSetValue("sun_color", hg.Vec4(sun_color.r, sun_color.g, sun_color.b, sun_color.a)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("sun_dir", hg.Vec4(sun_dir.x, sun_dir.y, sun_dir.z, 0)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("sun_params", hg.Vec4(self.sun_size, self.sun_smooth, self.sun_glow, self.sun_space_glow_intensity)))

		self.uniforms_list.push_back(hg.MakeUniformSetValue("reflect_offset", hg.Vec4(self.reflect_offset, 0, 0, 0)))
		if reflect_texture is None or reflect_depth_texture is None:
			flag_reflect = 0
		else:
			flag_reflect = self.scene_reflect
		self.uniforms_list.push_back(hg.MakeUniformSetValue("scene_reflect", hg.Vec4(flag_reflect, 0, 0, 0)))
		self.uniforms_list.push_back(hg.MakeUniformSetValue("sea_reflection", hg.Vec4(self.sea_reflection, 0, 0, 0)))

		# --- Setup textures:

		self.textures_list.clear()
		self.textures_list.push_back(hg.MakeUniformSetTexture("sea_noises", self.sea_texture, 0))
		self.textures_list.push_back(hg.MakeUniformSetTexture("stream_texture", self.stream_texture, 1))
		self.textures_list.push_back(hg.MakeUniformSetTexture("clouds_map", self.clouds_map, 2))
		self.textures_list.push_back(hg.MakeUniformSetTexture("tex_sky", self.tex_sky, 3))
		self.textures_list.push_back(hg.MakeUniformSetTexture("tex_space", self.tex_space, 4))
		if reflect_texture is not None:
			self.textures_list.push_back(hg.MakeUniformSetTexture("reflect_map", reflect_texture, 5))
		if reflect_depth_texture is not None:
			self.textures_list.push_back(hg.MakeUniformSetTexture("reflect_map_depth", reflect_depth_texture, 6))
		self.textures_list.push_back(hg.MakeUniformSetTexture("terrain_map", self.tex_terrain, 7))


	def render(self, view_id, camera: hg.Node, resolution: hg.Vec2, reflect_texture: hg.Texture = None, reflect_depth_texture: hg.Texture = None, frame_buffer=None):

		# Vars:
		cam = camera.GetCamera()
		if cam.GetIsOrthographic():
			focal_distance = camera.GetTransform().GetPos().y / (cam.GetSize() / 2)
		else:
			focal_distance = hg.FovToZoomFactor(cam.GetFov())
		cam_mat = camera.GetTransform().GetWorld()

		cam_normal = hg.GetRotationMatrix(cam_mat)
		cam_pos = hg.GetT(cam_mat)
		z_near = cam.GetZNear()
		z_far = cam.GetZFar()

		self.update_shader(cam_pos, cam_normal, focal_distance, z_near, z_far, resolution, reflect_texture, reflect_depth_texture)

		# --- Set View:
		if frame_buffer is not None:
			hg.SetViewFrameBuffer(view_id, frame_buffer.handle)
		hg.SetViewRect(view_id, 0, 0, int(resolution.x), int(resolution.y))
		#hg.SetViewClear(view_id, 0, 0x0, 1.0, 0)
		hg.SetViewClear(view_id, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
		cam = hg.TransformationMat4(hg.Vec3(0, 0, -focal_distance), hg.Vec3(0, 0, 0))

		view = hg.InverseFast(cam)
		proj = hg.ComputePerspectiveProjectionMatrix(0.1, 100, focal_distance, hg.Vec2(resolution.x / resolution.y, 1))
		hg.SetViewTransform(view_id, view, proj)
		hg.DrawModel(view_id, self.quad_mdl, self.sky_sea_render, self.uniforms_list, self.textures_list, self.quad_matrix)
		return view_id + 1
