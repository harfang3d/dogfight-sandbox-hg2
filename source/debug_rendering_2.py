# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
import planet_render
from WaterReflection import WaterReflection
from PostProcess import *
import sys
from Sprites import *
import harfang.bin

from source.planet_render import PlanetRender

# --------------- Compile assets:
print("Compiling assets...")
# dc.run_command("..\\bin\\assetc\\assetc assets -quiet -progress")
harfang.bin.assetc('..\\bin\\assetc\\assetc')


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
	vs_left, vs_right = hg.OpenVRStateToViewState(vr_state)
	vr_fov_left = hg.ZoomFactorToFov(hg.ExtractZoomFactorFromProjectionMatrix(vs_left.proj, hg.Vec2(1,1)))
	vr_fov_right = hg.ZoomFactorToFov(hg.ExtractZoomFactorFromProjectionMatrix(vs_right.proj, hg.Vec2(1,1)))

scene = hg.Scene()
hg.LoadSceneFromAssets("main.scn", scene, pl_resources, hg.GetForwardPipelineInfo())

if flag_vr:
	r = vr_resolution
else:
	r = resolution

post_process = PostProcess(r, 4, flag_vr)
sea_render = PlanetRender(scene, r, scene.GetNode("island_clipped").GetTransform().GetPos(), hg.Vec3(-20740.2158, 0, 9793.1535))
sea_render.load_json_script()
sea_render.reflect_offset = 1
water_reflexion = WaterReflection(scene, r, 4, flag_vr)

camera_fps = scene.GetNode("Camera_fps")
scene.SetCurrentCamera(camera_fps)
camera_fps.GetCamera().SetZNear(2)
camera_fps.GetCamera().SetZFar(50000)
camera_fps.GetTransform().SetPos(hg.Vec3(0, 17.4 + 1, 80))

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

# Scene 2
scene_2 = hg.Scene()
camera_2 = hg.CreateCamera(scene_2, hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(0, 0, 0)), 0.01, 50, camera_fps.GetCamera().GetFov())
scene_2.SetCurrentCamera(camera_2)
aircraft2_node, f = hg.CreateInstanceFromAssets(scene_2, hg.TranslationMat4(hg.Vec3(0, 0, 0)), "machines/rafale/rafale_rigged.scn", pl_resources, hg.GetForwardPipelineInfo())
remove_dummies_objects(aircraft2_node, scene_2)

fb_aa = 4
if flag_vr:
	scene2_frameBuffer_left = hg.CreateFrameBuffer(int(r.x), int(r.y), hg.TF_RGBA8, hg.TF_D32F, fb_aa, "frameBuffer_cockpit_left")  #hg.OpenVRCreateEyeFrameBuffer(hg.OVRAA_MSAA4x)
	scene2_frameBuffer_right = hg.CreateFrameBuffer(int(r.x), int(r.y), hg.TF_RGBA8, hg.TF_D32F, fb_aa, "frameBuffer_cockpit_right")  #hg.OpenVRCreateEyeFrameBuffer(hg.OVRAA_MSAA4x)
else:
	scene2_frameBuffer = hg.CreateFrameBuffer(int(resolution.x), int(resolution.y), hg.TF_RGBA8, hg.TF_D32F, fb_aa, "frameBuffer_scenedisplay")


env0 = scene.environment
env2 = scene_2.environment
env2.ambient = env0.ambient
env2.brdf_map = env0.brdf_map
env2.fog_color = env0.fog_color
env2.fog_far = env0.fog_far
env2.fog_near = env0.fog_near
env2.irradiance_map = env0.irradiance_map
env2.radiance_map = env0.radiance_map
sun0 = scene.GetNode("Sun")
light0 = sun0.GetLight()
sun_2 = hg.CreateLinearLight(scene_2, sun0.GetTransform().GetWorld(), light0.GetDiffuseColor(), light0.GetSpecularColor(), light0.GetPriority(), light0.GetShadowType(), 0.008, light0.GetPSSMSplit())

scene_2.Update(0)
sv = aircraft2_node.GetInstanceSceneView()
pilot_head = sv.GetNode(scene_2, "pilote_head.01")
f16_v = hg.GetT(pilot_head.GetTransform().GetWorld()) - hg.GetT(aircraft2_node.GetTransform().GetWorld())
camera_2.GetTransform().SetPos(f16_v)
scene_2.Update(0)

