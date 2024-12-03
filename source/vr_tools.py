# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg

class VRState:

	def __init__(self):

		body_mtx = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(0, 0, 0))
		vr_state = hg.OpenVRGetState(body_mtx, 1, 1000)
		# Local head initial matrix:
		self.head_matrix = vr_state.head
		self.initial_head_matrix = hg.TransformationMat4(hg.GetT(self.head_matrix), hg.GetRotationMatrix(self.head_matrix))  # hg.InverseFast(vr_state.body) * vr_state.head
		# Local eyes offsets:
		self.eye_left_offset = vr_state.left.offset
		self.eye_right_offset = vr_state.right.offset
		# Fov
		vs_left, vs_right = hg.OpenVRStateToViewState(vr_state)
		vr_ratio = hg.Vec2(1 , 0.75)

		self.fov_left = hg.ZoomFactorToFov(hg.ExtractZoomFactorFromProjectionMatrix(vs_left.proj, vr_ratio))
		self.fov_right = hg.ZoomFactorToFov(hg.ExtractZoomFactorFromProjectionMatrix(vs_right.proj, vr_ratio))
		self.resolution = hg.Vec2(vr_state.width, vr_state.height)
		self.ratio = hg.Vec2(self.resolution.x / self.resolution.y, 1)

	def update_initial_head_matrix(self):
		self.initial_head_matrix = hg.TransformationMat4(hg.GetT(self.head_matrix), hg.GetRotationMatrix(self.head_matrix))  # hg.InverseFast(self.body_matrix) * self.head_matrix

	# !! Call ONE TIME by frame !!
	def update(self):
		body_mtx = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(0, 0, 0))
		vr_state = hg.OpenVRGetState(body_mtx, 1, 1000)
		vs_left, vs_right = hg.OpenVRStateToViewState(vr_state)
		vr_ratio = hg.Vec2(1 , 0.75)
		self.fov_left = hg.ZoomFactorToFov(hg.ExtractZoomFactorFromProjectionMatrix(vs_left.proj, vr_ratio))
		self.fov_right = hg.ZoomFactorToFov(hg.ExtractZoomFactorFromProjectionMatrix(vs_right.proj, vr_ratio))
		self.head_matrix = vr_state.head
		self.eye_left_offset = vr_state.left.offset
		self.eye_right_offset = vr_state.right.offset


class VRViewState:
	def __init__(self, camera:hg.Node, vr_view: VRState):
		self.z_near = 0
		self.z_far = 0
		self.head_matrix = None
		self.initial_head_matrix = None
		self.eye_left = None
		self.eye_right = None
		self.vs_left = None
		self.vs_right = None
		self.update(camera, vr_view)

	def update(self, camera, vr_view):
		cam = camera.GetCamera()
		self.z_near = cam.GetZNear()
		self.z_far = cam.GetZFar()

		# Compute current head matrix relative to initial_head_matrix
		local_head_matrix = hg.InverseFast(vr_view.initial_head_matrix) * vr_view.head_matrix

		# World head:
		self.head_matrix = camera.GetTransform().GetWorld() * local_head_matrix
		self.initial_head_matrix = camera.GetTransform().GetWorld()

		# World eyes:
		self.eye_left = self.head_matrix * vr_view.eye_left_offset
		self.eye_right = self.head_matrix * vr_view.eye_right_offset

		# View states:
		self.vs_left = hg.ComputePerspectiveViewState(self.eye_left, vr_view.fov_left, self.z_near, self.z_far, vr_view.ratio)
		self.vs_right = hg.ComputePerspectiveViewState(self.eye_right, vr_view.fov_right, self.z_near, self.z_far, vr_view.ratio)


