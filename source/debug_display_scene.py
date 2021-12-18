# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.
# Display asset with basic pipeline

import harfang as hg

hg.InputInit()
hg.WindowSystemInit()

res_x, res_y = 1280, 720
win = hg.RenderInit('Dislay_scene', res_x, res_y, hg.RF_VSync | hg.RF_MSAA4X)
hg.RenderReset(res_x, res_y, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

hg.AddAssetsFolder("assets_compiled")

# rendering pipeline
pipeline = hg.CreateForwardPipeline(2048)
res = hg.PipelineResources()


# Framebuffer
aa = 4
quad_frameBuffer = hg.CreateFrameBuffer(res_x, res_y, hg.TF_RGBA8, hg.TF_D32F, aa, res, "frameBuffer_postprocess")
quad_mdl = hg.VertexLayout()
quad_mdl.Begin()
quad_mdl.Add(hg.A_Position, 3, hg.AT_Float)
quad_mdl.Add(hg.A_TexCoord0, 3, hg.AT_Float)
quad_mdl.End()

quad_model = hg.CreatePlaneModel(quad_mdl, 1, 1, 1, 1)
quad_uniform_set_value_list = hg.UniformSetValueList()
quad_uniform_set_texture_list = hg.UniformSetTextureList()
quad_render_state = hg.ComputeRenderState(hg.BM_Opaque, hg.DT_Disabled, hg.FC_Disabled)
quad_matrix = hg.TransformationMat4(hg.Vec3(0, 0, 1), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(res_x, 1, res_y))

post_process_program = hg.LoadProgramFromAssets("shaders/post_process")

color = hg.Vec4(1, 1, 1, 1)
uv_scale = hg.Vec4(1, 1, 0, 0)
quad_uniform_set_value_list.clear()
quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("uv_scale", uv_scale))
quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("color", color))

# load host scene
scene = hg.Scene()
hg.LoadSceneFromAssets("main.scn", scene, res, hg.GetForwardPipelineInfo())
f= False
carrier_node = hg.CreateInstanceFromAssets(scene, hg.TranslationMat4(hg.Vec3(0, 0, 0)), "machines/aircraft_carrier_blend/aircraft_carrier_blend.scn", res, hg.GetForwardPipelineInfo(), f)
aircraft_node = hg.CreateInstanceFromAssets(scene, hg.TranslationMat4(hg.Vec3(10, 19.2, 80)), "machines/tfx/TFX.scn", res, hg.GetForwardPipelineInfo(), f)

camera = hg.CreateCamera(scene, hg.TransformationMat4(hg.Vec3(0, 19.5, 80), hg.Vec3(0, 0, 0)), 0.1, 10000, 40/180 * 3.141)


scene.SetCurrentCamera(camera)
scene.Update(0)
cam_pos = camera.GetTransform().GetPos()
cam_rot = camera.GetTransform().GetRot()
# main loop
mouse = hg.Mouse()
keyboard = hg.Keyboard()

views = hg.SceneForwardPipelinePassViewId()
render_data = hg.SceneForwardPipelineRenderData()

while not keyboard.Pressed(hg.K_Escape):
	_, res_x, res_y = hg.RenderResetToWindow(win, res_x, res_y, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)
	mouse.Update()
	keyboard.Update()

	dt = hg.TickClock()

	hg.FpsController(keyboard, mouse, cam_pos, cam_rot, 20 if keyboard.Down(hg.K_LShift) else 8, dt)

	camera.GetTransform().SetPos(cam_pos)
	camera.GetTransform().SetRot(cam_rot)

	scene.Update(dt)


	view_state = scene.ComputeCurrentCameraViewState(hg.ComputeAspectRatioX(res_x, res_y))
	vid, passId = hg.SubmitSceneToPipeline(0, scene, hg.IntRect(0, 0, res_x, res_y), view_state, pipeline, res)
	"""
	view_id = 0
	vs = scene.ComputeCurrentCameraViewState(hg.ComputeAspectRatioX(res_x, res_y))
	view_id, passId = hg.PrepareSceneForwardPipelineCommonRenderData(view_id, scene, render_data, pipeline, res, views)
	view_id, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(view_id, vs, scene, render_data, pipeline, res, views)
	view_id, passId = hg.SubmitSceneToForwardPipeline(view_id, scene, hg.IntRect(0, 0, res_x, res_y), vs, pipeline, render_data, res, quad_frameBuffer.handle)


	# Display texture:
	hg.SetViewRect(view_id, 0, 0, res_x, res_y)
	hg.SetViewClear(view_id, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
	vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(0, 0, 0)), res_y, 0.1, 100, hg.ComputeAspectRatioX(res_x, res_y))
	hg.SetViewTransform(view_id, vs.view, vs.proj)
	quad_uniform_set_texture_list.clear()
	quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", res.GetTexture(quad_frameBuffer.color), 0))
	hg.DrawModel(view_id, quad_model, post_process_program, quad_uniform_set_value_list, quad_uniform_set_texture_list, quad_matrix, quad_render_state)
	view_id += 1
	"""

	hg.Frame()
	hg.UpdateWindow(win)

hg.RenderShutdown()
hg.DestroyWindow(win)
