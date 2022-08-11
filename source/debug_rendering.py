# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from planet_render import *
from WaterReflection import WaterReflection
from PostProcess import *
import sys
from Sprites import *

# --------------- Compile assets:
print("Compiling assets...")
#dc.run_command("..\\bin\\assetc\\assetc.exe assets -quiet -progress")


hg.InputInit()
hg.WindowSystemInit()

flag_vr = True

hg.SetLogDetailed(True)

res_x, res_y = 1600, 900
resolution = hg.Vec2(res_x, res_y)

win = hg.NewWindow(res_x, res_y)

hg.RenderInit(win)
hg.RenderReset(res_x, res_y, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

hg.AddAssetsFolder("assets_compiled")

texture_test = hg.LoadTextureFromAssets("textures/test.png", 0)[0]

pl_resources = hg.PipelineResources()

# input devices and fps controller states
keyboard = hg.Keyboard()
mouse = hg.Mouse()

# rendering pipeline
pipeline = hg.CreateForwardPipeline()
render_data = hg.SceneForwardPipelineRenderData()

# OpenVR initialization
if flag_vr:
	if not hg.OpenVRInit():
		sys.exit()
	# Init VR environment
	vr_left_fb = hg.OpenVRCreateEyeFrameBuffer(hg.OVRAA_MSAA4x)
	vr_right_fb = hg.OpenVRCreateEyeFrameBuffer(hg.OVRAA_MSAA4x)
	body_mtx = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(0, 0, 0))
	vr_state = hg.OpenVRGetState(body_mtx, 1, 1000)
	vr_resolution = hg.Vec2(vr_state.width, vr_state.height)
	rot = hg.GetR(vr_state.head)
	rot.x = 0
	rot.z = 0
	initial_head_matrix = hg.TransformationMat4(hg.GetT(vr_state.head), rot)

scene = hg.Scene()
hg.LoadSceneFromAssets("main.scn", scene, pl_resources, hg.GetForwardPipelineInfo())

if flag_vr:
	r = vr_resolution
else:
	r = resolution

post_process = PostProcess(r,4, flag_vr)
sea_render = PlanetRender(scene, r, scene.GetNode("island_clipped").GetTransform().GetPos(), hg.Vec3(-20740.2158, 0, 9793.1535))
sea_render.load_json_script()
sea_render.reflect_offset = 1
water_reflexion = WaterReflection(scene, r, 4, flag_vr)

camera_fps = scene.GetNode("Camera_fps")
scene.SetCurrentCamera(camera_fps)
camera_fps.GetCamera().SetZNear(2)
camera_fps.GetCamera().SetZFar(50000)
camera_fps.GetTransform().SetPos(hg.Vec3(0, 17.4 + 3, 80))

scene.Update(0)

# Load scene
def remove_dummies_objects(parent_node, scn):
	sv = parent_node.GetInstanceSceneView()
	nodes = sv.GetNodes(scn)
	for i in range(nodes.size()):
		nd = nodes.at(i)
		nm = nd.GetName()
		if "dummy" in nm or "slot" in nm or "col_shape" in nm:
			if nd.HasObject():
				nd.RemoveObject()


# Scene 1
shader = hg.LoadPipelineProgramRefFromAssets('core/shader/default.hps', pl_resources, hg.GetForwardPipelineInfo())
vtx_layout = hg.VertexLayoutPosFloatNormUInt8()
cube_mdl = hg.CreateCubeModel(vtx_layout, 0.06, 0.06, 0.1)
cube_ref = pl_resources.AddModel('cube', cube_mdl)
mat_yellow_cube = hg.CreateMaterial(shader, 'uDiffuseColor', hg.Vec4I(255, 220, 64), 'uSelfColor', hg.Vec4I(255, 220, 64))
mat_red_cube = hg.CreateMaterial(shader, 'uDiffuseColor', hg.Vec4I(255, 0, 0), 'uSelfColor', hg.Vec4I(255, 0, 0))
yellow_cube = hg.CreateObject(scene, hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(0, hg.Deg(0), 0)), cube_ref, [mat_yellow_cube])
red_cube = hg.CreateObject(scene, hg.TranslationMat4(hg.Vec3(0, 0, 0)), cube_ref, [mat_red_cube])

