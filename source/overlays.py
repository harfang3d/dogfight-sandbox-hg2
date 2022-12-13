# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from math import atan, cos, sin, pi

class Overlays:

	uniforms_values_list = hg.UniformSetValueList()
	uniforms_textures_list = hg.UniformSetTextureList()
	flat_render_state = None

	# ================= Lines 3D
	vtx_decl_lines = None
	shader_flat = None
	lines = []

	# ================= Texts 3D
	font_program = None
	debug_font = None
	text_matrx = None
	texts3D_display_list = []
	texts2D_display_list = []

	# ================= Primitives 3D
	vtx_layout_flat = None
	vtx_flat = None
	uniforms_values_list = hg.UniformSetValueList()
	uniforms_textures_list = hg.UniformSetTextureList()
	circle_num_sections = 32
	primitives3D_display_list = []

	@classmethod
	def init(cls):
		cls.vtx_decl_lines = hg. VertexLayoutPosFloatColorFloat()
		cls.shader_flat = hg.LoadProgramFromAssets("shaders/pos_rgb")

		cls.font_program = hg.LoadProgramFromAssets("core/shader/font.vsb", "core/shader/font.fsb")
		cls.debug_font = hg.LoadFontFromAssets("font/default.ttf", 64)
		cls.text_matrx = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(hg.Deg(0), hg.Deg(0), hg.Deg(0)), hg.Vec3(1, -1, 1))
		cls.uniforms_values_list.push_back(hg.MakeUniformSetValue("u_color", hg.Vec4(1, 1, 0, 1)))
		cls.flat_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Disabled, hg.FC_Disabled)

		cls.vtx_layout_flat = hg. VertexLayoutPosFloatColorFloat()
		cls.vtx_flat = hg.Vertices(cls.vtx_layout_flat, cls.circle_num_sections + 1)

	@classmethod
	def display_named_vector(cls, position, direction, label, label_offset2D, color, label_size=0.012):
		if label != "":
			cls.add_text2D_from_3D_position(label, position, label_offset2D, label_size, color)
		cls.add_line(position, position + direction, color, color)

	@classmethod
	def display_vector(cls, position, direction, color0=hg.Color.Yellow, color1=hg.Color.Orange):
		cls.lines.append([position, position + direction, color0, color1])

	@classmethod
	def display_boxe(cls, vertices, color):
		links = [0, 1,
				 1, 2,
				 2, 3,
				 3, 0,
				 5, 6,
				 6, 7,
				 7, 4,
				 4, 5,
				 0, 4,
				 1, 5,
				 2, 6,
				 3, 7]
		for i in range(len(links) // 2):
			cls.lines.append([vertices[links[i * 2]], vertices[links[i * 2 + 1]], color, color])

	@classmethod
	def add_line(cls, p0, p1, c0, c1):
		cls.lines.append([p0, p1, c0, c1])

	@classmethod
	def draw_lines(cls, vid):
		vtx = hg.Vertices(cls.vtx_decl_lines, len(cls.lines) * 2)
		for i, line in enumerate(cls.lines):
			vtx.Begin(i * 2).SetPos(line[0]).SetColor0(line[2]).End()
			vtx.Begin(i * 2 + 1).SetPos(line[1]).SetColor0(line[3]).End()
		hg.DrawLines(vid, vtx, cls.shader_flat)

	@classmethod
	def display_physics_debug(cls, vid, physics):
		physics.RenderCollision(vid, cls.vtx_decl_lines, cls.shader_flat, hg.ComputeRenderState(hg.BM_Opaque, hg.DT_Disabled, hg.FC_Disabled), 1)

	@classmethod
	def get_2d(cls, camera, point3d: hg.Vec3, resolution: hg.Vec2):
		cam_mat = camera.GetTransform().GetWorld()
		view_matrix = hg.InverseFast(cam_mat)
		c = camera.GetCamera()
		projection_matrix = hg.ComputePerspectiveProjectionMatrix(c.GetZNear(), c.GetZFar(), hg.FovToZoomFactor(c.GetFov()), hg.Vec2(resolution.x / resolution.y, 1))
		pos_view = view_matrix * point3d
		f, pos2d = hg.ProjectToScreenSpace(projection_matrix, pos_view, resolution)
		if f:
			return hg.Vec2(pos2d.x, pos2d.y) / resolution
		else:
			return None

	@classmethod
	def get_2d_vr(cls, vr_hud_pos: hg.Vec3, point3d: hg.Vec3, resolution: hg.Vec2, head_matrix: hg.Mat4, z_near, z_far):
		fov = atan(vr_hud_pos.y / (2 * vr_hud_pos.z)) * 2
		vs = hg.ComputePerspectiveViewState(head_matrix, fov, z_near, z_far, hg.Vec2(vr_hud_pos.x / vr_hud_pos.y, 1))
		pos_view = vs.view * point3d
		f, pos2d = hg.ProjectToScreenSpace(vs.proj, pos_view, resolution)
		if f:
			return hg.Vec2(pos2d.x, pos2d.y)
		else:
			return None

	@classmethod
	def add_text3D(cls, text, pos, size, color, h_align=hg.DTHA_Left):
		cls.texts3D_display_list.append({"text": text, "pos": pos, "size": size, "color": color, "h_align": h_align, "font": cls.debug_font})


	@classmethod
	def add_circle3D(cls, position:hg.Vec3, r:float, color:hg.Color):
		cls.primitives3D_display_list.append({"type": "circle", "pos": position, "r": r, "color":color})

	@classmethod
	def display_circle3D(cls, vid, camera_rotation_matrix, pos, r, color, angle_start=0, angle=2*pi):
		cls.vtx_flat.Clear()
		cls.uniforms_values_list.clear()
		cls.uniforms_textures_list.clear()
		matrix = hg.TransformationMat4(pos, camera_rotation_matrix)
		cls.vtx_flat.Begin(0).SetPos(pos).SetColor0(color).SetTexCoord0(hg.Vec2(0, 0)).End()

		idx = []
		step = angle / cls.circle_num_sections

		for i in range(cls.circle_num_sections + 1):
			alpha = i * step + angle_start
			cls.vtx_flat.Begin(i + 1).SetPos(matrix * hg.Vec3(cos(alpha) * r, sin(alpha) * r, 0)).SetColor0(color).End()
			if i > 0:
				idx += [0, i + 1, i]

		hg.DrawTriangles(vid, idx, cls.vtx_flat, cls.shader_flat, cls.uniforms_values_list, cls.uniforms_textures_list, cls.flat_render_state)

	@classmethod
	def display_primitives3D(cls, vid, camera_matrix):
		rotmat = hg.GetRotationMatrix(camera_matrix)
		for primitive in cls.primitives3D_display_list:
			if primitive["type"] == "circle":
				cls.display_circle3D(vid, rotmat, primitive["pos"], primitive["r"], primitive["color"])

	@classmethod
	def display_texts3D(cls, vid, camera_matrix):
		for txt in cls.texts3D_display_list:
			cls.display_text3D(vid, camera_matrix, txt["text"], txt["pos"], txt["size"], txt["font"], txt["color"], txt["h_align"])

	@classmethod
	def display_text3D(cls, vid, camera_matrix, text, pos, size, font, color, h_align=hg.DTHA_Center):
		"""
		cam_pos = hg.GetT(cam_mat)
		az = hg.Normalize(pos-cam_pos)
		ax = hg.Cross(hg.Vec3.Up, az)
		ay = hg.Cross(az, ax)
		mat = hg.Mat3(ax, ay, az)
		"""
		mat = hg.GetRotationMatrix(camera_matrix)
		cls.uniforms_values_list.clear()
		cls.uniforms_values_list.push_back(hg.MakeUniformSetValue("u_color", hg.Vec4(color.r, color.g, color.b, color.a)))  # Color
		hg.DrawText(vid, font, text, cls.font_program, "u_tex", 0,
					hg.TransformationMat4(pos, mat, hg.Vec3(1, -1, 1) * size),  # * (size * resolution.y / 64)),
					hg.Vec3(0, 0, 0),
					h_align, hg.DTVA_Bottom,
					cls.uniforms_values_list, cls.uniforms_textures_list, cls.flat_render_state)

	@classmethod
	def add_text2D_from_3D_position(cls, text, pos3D, offset2D, size, color, font=None, h_align=hg.DTHA_Left):
		cls.add_text2D(text, pos3D, size, color, font, h_align, True, offset2D)

	@classmethod
	def add_text2D(cls, text, pos, size, color, font=None, h_align=hg.DTHA_Left, convert_to_2D=False, offset2D=None):
		if font is None:
			font = cls.debug_font
		cls.texts2D_display_list.append({"text": text, "pos": pos, "offset2D": offset2D, "size": size, "color": color, "h_align": h_align, "font": font, "convert_to_2D": convert_to_2D})

	@classmethod
	def display_texts2D(cls, vid, camera, resolution):
		for txt in cls.texts2D_display_list:
			pos = txt["pos"]
			if txt["convert_to_2D"]:
				pos = cls.get_2d(camera, pos, resolution)
				if pos is None:
					continue
				if "offset2D" in txt and txt["offset2D"] is not None:
					pos += txt["offset2D"]
			cls.display_text2D(vid, resolution, txt["text"], pos, txt["size"], txt["font"], txt["color"], txt["h_align"])

	@classmethod
	def display_text2D(cls, vid, resolution, text, pos, size, font, color, h_align):
		cls.uniforms_values_list.clear()
		cls.uniforms_values_list.push_back(hg.MakeUniformSetValue("u_color", hg.Vec4(color.r, color.g, color.b, color.a)))  # Color
		hg.DrawText(vid, font, text, cls.font_program, "u_tex", 0,
					hg.TransformationMat4(hg.Vec3(pos.x * resolution.x, pos.y * resolution.y, 1), hg.Vec3(0, 0, 0), hg.Vec3(1, -1, 1) * (size * resolution.y / 64)),
					hg.Vec3(0, 0, 0),
					h_align, hg.DTVA_Bottom,
					cls.uniforms_values_list, cls.uniforms_textures_list, cls.flat_render_state)

	@classmethod
	def display_texts2D_vr(cls, vid, head_matrix: hg.Mat4, z_near, z_far, resolution, vr_matrix, vr_hud_pos):
		for txt in cls.texts2D_display_list:
			pos = txt["pos"]
			if txt["convert_to_2D"]:
				pos = cls.get_2d_vr(vr_hud_pos, pos, resolution, head_matrix, z_near, z_far)
				if pos is None:
					continue
				if "offset2D" in txt and txt["offset2D"] is not None:
					pos += txt["offset2D"]
			cls.display_text2D_vr(vid, vr_matrix, vr_hud_pos, resolution, txt["text"], pos, txt["size"], txt["font"], txt["color"], txt["h_align"])

	@classmethod
	def display_text2D_vr(cls, v_id, vr_matrix, vr_hud_pos, resolution, text, pos, size, font, color, h_align):
		pos_vr = hg.Vec3((pos.x - 0.5) * vr_hud_pos.x, (pos.y - 0.5) * vr_hud_pos.y, vr_hud_pos.z - 0.01)
		scale2D = hg.Vec3(1, -1, 1) * (size * resolution.y / 64)
		scale_vr = hg.Vec3(scale2D.x / resolution.x * vr_hud_pos.x, scale2D.y / resolution.y * vr_hud_pos.y, 1)
		matrix = vr_matrix * hg.TransformationMat4(pos_vr, hg.Vec3(0, 0, 0), scale_vr)

		cls.uniforms_values_list.clear()
		cls.uniforms_values_list.push_back(hg.MakeUniformSetValue("u_color", hg.Vec4(color.r, color.g, color.b, color.a)))  # Color
		hg.DrawText(v_id, font, text, cls.font_program, "u_tex", 0,
					matrix,
					hg.Vec3(0, 0, 0),
					h_align, hg.DTVA_Bottom,
					cls.uniforms_values_list, cls.uniforms_textures_list, cls.flat_render_state)
