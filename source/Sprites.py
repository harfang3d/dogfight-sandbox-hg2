# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg


class Sprite:
	tex0_program = None
	spr_render_state = None
	spr_model = None
	vs_pos_tex0_decl = None

	@classmethod
	def init_system(cls):
		cls.tex0_program = hg.LoadProgramFromAssets("shaders/sprite.vsb", "shaders/sprite.fsb")

		cls.vs_pos_tex0_decl = hg.VertexLayout()
		cls.vs_pos_tex0_decl.Begin()
		cls.vs_pos_tex0_decl.Add(hg.A_Position, 3, hg.AT_Float)
		cls.vs_pos_tex0_decl.Add(hg.A_TexCoord0, 3, hg.AT_Float)
		cls.vs_pos_tex0_decl.End()
		cls.spr_model = hg.CreatePlaneModel(cls.vs_pos_tex0_decl, 1, 1, 1, 1)

		cls.spr_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Disabled, hg.FC_Disabled)

		cls.vr_size = None
		cls.vr_distance = 1


	@classmethod
	def setup_matrix_sprites2D(cls, vid, resolution: hg.Vec2):
		vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(resolution.x / 2, resolution.y / 2, 0)), resolution.y, 0.1, 100, hg.Vec2(resolution.x / resolution.y, 1))
		hg.SetViewTransform(vid, vs.view, vs.proj)

	def __init__(self, w, h, texture_path):
		self.width = w
		self.height = h
		self.texture_path = texture_path
		self.texture = hg.LoadTextureFromAssets(self.texture_path, 0)[0]
		self.texture_uniform = hg.MakeUniformSetTexture("s_tex", self.texture, 0)
		self.color = hg.Color(1, 1, 1, 1)
		self.uniform_set_value_list = hg.UniformSetValueList()
		self.uniform_set_texture_list = hg.UniformSetTextureList()
		self.uniform_set_texture_list.push_back(self.texture_uniform)
		self.color_set_value = hg.MakeUniformSetValue("color", hg.Vec4(self.color.r, self.color.g, self.color.b, self.color.a))
		self.uv_scale = hg.Vec2(1, 1)
		self.uv_scale_set_value = hg.MakeUniformSetValue("uv_scale", hg.Vec4(self.uv_scale.x, self.uv_scale.y, 0, 0))
		self.position = hg.Vec3(0, 0, 2)
		self.scale = hg.Vec3(self.width, 1, self.height)
		self.rotation = hg.Vec3(0, 0, 0)
		self.size = 1

	def compute_matrix(self):
		return hg.TransformationMat4(self.position, self.rotation) * hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(hg.Deg(90), 0, 0), self.scale * self.size)

	def set_position(self, x, y):
		self.position.x = x
		self.position.y = y

	def set_uv_scale(self, uv_scale: hg.Vec2):
		self.uv_scale = uv_scale
		self.uv_scale_set_value = hg.MakeUniformSetValue("uv_scale", hg.Vec4(self.uv_scale.x, self.uv_scale.y, 0, 0))

	def set_size(self, size):
		self.size = size

	def set_color(self, color: hg.Color):
		self.color = color
		self.color_set_value = hg.MakeUniformSetValue("color", hg.Vec4(self.color.r, self.color.g, self.color.b, self.color.a))

	def draw(self, v_id):
		self.uniform_set_value_list.clear()
		self.uniform_set_value_list.push_back(self.color_set_value)
		self.uniform_set_value_list.push_back(self.uv_scale_set_value)
		matrix = self.compute_matrix()
		hg.DrawModel(v_id, Sprite.spr_model, Sprite.tex0_program, self.uniform_set_value_list, self.uniform_set_texture_list, matrix, Sprite.spr_render_state)

	def draw_vr(self, v_id, vr_matrix, resolution, vr_hud):
		pos_vr = hg.Vec3((self.position.x / resolution.x - 0.5) * vr_hud.x, (self.position.y / resolution.y - 0.5) * vr_hud.y, vr_hud.z)
		scale_vr = hg.Vec3(self.scale.x / resolution.x * vr_hud.x, 1, self.scale.z / resolution.y * vr_hud.y)
		matrix = vr_matrix * hg.TransformationMat4(pos_vr, self.rotation) * hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(hg.Deg(90), 0, 0), scale_vr * self.size)

		self.uniform_set_value_list.clear()
		self.uniform_set_value_list.push_back(self.color_set_value)
		self.uniform_set_value_list.push_back(self.uv_scale_set_value)
		hg.DrawModel(v_id, Sprite.spr_model, Sprite.tex0_program, self.uniform_set_value_list, self.uniform_set_texture_list, matrix, Sprite.spr_render_state)