carrier_node, f = hg.CreateInstanceFromAssets(scene, hg.TranslationMat4(hg.Vec3(0, 0, 0)), "machines/aircraft_carrier_blend/aircraft_carrier_blend.scn", pl_resources, hg.GetForwardPipelineInfo())
aircraft_node, f  = hg.CreateInstanceFromAssets(scene, hg.TranslationMat4(hg.Vec3(10, 19.2, 80)), "machines/tfx/TFX.scn", pl_resources, hg.GetForwardPipelineInfo())

remove_dummies_objects(carrier_node, scene)
remove_dummies_objects(aircraft_node, scene)

quad_mdl = hg.VertexLayout()
quad_mdl.Begin()
quad_mdl.Add(hg.A_Position, 3, hg.AT_Float)
quad_mdl.Add(hg.A_TexCoord0, 3, hg.AT_Float)
quad_mdl.End()
if flag_vr:
	r = vr_resolution
else:
	r = resolution
quad_size = hg.Vec2(r.x / r.y, 1) * 2
quad_model = hg.CreatePlaneModel(quad_mdl, quad_size.x, quad_size.y, 1, 1)
quad_uniform_set_value_list = hg.UniformSetValueList()
quad_uniform_set_texture_list = hg.UniformSetTextureList()
write_z = False
quad_render_state = hg.ComputeRenderState(hg.BM_Opaque, hg.DT_Disabled, hg.FC_Disabled, write_z)
quad_matrix = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(1, 1, 1))
scenedisplay_prg = hg.LoadProgramFromAssets("shaders/scenedisplay")
quad_uniform_set_value_list.clear()
quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("color", hg.Vec4(1, 1, 1, 1)))
quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("quad_size", hg.Vec4(quad_size.x, quad_size.y, 1, 1)))


# Camera move
fps_rot = camera_fps.GetTransform().GetRot()
fps_pos = camera_fps.GetTransform().GetPos()
fps_rot_inertia = 0.1
fps_pos_inertia = 0.1

if flag_vr:
	# VR display:
	# Setup 2D rendering to display eyes textures
	vr_quad_layout = hg.VertexLayout()
	vr_quad_layout.Begin().Add(hg.A_Position, 3, hg.AT_Float).Add(hg.A_TexCoord0, 3, hg.AT_Float).End()

	vr_quad_model = hg.CreatePlaneModel(vr_quad_layout, 1, 1, 1, 1)
	vr_quad_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Disabled, hg.FC_Disabled)

	eye_t_size = res_x / 2.5
	eye_t_x = (res_x - 2 * eye_t_size) / 6 + eye_t_size / 2
	vr_quad_matrix = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(eye_t_size, 1, eye_t_size))

	vr_tex0_program = hg.LoadProgramFromAssets("shaders/vrdisplay")

	vr_quad_uniform_set_value_list = hg.UniformSetValueList()
	vr_quad_uniform_set_value_list.clear()
	vr_quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("color", hg.Vec4(1, 1, 1, 1)))

	vr_quad_uniform_set_texture_list = hg.UniformSetTextureList()


