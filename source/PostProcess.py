# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg


class PostProcess:
	def __init__(self, resolution, antialiasing = 4, flag_vr=False):
		# Setup frame buffers

		self.render_program = hg.LoadProgramFromAssets("shaders/copy")

		self.flag_vr = flag_vr

		# Render frame buffer
		if flag_vr:
			self.quad_frameBuffer_left = hg.CreateFrameBuffer(int(resolution.x), int(resolution.y), hg.TF_RGBA8, hg.TF_D32F, antialiasing, "frameBuffer_postprocess_left")  # hg.OpenVRCreateEyeFrameBuffer(hg.OVRAA_MSAA4x)
			self.quad_frameBuffer_right = hg.CreateFrameBuffer(int(resolution.x), int(resolution.y), hg.TF_RGBA8, hg.TF_D32F, antialiasing, "frameBuffer_postprocess_right")  # hg.OpenVRCreateEyeFrameBuffer(hg.OVRAA_MSAA4x)
		else:
			self.quad_frameBuffer = hg.CreateFrameBuffer(int(resolution.x), int(resolution.y), hg.TF_RGBA8, hg.TF_D32F, antialiasing, "frameBuffer_postprocess")

		# Setup 2D rendering
		self.quad_mdl = hg.VertexLayout()
		self.quad_mdl.Begin()
		self.quad_mdl.Add(hg.A_Position, 3, hg.AT_Float)
		self.quad_mdl.Add(hg.A_TexCoord0, 3, hg.AT_Float)
		self.quad_mdl.End()

		self.quad_model = hg.CreatePlaneModel(self.quad_mdl, 1, 1, 1, 1)
		self.quad_uniform_set_value_list = hg.UniformSetValueList()
		self.quad_uniform_set_texture_list = hg.UniformSetTextureList()
		self.quad_render_state = hg.ComputeRenderState(hg.BM_Opaque, hg.DT_Disabled, hg.FC_Disabled)
		self.quad_matrix = hg.TransformationMat4(hg.Vec3(0, 0, 1), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(resolution.x, 1, resolution.y))

		self.post_process_program = hg.LoadProgramFromAssets("shaders/post_process")

		self.color = hg.Vec4(1, 1, 1, 1)
		self.uv_scale = hg.Vec4(1, 1, 0, 0)
		self.fade_t = 0
		self.fade_f = 0
		self.fade_duration = 1
		self.fade_direction = 1
		self.fade_running = False

		self.quad_uniform_set_value_list.clear()
		self.quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("uv_scale", self.uv_scale))
		self.quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("color", self.color))

	def setup_fading(self, duration, direction):
		self.fade_duration = duration
		self.fade_direction = direction
		self.fade_running = True
		self.fade_t = 0

	def update_fading(self, dts):
		if self.fade_running:
			if self.fade_t >= self.fade_duration: self.fade_running = False
			self.fade_t += dts
			self.fade_f = min(1, self.fade_t / self.fade_duration)
			if self.fade_direction < 0: self.fade_f = 1 - self.fade_f
			self.quad_uniform_set_value_list.clear()
			c = self.color * self.fade_f
			c.w = 1
			self.quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("color", c))
			self.quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("uv_scale", self.uv_scale))

	def display(self, view_id, resources, resolution, custom_texture=None):
		hg.SetViewRect(view_id, 0, 0, int(resolution.x), int(resolution.y))
		hg.SetViewClear(view_id, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
		hg.SetViewFrameBuffer(view_id, hg.InvalidFrameBufferHandle)
		vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(0, 0, 0)), resolution.y, 0.1, 100, hg.ComputeAspectRatioX(resolution.x, resolution.y))
		hg.SetViewTransform(view_id, vs.view, vs.proj)
		self.quad_uniform_set_texture_list.clear()
		if custom_texture is None:
			self.quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.GetColorTexture(self.quad_frameBuffer), 0))
		else:
			self.quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", custom_texture, 0))
		hg.DrawModel(view_id, self.quad_model, self.post_process_program, self.quad_uniform_set_value_list, self.quad_uniform_set_texture_list, self.quad_matrix, self.quad_render_state)
		return view_id + 1

	def display_vr(self, view_id, vr_state: hg.OpenVRState, vs_left: hg.ViewState, vs_right: hg.ViewState, output_left_fb: hg.OpenVREyeFrameBuffer, output_right_fb: hg.OpenVREyeFrameBuffer, resources):

		focal_distance_left = hg.ExtractZoomFactorFromProjectionMatrix(vs_left.proj)
		focal_distance_right = hg.ExtractZoomFactorFromProjectionMatrix(vs_right.proj)

		z_near, z_far = hg.ExtractZRangeFromProjectionMatrix(vs_left.proj)
		z_ratio = (z_near + 0.01) / focal_distance_left
		hg.SetViewFrameBuffer(view_id, output_left_fb.GetHandle())
		hg.SetViewRect(view_id, 0, 0, int(vr_state.width), int(vr_state.height))
		hg.SetViewClear(view_id, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
		hg.SetViewTransform(view_id, hg.InverseFast(vr_state.left.offset), vs_left.proj)
		matrx = vr_state.left.offset * hg.TransformationMat4(hg.Vec3(0, 0, focal_distance_left * z_ratio), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(2, 2, 2) * z_ratio)
		self.quad_uniform_set_texture_list.clear()
		# self.quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.OpenVRGetColorTexture(self.quad_frameBuffer_left), 0))
		self.quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.GetColorTexture(self.quad_frameBuffer_left), 0))
		hg.DrawModel(view_id, self.quad_model, self.post_process_program, self.quad_uniform_set_value_list, self.quad_uniform_set_texture_list, matrx, self.quad_render_state)
		view_id += 1

		z_near, z_far = hg.ExtractZRangeFromProjectionMatrix(vs_right.proj)
		z_ratio = (z_near + 0.01) / focal_distance_right
		hg.SetViewFrameBuffer(view_id, output_right_fb.GetHandle())
		hg.SetViewRect(view_id, 0, 0, int(vr_state.width), int(vr_state.height))
		hg.SetViewClear(view_id, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
		hg.SetViewTransform(view_id, hg.InverseFast(vr_state.right.offset), vs_right.proj)
		matrx = vr_state.right.offset * hg.TransformationMat4(hg.Vec3(0, 0, focal_distance_right * z_ratio), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(2, 2, 2) * z_ratio)
		self.quad_uniform_set_texture_list.clear()
		# self.quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.OpenVRGetColorTexture(self.quad_frameBuffer_left), 0))
		self.quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.GetColorTexture(self.quad_frameBuffer_right), 0))
		hg.DrawModel(view_id, self.quad_model, self.post_process_program, self.quad_uniform_set_value_list, self.quad_uniform_set_texture_list, matrx, self.quad_render_state)
		return view_id + 1
