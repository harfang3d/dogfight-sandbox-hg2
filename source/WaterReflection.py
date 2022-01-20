# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
import json
import data_converter as dc
from vr_tools import *


class WaterReflection():
	def __init__(self, scene, resolution: hg.Vec2, resources: hg.PipelineResources, flag_vr=False):
		self.flag_vr = flag_vr
		# Parameters:
		self.color = hg.Color(1, 0, 0, 1)
		self.reflect_level = 0.75

		self.camera_reflect = hg.CreateCamera(scene, hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(0, 0, 0)), 1, 10000)
		self.main_camera = None

		self.render_program = hg.LoadProgramFromAssets("shaders/copy")

		fb_aa = 4
		if not flag_vr:
			self.quad_frameBuffer = hg.CreateFrameBuffer(int(resolution.x), int(resolution.y), hg.TF_RGBA8, hg.TF_D32F, fb_aa, "frameBuffer_reflect")
		else:
			self.quad_frameBuffer_left = hg.CreateFrameBuffer(int(resolution.x), int(resolution.y), hg.TF_RGBA8, hg.TF_D32F, fb_aa, "frameBuffer_reflect_left")
			self.quad_frameBuffer_right = hg.CreateFrameBuffer(int(resolution.x), int(resolution.y), hg.TF_RGBA8, hg.TF_D32F, fb_aa, "frameBuffer_reflect_right")

	@staticmethod
	def get_plane_projection_factor(p: hg.Vec3, plane_origine: hg.Vec3, plane_normal: hg.Vec3):
		d = -plane_normal.x * plane_origine.x - plane_normal.y * plane_origine.y - plane_normal.z * plane_origine.z
		return -plane_normal.x * p.x - plane_normal.y * p.y - plane_normal.z * p.z - d

	def compute_reflect_matrix(self, mat):
		plane_pos = hg.Vec3(0, 0, 0)
		plane_normal = hg.Vec3(0, 1, 0)
		pos = hg.GetT(mat)
		t = self.get_plane_projection_factor(pos, plane_pos, plane_normal)
		pos_reflect = pos + plane_normal * 2 * t
		xAxis = hg.GetX(mat)
		zAxis = hg.GetZ(mat)
		px = pos + xAxis
		tx = self.get_plane_projection_factor(px, plane_pos, plane_normal)
		x_reflect = px + plane_normal * 2 * tx - pos_reflect
		z_reflect = hg.Reflect(zAxis, plane_normal)
		y_reflect = hg.Cross(z_reflect, x_reflect)
		mat_reflect = hg.TranslationMat4(pos_reflect)
		hg.SetX(mat_reflect, x_reflect)
		hg.SetY(mat_reflect, y_reflect)
		hg.SetZ(mat_reflect, z_reflect)
		return mat_reflect

	def set_camera(self, scene):
		self.main_camera = scene.GetCurrentCamera()
		mat_reflect = self.compute_reflect_matrix(self.main_camera.GetTransform().GetWorld())
		self.camera_reflect.GetTransform().SetWorld(mat_reflect)
		cam_org = self.main_camera.GetCamera()
		cam = self.camera_reflect.GetCamera()
		cam.SetFov(cam_org.GetFov())
		cam.SetZNear(cam_org.GetZNear())
		cam.SetZFar(cam_org.GetZFar())
		scene.SetCurrentCamera(self.camera_reflect)

	def compute_vr_reflect(self, camera, vr_state: hg.OpenVRState, vs_left: hg.ViewState, vs_right: hg.ViewState):

		eye_left = vr_state.head * vr_state.left.offset
		eye_right = vr_state.head * vr_state.right.offset

		mat_left_reflect = self.compute_reflect_matrix(eye_left)
		mat_right_reflect = self.compute_reflect_matrix(eye_right)

		fov_left = hg.ZoomFactorToFov(hg.ExtractZoomFactorFromProjectionMatrix(vs_left.proj))
		fov_right = hg.ZoomFactorToFov(hg.ExtractZoomFactorFromProjectionMatrix(vs_right.proj))

		znear = camera.GetCamera().GetZNear()
		zfar = camera.GetCamera().GetZFar()

		ratio = hg.Vec2(vr_state.width / vr_state.height, 1)

		vs_left_reflect = hg.ComputePerspectiveViewState(mat_left_reflect, fov_left, znear, zfar, ratio)
		vs_right_reflect = hg.ComputePerspectiveViewState(mat_right_reflect, fov_right, znear, zfar, ratio)

		return vs_left_reflect, vs_right_reflect

	def restore_camera(self, scene):
		scene.SetCurrentCamera(self.main_camera)

	def load_parameters(self, file_name="assets/scripts/water_reflection.json"):
		json_script = hg.GetFilesystem().FileToString(file_name)
		if json_script != "":
			script_parameters = json.loads(json_script)
			self.color = dc.list_to_color(script_parameters["color"])
			self.reflect_level = script_parameters["reflect_level"]

	def save_parameters(self, output_filename="assets/scripts/water_reflection.json"):
		script_parameters = {"color": dc.color_to_list(self.color), "reflect_level": self.reflect_level}
		json_script = json.dumps(script_parameters, indent=4)
		return hg.GetFilesystem().StringToFile(output_filename, json_script)