def update_fps_vr(camera, head_mtx, fps_p, dts):
	speed = 1
	if keyboard.Down(hg.K_LShift):
		speed = 100
	elif keyboard.Down(hg.K_LCtrl):
		speed = 1000
	elif keyboard.Down(hg.K_RCtrl):
		speed = 50000

	aX = hg.GetX(head_mtx)
	aY = hg.GetY(head_mtx)
	aZ = hg.GetZ(head_mtx)

	if keyboard.Down(hg.K_Up) or keyboard.Down(hg.K_W):
		fps_p += aZ * speed * dts
	if keyboard.Down(hg.K_Down) or keyboard.Down(hg.K_S):
		fps_p -= aZ * speed * dts
	if keyboard.Down(hg.K_Left) or keyboard.Down(hg.K_A):
		fps_p -= aX * speed * dts
	if keyboard.Down(hg.K_Right) or keyboard.Down(hg.K_D):
		fps_p += aX * speed * dts

	if keyboard.Down(hg.K_R):
		fps_p += aY * speed * dts
	if keyboard.Down(hg.K_F):
		fps_p -= aZ * speed * dts

	cam_pos0 = camera.GetTransform().GetPos()
	camera.GetTransform().SetPos(cam_pos0 + (fps_p - cam_pos0) * fps_pos_inertia)
	return fps_p


def update_camera(camera, dts, fps_p, fps_r):
	cam_t = camera.GetTransform()
	cam_fov = camera.GetCamera().GetFov()
	speed = 1
	if keyboard.Down(hg.K_LShift):
		speed = 100
	elif keyboard.Down(hg.K_LCtrl):
		speed = 1000
	elif keyboard.Down(hg.K_RCtrl):
		speed = 50000

	fps_rot_fov = hg.Vec3(fps_r)
	hg.FpsController(keyboard, mouse, fps_p, fps_r, speed, hg.time_from_sec_f(dts))

	if keyboard.Down(hg.K_U):
		fps_r.z += 0.1
	elif keyboard.Down(hg.K_I):
		fps_r.z -= 0.1

	fps_r = fps_rot_fov + (fps_r - fps_rot_fov) * cam_fov / (40 / 180 * pi)

	fov = camera.GetCamera().GetFov()
	if keyboard.Down(hg.K_F1):
		fov *= 1.01
	elif keyboard.Down(hg.K_F2):
		fov *= 0.99
	camera.GetCamera().SetFov(fov)

	cam_pos0 = cam_t.GetPos()
	cam_t.SetPos(cam_pos0 + (fps_p - cam_pos0) * fps_pos_inertia)
	cam_rot0 = cam_t.GetRot()
	cam_t.SetRot(cam_rot0 + (fps_r - cam_rot0) * fps_rot_inertia)

# Sprites:
Sprite.init_system()
if flag_vr:
	ratio = resolution.x / resolution.y
	size = 10
	vr_hud = hg.Vec3(size * ratio, size, 12)
spr_hud = Sprite(1280, 720, "sprites/hud_border.png")
spr_hud.set_size(resolution.x / 1280)


# main loop
hg.ResetClock()
scene.Update(0)
post_process.setup_fading(3, 1)