quad_mdl = hg.VertexLayout()
quad_mdl.Begin()
quad_mdl.Add(hg.A_Position, 3, hg.AT_Float)
quad_mdl.Add(hg.A_TexCoord0, 3, hg.AT_Float)
quad_mdl.End()

if flag_vr:
	r = vr_resolution
else:
	r = resolution
quad_model = hg.CreatePlaneModel(quad_mdl, 1, 1, 1, 1)
quad_uniform_set_value_list = hg.UniformSetValueList()
quad_uniform_set_texture_list = hg.UniformSetTextureList()
write_z = False
quad_render_state = hg.ComputeRenderState(hg.BM_Opaque, hg.DT_Disabled, hg.FC_Disabled, write_z)
quad_matrix = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(r.x / r.y, 1, 1) * 2)
scenedisplay_prg = hg.LoadProgramFromAssets("shaders/scenedisplay")
quad_uniform_set_value_list.clear()
quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("color", hg.Vec4(1, 1, 1, 1)))
quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("uv_scale", hg.Vec4(1, 1, 0, 0)))


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


def update_fps_vr(camera, head_mtx, dts):
	global fps_pos
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
		fps_pos += aZ * speed * dts
	if keyboard.Down(hg.K_Down) or keyboard.Down(hg.K_S):
		fps_pos -= aZ * speed * dts
	if keyboard.Down(hg.K_Left) or keyboard.Down(hg.K_A):
		fps_pos -= aX * speed * dts
	if keyboard.Down(hg.K_Right) or keyboard.Down(hg.K_D):
		fps_pos += aX * speed * dts

	if keyboard.Down(hg.K_R):
		fps_pos += aY * speed * dts
	if keyboard.Down(hg.K_F):
		fps_pos -= aZ * speed * dts

	cam_pos0 = camera.GetTransform().GetPos()
	camera.GetTransform().SetPos(cam_pos0 + (fps_pos - cam_pos0) * fps_pos_inertia)


def update_camera(camera, dts):
	global fps_rot, fps_pos
	cam_t = camera.GetTransform()
	cam_fov = camera.GetCamera().GetFov()
	speed = 1
	if keyboard.Down(hg.K_LShift):
		speed = 100
	elif keyboard.Down(hg.K_LCtrl):
		speed = 1000
	elif keyboard.Down(hg.K_RCtrl):
		speed = 50000

	fps_rot_fov = hg.Vec3(fps_rot)
	hg.FpsController(keyboard, mouse, fps_pos, fps_rot, speed, hg.time_from_sec_f(dts))

	if keyboard.Down(hg.K_U):
		fps_rot.z += 0.1
	elif keyboard.Down(hg.K_I):
		fps_rot.z -= 0.1

	fps_rot = fps_rot_fov + (fps_rot - fps_rot_fov) * cam_fov / (40 / 180 * pi)

	fov = camera.GetCamera().GetFov()
	if keyboard.Down(hg.K_F1):
		fov *= 1.01
	elif keyboard.Down(hg.K_F2):
		fov *= 0.99
	camera.GetCamera().SetFov(fov)

	cam_pos0 = cam_t.GetPos()
	cam_t.SetPos(cam_pos0 + (fps_pos - cam_pos0) * fps_pos_inertia)
	cam_rot0 = cam_t.GetRot()
	cam_t.SetRot(cam_rot0 + (fps_rot - cam_rot0) * fps_rot_inertia)

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
scene_2.Update(0)
post_process.setup_fading(3, 1)