while not keyboard.Pressed(hg.K_Escape):

	flag_render_reflect = True
	flag_render_planet = True
	flag_render_scene3d = True

	sprites_display_list = []

	keyboard.Update()
	mouse.Update()
	dt = hg.TickClock()
	dts = hg.time_to_sec_f(dt)

	cam = scene.GetCurrentCamera()

	if flag_vr:
		main_camera_matrix = cam.GetTransform().GetWorld()
		body_mtx = main_camera_matrix * hg.InverseFast(initial_head_matrix)
		vr_state = hg.OpenVRGetState(body_mtx, cam.GetCamera().GetZNear(), cam.GetCamera().GetZFar())

		vs_left, vs_right = hg.OpenVRStateToViewState(vr_state)
		vr_eye_rect = hg.IntRect(0, 0, int(vr_state.width), int(vr_state.height))

		fps_pos = update_fps_vr(cam, vr_state.head, fps_pos, dts)

		scene.Update(dt)
		pos = cam.GetTransform().GetPos()
		rot = cam.GetTransform().GetRot()
	
		#if keyboard.Pressed(hg.K_F12):
		#	vr_state.update_initial_head_matrix()

		red_cube.GetTransform().SetWorld(vr_state.head * vr_state.right.offset)
		yellow_cube.GetTransform().SetWorld(vr_state.head * vr_state.left.offset)

	else:
		update_camera(cam, dts, fps_pos, fps_rot)

		scene.Update(dt)
		pos = cam.GetTransform().GetPos()
		rot = cam.GetTransform().GetRot()


	vid = 0
	views = hg.SceneForwardPipelinePassViewId()
	scene.canvas.color = hg.Color(1,0,0,1) #sea_render.high_atmosphere_color

	# ========== Display Reflect scene ===================
	post_process.update_fading(dts)
	if flag_render_reflect:
		if not flag_vr:

			water_reflexion.set_camera(scene)
			scene.canvas.clear_z = True
			scene.canvas.clear_color = True
			#hg.SetViewClear(vid, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
			#hg.SetViewClear(vid, 0, 0x0, 1.0, 0)

			vs = scene.ComputeCurrentCameraViewState(hg.ComputeAspectRatioX(res_x, res_y))
			vid, passId = hg.PrepareSceneForwardPipelineCommonRenderData(vid, scene, render_data, pipeline, pl_resources, views)
			vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs, scene, render_data, pipeline, pl_resources, views)

			# Get quad_frameBuffer.handle to define output frameBuffer
			#vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, hg.IntRect(0, 0, res_x, res_y), vs, pipeline, render_data, pl_resources, post_process.quad_frameBuffer.handle)
			vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, hg.IntRect(0, 0, res_x, res_y), vs, pipeline, render_data, pl_resources, water_reflexion.quad_frameBuffer.handle)
			water_reflexion.restore_camera(scene)
		else:
			scene.canvas.clear_z = True
			scene.canvas.clear_color = True
			cam = scene.GetCurrentCamera()
			left_reflect, right_reflect = water_reflexion.compute_vr_reflect(cam, vr_state, vs_left, vs_right)

			vid, passId = hg.PrepareSceneForwardPipelineCommonRenderData(vid, scene, render_data, pipeline, pl_resources, views)
			vr_eye_rect = hg.IntRect(0, 0, int(vr_resolution.x), int(vr_resolution.y))

			# Prepare the left eye render data then draw to its framebuffer
			vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, left_reflect, scene, render_data, pipeline, pl_resources, views)
			vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, vr_eye_rect, left_reflect, pipeline, render_data, pl_resources, water_reflexion.quad_frameBuffer_left.handle)

			# Prepare the right eye render data then draw to its framebuffer
			vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, right_reflect, scene, render_data, pipeline, pl_resources, views)
			vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, vr_eye_rect, right_reflect, pipeline, render_data, pl_resources, water_reflexion.quad_frameBuffer_right.handle)

	# ========== Display raymarch scene ===================

	if flag_render_planet:
		if not flag_vr:
			scene.canvas.clear_z = True
			scene.canvas.clear_color = True
			#hg.SetViewClear(vid, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
			if flag_render_reflect:
				vid = sea_render.render(vid, scene.GetCurrentCamera(), hg.Vec2(res_x, res_y), hg.GetColorTexture(water_reflexion.quad_frameBuffer), hg.GetDepthTexture(water_reflexion.quad_frameBuffer), post_process.quad_frameBuffer)
			else:
				vid = sea_render.render(vid, scene.GetCurrentCamera(), hg.Vec2(res_x, res_y), None, None, post_process.quad_frameBuffer)

		else:

			scene.canvas.clear_z = False
			scene.canvas.clear_color = False
			# hg.SetViewClear(vid, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
			tex_reflect_left_color = hg.GetColorTexture(water_reflexion.quad_frameBuffer_left)
			tex_reflect_left_depth = hg.GetDepthTexture(water_reflexion.quad_frameBuffer_left)
			tex_reflect_right_color = hg.GetColorTexture(water_reflexion.quad_frameBuffer_right)
			tex_reflect_right_depth = hg.GetDepthTexture(water_reflexion.quad_frameBuffer_right)
			#vid = sea_render.render_vr(vid, vr_state, vs_left, vs_right, post_process.quad_frameBuffer_left, post_process.quad_frameBuffer_right, tex_reflect_left_color, tex_reflect_left_depth, tex_reflect_right_color, tex_reflect_right_depth)
			vid = sea_render.render_vr(vid, vr_state, vs_left, vs_right, vr_left_fb, vr_right_fb, tex_reflect_left_color, tex_reflect_left_depth, tex_reflect_right_color, tex_reflect_right_depth)

	# ========== Display models scene ===================

	if flag_render_scene3d:
		if flag_render_planet or flag_render_reflect:
			scene.canvas.clear_z = False
			scene.canvas.clear_color = False
		else:
			scene.canvas.clear_z = True
			scene.canvas.clear_color = True

		if not flag_vr:
			vs = scene.ComputeCurrentCameraViewState(hg.ComputeAspectRatioX(res_x, res_y))
			vid, passId = hg.PrepareSceneForwardPipelineCommonRenderData(vid, scene, render_data, pipeline, pl_resources, views)
			vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs, scene, render_data, pipeline, pl_resources, views)

			# Get quad_frameBuffer.handle to define output frameBuffer
			vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, hg.IntRect(0, 0, res_x, res_y), vs, pipeline, render_data, pl_resources, post_process.quad_frameBuffer.handle)

		else:
			vid, passId = hg.PrepareSceneForwardPipelineCommonRenderData(vid, scene, render_data, pipeline, pl_resources, views)
			vr_eye_rect = hg.IntRect(0, 0, int(vr_resolution.x), int(vr_resolution.y))

			# Prepare the left eye render data then draw to its framebuffer
			vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs_left, scene, render_data, pipeline, pl_resources, views)
			#vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, vr_eye_rect, vs_left, pipeline, render_data, pl_resources, post_process.quad_frameBuffer_left.handle)
			vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, vr_eye_rect, vs_left, pipeline, render_data, pl_resources, vr_left_fb.GetHandle())

			# Display additional geometry
			""".
			hg.SetViewFrameBuffer(vid, vr_left_fb.handle)
			hg.SetViewRect(vid, 0, 0, vr_state.width, vr_state.height)
			hg.SetViewTransform(vid, vs_left.view, vs_left.proj)
			mat = hg.TransformationMat4(hg.Vec3(0, 20, 120), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(10, 1, 10))
			hg.DrawModel(vid, vr_quad_model, vr_tex0_program, vr_quad_uniform_set_value_list, vr_quad_uniform_set_texture_list, mat, vr_quad_render_state)
			vid += 1
			"""

			# Prepare the right eye render data then draw to its framebuffer
			vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs_right, scene, render_data, pipeline, pl_resources, views)
			#vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, vr_eye_rect, vs_right, pipeline, render_data, pl_resources, post_process.quad_frameBuffer_right.handle)
			vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, vr_eye_rect, vs_right, pipeline, render_data, pl_resources, vr_right_fb.GetHandle())

			# Display additional geometry
			"""
			hg.SetViewFrameBuffer(vid, vr_right_fb.handle)
			hg.SetViewRect(vid, 0, 0, vr_state.width, vr_state.height)
			hg.SetViewTransform(vid, vs_right.view, vs_right.proj)
			mat = hg.TransformationMat4(hg.Vec3(0, 20, 120), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(10, 1, 10))
			hg.DrawModel(vid, vr_quad_model, vr_tex0_program, vr_quad_uniform_set_value_list, vr_quad_uniform_set_texture_list, mat, vr_quad_render_state)
			vid += 1
			"""

	# ==================== Display 2D sprites ===========

	spr_hud.set_position(800/1600*resolution.x, 450/900*resolution.y)
	sprites_display_list.append(spr_hud)

	if not flag_vr:

		hg.SetViewFrameBuffer(vid, post_process.quad_frameBuffer.handle)
		hg.SetViewRect(vid, 0, 0, res_x, res_y)

		Sprite.setup_matrix_sprites2D(vid, resolution)

		for spr in sprites_display_list:
			spr.draw(vid)
		vid += 1
	else:
		vr_ratio = hg.Vec2(vr_resolution.x / vr_resolution.y, 1)
		cam_mat = cam.GetTransform().GetWorld()
		mat_spr = cam_mat  # * vr_state.initial_head_offset
		left_spr_proj = hg.ComputePerspectiveProjectionMatrix(0.1, 100, hg.ExtractZoomFactorFromProjectionMatrix(vs_left.proj), vr_ratio)
		right_spr_proj = hg.ComputePerspectiveProjectionMatrix(0.1, 100, hg.ExtractZoomFactorFromProjectionMatrix(vs_right.proj), vr_ratio)
		#mat_right = vr_state.body #head * vr_state.right.offset

		hg.SetViewFrameBuffer(vid, post_process.quad_frameBuffer_left.handle)
		hg.SetViewRect(vid, 0, 0, int(vr_resolution.x), int(vr_resolution.y))
		hg.SetViewTransform(vid, vs_left.view, left_spr_proj)
		for spr in sprites_display_list:
			spr.draw_vr(vid, mat_spr, resolution, vr_hud)
		vid += 1

		hg.SetViewFrameBuffer(vid, post_process.quad_frameBuffer_right.handle)
		hg.SetViewRect(vid, 0, 0, int(vr_resolution.x), int(vr_resolution.y))
		hg.SetViewTransform(vid, vs_right.view, right_spr_proj)
		for spr in sprites_display_list:
			spr.draw_vr(vid, mat_spr, resolution, vr_hud)
		vid += 1

	# ========== Post process:
	if not flag_vr:
		scene.canvas.clear_z = False
		scene.canvas.clear_color = False

		vid = post_process.display(vid, pl_resources, resolution)  # , pl_resources.GetTexture(water_reflexion.quad_frameBuffer.color))

	else:
		pass
		#vid = post_process.display_vr(vid, vr_state, vs_left, vs_right, vr_left_fb, vr_right_fb, pl_resources)

	# ============ Display the VR eyes texture to the backbuffer

	if flag_vr:
		hg.SetViewRect(vid, 0, 0, res_x, res_y)
		hg.SetViewClear(vid, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
		vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(0, 0, 0)), res_y, 0.1, 100, hg.ComputeAspectRatioX(res_x, res_y))
		hg.SetViewTransform(vid, vs.view, vs.proj)

		vr_quad_uniform_set_texture_list.clear()
		#vr_quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", texture_test, 0))
		vr_quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.OpenVRGetColorTexture(vr_left_fb), 0))
		hg.SetT(vr_quad_matrix, hg.Vec3(eye_t_x, 0, 1))
		hg.DrawModel(vid, vr_quad_model, vr_tex0_program, vr_quad_uniform_set_value_list, vr_quad_uniform_set_texture_list, vr_quad_matrix, vr_quad_render_state)

		vr_quad_uniform_set_texture_list.clear()
		#vr_quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", texture_test, 0))
		vr_quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.OpenVRGetColorTexture(vr_right_fb), 0))
		hg.SetT(vr_quad_matrix, hg.Vec3(-eye_t_x, 0, 1))
		hg.DrawModel(vid, vr_quad_model, vr_tex0_program, vr_quad_uniform_set_value_list, vr_quad_uniform_set_texture_list, vr_quad_matrix, vr_quad_render_state)


	# ===================== EOF ============================
	hg.Frame()
	if flag_vr:
		hg.OpenVRSubmitFrame(vr_left_fb, vr_right_fb)
	hg.UpdateWindow(win)

hg.RenderShutdown()
hg.DestroyWindow(win)