def compute_vr_viewstate(vr_state:hg.OpenVRState, camera):
	cam = camera.GetCamera()
	z_near = cam.GetZNear()
	z_far = cam.GetZFar()
	local_head_matrix = hg.InverseFast(initial_head_matrix) * vr_state.head
	head_matrix = camera.GetTransform().GetWorld() * local_head_matrix

	eye_left = head_matrix * vr_state.left.offset
	eye_right = head_matrix * vr_state.right.offset

	ratio = hg.Vec2(vr_resolution.x / vr_resolution.y, 1)
	vs_left = hg.ComputePerspectiveViewState(eye_left, vr_fov_left, z_near, z_far, ratio)
	vs_right = hg.ComputePerspectiveViewState(eye_right, vr_fov_right, z_near, z_far, ratio)


	vs_left.view = hg.InverseFast(eye_left)
	vs_left.proj = vr_state.left.projection
	vs_left.frustum = hg.MakeFrustum(vr_state.left.projection * vs_left.view)

	vs_right.view = hg.InverseFast(eye_right)
	vs_right.proj = vr_state.right.projection
	vs_right.frustum = hg.MakeFrustum(vr_state.right.projection * vs_right.view)


	return head_matrix, eye_left, eye_right, vs_left, vs_right

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
	cam2 = scene_2.GetCurrentCamera()



	if flag_vr:

		body_mtx = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(0, 0, 0))
		vr_state = hg.OpenVRGetState(body_mtx, 0.1, 5000)

		head_matrix_1, eye_left_1, eye_right_1, vs_left_1, vs_right_1 = compute_vr_viewstate(vr_state, cam)
		head_matrix_2, eye_left_2, eye_right_2, vs_left_2, vs_right_2 = compute_vr_viewstate(vr_state, cam2)

		update_fps_vr(cam, head_matrix_1, dts)

		scene.Update(dt)
		pos = cam.GetTransform().GetPos()
		rot = cam.GetTransform().GetRot()
		#cam2.GetTransform().SetPos(pos)
		cam2.GetTransform().SetRot(rot)
		scene_2.Update(dt)


		#if keyboard.Pressed(hg.K_F12):
		#	vr_state.update_initial_head_matrix()

		red_cube.GetTransform().SetWorld(vr_state.head * vr_state.right.offset)
		yellow_cube.GetTransform().SetWorld(vr_state.head * vr_state.left.offset)



	else:
		update_camera(cam, dts)

		scene.Update(dt)
		pos = cam.GetTransform().GetPos()
		rot = cam.GetTransform().GetRot()
		#cam2.GetTransform().SetPos(pos)
		cam2.GetTransform().SetRot(rot)
		cam2.GetCamera().SetFov(cam.GetCamera().GetFov())
		scene_2.Update(dt)


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
			left_reflect, right_reflect = water_reflexion.compute_vr_reflect(cam, vr_resolution, eye_left_1, eye_right_1, vs_left_1, vs_right_1)

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
				vid = sea_render.render(vid, scene.GetCurrentCamera(), hg.Vec2(res_x, res_y), hg.GetColorTexture(water_reflexion.quad_frameBuffer), hg.GetDepthTexture(water_reflexion.quad_frameBuffer), scene2_frameBuffer)
			else:
				vid = sea_render.render(vid, scene.GetCurrentCamera(), hg.Vec2(res_x, res_y), None, None, scene2_frameBuffer)

		else:

			scene.canvas.clear_z = False
			scene.canvas.clear_color = False
			# hg.SetViewClear(vid, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
			tex_reflect_left_color = hg.GetColorTexture(water_reflexion.quad_frameBuffer_left)
			tex_reflect_left_depth = hg.GetDepthTexture(water_reflexion.quad_frameBuffer_left)
			tex_reflect_right_color = hg.GetColorTexture(water_reflexion.quad_frameBuffer_right)
			tex_reflect_right_depth = hg.GetDepthTexture(water_reflexion.quad_frameBuffer_right)
			vid = sea_render.render_vr(vid, cam, vr_state, vr_resolution, eye_left_1, eye_right_1, vs_left_1, vs_right_1, scene2_frameBuffer_left, scene2_frameBuffer_right, tex_reflect_left_color, tex_reflect_left_depth, tex_reflect_right_color, tex_reflect_right_depth)

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
			vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, hg.IntRect(0, 0, res_x, res_y), vs, pipeline, render_data, pl_resources, scene2_frameBuffer.handle)

		else:
			vid, passId = hg.PrepareSceneForwardPipelineCommonRenderData(vid, scene, render_data, pipeline, pl_resources, views)
			vr_eye_rect = hg.IntRect(0, 0, int(vr_resolution.x), int(vr_resolution.y))

			# Prepare the left eye render data then draw to its framebuffer
			vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs_left_1, scene, render_data, pipeline, pl_resources, views)
			vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, vr_eye_rect, vs_left_1, pipeline, render_data, pl_resources, scene2_frameBuffer_left.handle)
			#vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, vr_eye_rect, vs_left, pipeline, render_data, pl_resources, vr_left_fb.GetHandle())

			# Display additional geometry
			"""
			hg.SetViewFrameBuffer(vid, vr_left_fb.handle)
			hg.SetViewRect(vid, 0, 0, vr_state.width, vr_state.height)
			hg.SetViewTransform(vid, vs_left.view, vs_left.proj)
			mat = hg.TransformationMat4(hg.Vec3(0, 20, 120), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(10, 1, 10))
			hg.DrawModel(vid, vr_quad_model, vr_tex0_program, vr_quad_uniform_set_value_list, vr_quad_uniform_set_texture_list, mat, vr_quad_render_state)
			vid += 1
			"""

			# Prepare the right eye render data then draw to its framebuffer
			vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs_right_1, scene, render_data, pipeline, pl_resources, views)
			vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, vr_eye_rect, vs_right_1, pipeline, render_data, pl_resources, scene2_frameBuffer_right.handle)
			#vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, vr_eye_rect, vs_right, pipeline, render_data, pl_resources, vr_right_fb.GetHandle())

			# Display additional geometry
			"""
			hg.SetViewFrameBuffer(vid, vr_right_fb.handle)
			hg.SetViewRect(vid, 0, 0, vr_state.width, vr_state.height)
			hg.SetViewTransform(vid, vs_right.view, vs_right.proj)
			mat = hg.TransformationMat4(hg.Vec3(0, 20, 120), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(10, 1, 10))
			hg.DrawModel(vid, vr_quad_model, vr_tex0_program, vr_quad_uniform_set_value_list, vr_quad_uniform_set_texture_list, mat, vr_quad_render_state)
			vid += 1
			"""


	# ==================== Display scene 2 ==============

		if not flag_vr:
			# Display framebuffer color texture

			hg.SetViewFrameBuffer(vid, post_process.quad_frameBuffer.handle)
			hg.SetViewRect(vid, 0, 0, res_x, res_y)
			hg.SetViewClear(vid, 0, 0, 0, 0)

			#vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(0, 0, 0)), res_y, 0.1, 10, hg.ComputeAspectRatioX(res_x, res_y))
			#hg.SetViewTransform(vid, vs.view, vs.proj)

			camera = scene_2.GetCurrentCamera()
			cam = camera.GetCamera()
			focal_distance = hg.FovToZoomFactor(cam.GetFov())
			cam_mat = hg.TransformationMat4(hg.Vec3(0, 0, -focal_distance), hg.Vec3(0, 0, 0))
			view = hg.InverseFast(cam_mat)
			proj = hg.ComputePerspectiveProjectionMatrix(0.1, 100, focal_distance, hg.Vec2(resolution.x / resolution.y, 1))
			hg.SetViewTransform(vid, view, proj)

			quad_uniform_set_texture_list.clear()
			quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.GetColorTexture(scene2_frameBuffer), 0))
			hg.DrawModel(vid, quad_model, scenedisplay_prg, quad_uniform_set_value_list, quad_uniform_set_texture_list, quad_matrix, quad_render_state)
			vid += 1

			scene_2.canvas.clear_z = True
			scene_2.canvas.clear_color = False
			vs = scene_2.ComputeCurrentCameraViewState(hg.ComputeAspectRatioX(res_x, res_y))
			vid, passId = hg.PrepareSceneForwardPipelineCommonRenderData(vid, scene_2, render_data, pipeline, pl_resources, views)
			vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs, scene_2, render_data, pipeline, pl_resources, views)

			# Get quad_frameBuffer.handle to define output frameBuffer
			vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene_2, hg.IntRect(0, 0, res_x, res_y), vs, pipeline, render_data, pl_resources, post_process.quad_frameBuffer.handle)

		else:
			focal_distance_left = hg.ExtractZoomFactorFromProjectionMatrix(vs_left_2.proj)
			focal_distance_right = hg.ExtractZoomFactorFromProjectionMatrix(vs_right_2.proj)

			#z_near = cam2.GetCamera().GetZNear()
			#z_far = cam2.GetCamera().GetZFar()

			z_near, z_far = hg.ExtractZRangeFromProjectionMatrix(vs_left_2.proj)
			z_ratio = (z_near + 0.01) / focal_distance_left
			hg.SetViewFrameBuffer(vid, post_process.quad_frameBuffer_left.handle)
			hg.SetViewRect(vid, 0, 0, int(vr_state.width), int(vr_state.height))
			hg.SetViewClear(vid, hg.CF_Color | hg.CF_Depth, 0xff0000, 1.0, 0)
			hg.SetViewTransform(vid, hg.InverseFast(vr_state.left.offset), vs_left_2.proj)
			matrx = vr_state.left.offset * hg.TransformationMat4(hg.Vec3(0, 0, focal_distance_left * z_ratio), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(2, 2, 2) * z_ratio)
			quad_uniform_set_texture_list.clear()
			quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex",  hg.GetColorTexture(scene2_frameBuffer_left), 0))
			hg.DrawModel(vid, quad_model, scenedisplay_prg, quad_uniform_set_value_list, quad_uniform_set_texture_list, matrx, quad_render_state)
			vid += 1

			z_near, z_far = hg.ExtractZRangeFromProjectionMatrix(vs_right_2.proj)
			z_ratio = (z_near + 0.01) / focal_distance_right
			hg.SetViewFrameBuffer(vid, post_process.quad_frameBuffer_right.handle)
			hg.SetViewRect(vid, 0, 0, int(vr_state.width), int(vr_state.height))
			hg.SetViewClear(vid, hg.CF_Color | hg.CF_Depth, 0xff0000, 1.0, 0)
			hg.SetViewTransform(vid, hg.InverseFast(vr_state.right.offset), vs_right_2.proj)
			matrx = vr_state.right.offset * hg.TransformationMat4(hg.Vec3(0, 0, focal_distance_right * z_ratio), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(2, 2, 2) * z_ratio)
			quad_uniform_set_texture_list.clear()
			quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.GetColorTexture(scene2_frameBuffer_right), 0))
			hg.DrawModel(vid, quad_model, scenedisplay_prg, quad_uniform_set_value_list, quad_uniform_set_texture_list, matrx, quad_render_state)
			vid += 1

			scene_2.canvas.clear_z = True
			scene_2.canvas.clear_color = False

			vid, passId = hg.PrepareSceneForwardPipelineCommonRenderData(vid, scene_2, render_data, pipeline, pl_resources, views)
			vr_eye_rect = hg.IntRect(0, 0, int(vr_resolution.x), int(vr_resolution.y))

			# Prepare the left eye render data then draw to its framebuffer
			vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs_left_2, scene_2, render_data, pipeline, pl_resources, views)
			vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene_2, vr_eye_rect, vs_left_2, pipeline, render_data, pl_resources, post_process.quad_frameBuffer_left.handle)

			# Prepare the right eye render data then draw to its framebuffer
			vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs_right_2, scene_2, render_data, pipeline, pl_resources, views)
			vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene_2, vr_eye_rect, vs_right_2, pipeline, render_data, pl_resources, post_process.quad_frameBuffer_right.handle)


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
		cam_mat = cam2.GetTransform().GetWorld()
		mat_spr = cam_mat  # * vr_state.initial_head_offset
		left_spr_proj = hg.ComputePerspectiveProjectionMatrix(0.1, 100, hg.ExtractZoomFactorFromProjectionMatrix(vs_left_2.proj), vr_ratio)
		right_spr_proj = hg.ComputePerspectiveProjectionMatrix(0.1, 100, hg.ExtractZoomFactorFromProjectionMatrix(vs_right_2.proj), vr_ratio)
		#mat_right = vr_state.body #head * vr_state.right.offset

		hg.SetViewFrameBuffer(vid, post_process.quad_frameBuffer_left.handle)
		hg.SetViewRect(vid, 0, 0, int(vr_resolution.x), int(vr_resolution.y))
		hg.SetViewTransform(vid, vs_left_2.view, left_spr_proj)
		for spr in sprites_display_list:
			spr.draw_vr(vid, mat_spr, resolution, vr_hud)
		vid += 1

		hg.SetViewFrameBuffer(vid, post_process.quad_frameBuffer_right.handle)
		hg.SetViewRect(vid, 0, 0, int(vr_resolution.x), int(vr_resolution.y))
		hg.SetViewTransform(vid, vs_right_2.view, right_spr_proj)
		for spr in sprites_display_list:
			spr.draw_vr(vid, mat_spr, resolution, vr_hud)
		vid += 1

	# ========== Post process:
	if not flag_vr:
		scene.canvas.clear_z = False
		scene.canvas.clear_color = False

		vid = post_process.display(vid, pl_resources, resolution)  # , pl_resources.GetTexture(water_reflexion.quad_frameBuffer.color))

	else:
		vid = post_process.display_vr(vid, vr_state, vs_left_1, vs_right_1, vr_left_fb, vr_right_fb, pl_resources)

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
