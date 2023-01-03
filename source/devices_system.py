# Display a scene in VR

import harfang as hg
import sys
import json

def str_to_booleans(script):
    for k, v in script.items():
        if v.__class__ == str:
            if v == "true": script[k] = True
            elif v == "false": script[k] = False
        elif v.__class__ == dict:
            str_to_booleans(v)

def booleans_to_str(script):
    for k, v in script.items():
        if v.__class__ == bool:
            script[k] = "true" if v else "false"
        elif v.__class__ == dict:
            booleans_to_str(v)

def save_device_configs(file_name, device_configs):
    file = open(file_name, "w")
    if file:
        booleans_to_str(device_configs)
        json_script = json.dumps(device_configs, indent=4)
        file.write(json_script)
        file.close()
        str_to_booleans(device_configs)
        return True
    else:
        print("ERROR - Can't open json file : " + file_name)
        return False

def load_devices_configurations_file(file_name):
    #file = hg.OpenText(file_name)
    file = open(file_name, "r")
    if not file:
        print("ERROR - Can't open json file : " + file_name)
    else:
        json_script = file.read()
        file.close()
        if json_script != "":
            jsonscript = json.loads(json_script)
            str_to_booleans(jsonscript)
            return jsonscript


def create_device_config(joystick:hg.Joystick):
    device_config = {}
    for j in range(joystick.ButtonsCount()):
        device_config[f"button_{j}"] = {
                                            "type": "button",
                                            "id": j,
                                            "name": f"Button  {j}"
                                        }
    for j in range(joystick.AxesCount()):
        device_config[f"axis_{j}"] = {
                                        "type": "axis",
                                        "name": f"Axis {j}",
                                        "reset": True,
                                        "invert": False,
                                        "id": j,
                                        "min": -1,
                                        "max": 1,
                                        "zero": 0,
                                        "zero_epsilon": 0.01
                                    }
    return device_config

hg.InputInit()
hg.WindowSystemInit()

devices = []
device_configurations = load_devices_configurations_file("scripts/devices_config.json")
joysticks = hg.GetJoystickNames()
flag_config_changes = False
for nm in joysticks:
    if nm != "" and nm !="default":
        joystick = hg.Joystick(nm)
        joystick.Update()
        if joystick.IsConnected():
            device_name = joystick.GetDeviceName()
            if device_name not in device_configurations:
                device_configurations[device_name] = create_device_config(joystick)
                flag_config_changes = True
            devices.append(joystick)

if flag_config_changes:
    save_device_configs("scripts/new_devices_config.json", device_configurations)

#get_devices(False)

def test_vr():

    hg.InputInit()
    hg.WindowSystemInit()

    res_x, res_y = 1280, 720
    win = hg.NewWindow(res_x, res_y)
    hg.RenderInit(win, hg.RT_OpenGL)
    hg.RenderReset(res_x, res_y, hg.RF_MSAA4X | hg.RF_MaxAnisotropy)
    
    #win = hg.RenderInit("Harfang - OpenVR Scene", res_x, res_y, hg.RF_VSync | hg.RF_MSAA4X)

    hg.AddAssetsFolder("assets_compiled")

    pipeline = hg.CreateForwardPipeline()
    res = hg.PipelineResources()

    render_data = hg.SceneForwardPipelineRenderData()  # this object is used by the low-level scene rendering API to share view-independent data with both eyes

    # OpenVR initialization
    
    if not hg.OpenVRInit():
        sys.exit()

    #get_devices(True)

    vr_left_fb = hg.OpenVRCreateEyeFrameBuffer(hg.OVRAA_MSAA4x)
    vr_right_fb = hg.OpenVRCreateEyeFrameBuffer(hg.OVRAA_MSAA4x)

    # Create models
    vtx_layout = hg.VertexLayoutPosFloatNormUInt8()

    cube_mdl = hg.CreateCubeModel(vtx_layout, 1, 1, 1)
    cube_ref = res.AddModel('cube', cube_mdl)
    ground_mdl = hg.CreateCubeModel(vtx_layout, 50, 0.01, 50)
    ground_ref = res.AddModel('ground', ground_mdl)

    # Load shader
    prg_ref = hg.LoadPipelineProgramRefFromAssets('core/shader/pbr.hps', res, hg.GetForwardPipelineInfo())

    # Create materials
    def create_material(ubc, orm):
        mat = hg.Material()
        hg.SetMaterialProgram(mat, prg_ref)
        hg.SetMaterialValue(mat, "uBaseOpacityColor", ubc)
        hg.SetMaterialValue(mat, "uOcclusionRoughnessMetalnessColor", orm)
        return mat


    # Create scene
    scene = hg.Scene()
    scene.canvas.color = hg.Color(255 / 255, 255 / 255, 217 / 255, 1)
    scene.environment.ambient = hg.Color(15 / 255, 12 / 255, 9 / 255, 1)

    lgt = hg.CreateSpotLight(scene, hg.TransformationMat4(hg.Vec3(-8, 4, -5), hg.Vec3(hg.Deg(19), hg.Deg(59), 0)), 0, hg.Deg(5), hg.Deg(30), hg.Color.White, hg.Color.White, 10, hg.LST_Map, 0.0001)
    back_lgt = hg.CreatePointLight(scene, hg.TranslationMat4(hg.Vec3(2.4, 1, 0.5)), 10, hg.Color(94 / 255, 255 / 255, 228 / 255, 1), hg.Color(94 / 255, 1, 228 / 255, 1), 0)

    mat_cube = create_material(hg.Vec4(255 / 255, 230 / 255, 20 / 255, 1), hg.Vec4(1, 0.658, 0., 1))
    hg.CreateObject(scene, hg.TransformationMat4(hg.Vec3(0, 0.5, 0), hg.Vec3(0, hg.Deg(70), 0)), cube_ref, [mat_cube])

    mat_ground = create_material(hg.Vec4(255 / 255, 120 / 255, 147 / 255, 1), hg.Vec4(1, 1, 0.1, 1))
    hg.CreateObject(scene, hg.TranslationMat4(hg.Vec3(0, 0, 0)), ground_ref, [mat_ground])

    # Setup 2D rendering to display eyes textures
    quad_layout = hg.VertexLayout()
    quad_layout.Begin().Add(hg.A_Position, 3, hg.AT_Float).Add(hg.A_TexCoord0, 3, hg.AT_Float).End()

    quad_model = hg.CreatePlaneModel(quad_layout, 1, 1, 1, 1)
    quad_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Disabled, hg.FC_Disabled)

    eye_t_size = res_x / 2.5
    eye_t_x = (res_x - 2 * eye_t_size) / 6 + eye_t_size / 2
    quad_matrix = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(eye_t_size, 1, eye_t_size))

    tex0_program = hg.LoadProgramFromAssets("shaders/sprite")

    quad_uniform_set_value_list = hg.UniformSetValueList()
    quad_uniform_set_value_list.clear()
    quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("color", hg.Vec4(1, 1, 1, 1)))

    quad_uniform_set_texture_list = hg.UniformSetTextureList()

    # Main loop
    while not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(win):
        dt = hg.TickClock()

        scene.Update(dt)

        actor_body_mtx = hg.TransformationMat4(hg.Vec3(-1.3, .45, -2), hg.Vec3(0, 0, 0))

        vr_state = hg.OpenVRGetState(actor_body_mtx, 0.01, 1000)
        left, right = hg.OpenVRStateToViewState(vr_state)

        vid = 0  # keep track of the next free view id
        passId = hg.SceneForwardPipelinePassViewId()

        # Prepare view-independent render data once
        vid, passId = hg.PrepareSceneForwardPipelineCommonRenderData(vid, scene, render_data, pipeline, res, passId)
        vr_eye_rect = hg.IntRect(0, 0, vr_state.width, vr_state.height)

        # Prepare the left eye render data then draw to its framebuffer
        vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, left, scene, render_data, pipeline, res, passId)
        vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, vr_eye_rect, left, pipeline, render_data, res, vr_left_fb.GetHandle())

        # Prepare the right eye render data then draw to its framebuffer
        vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, right, scene, render_data, pipeline, res, passId)
        vid, passId = hg.SubmitSceneToForwardPipeline(vid, scene, vr_eye_rect, right, pipeline, render_data, res, vr_right_fb.GetHandle())

        # Display the VR eyes texture to the backbuffer
        hg.SetViewRect(vid, 0, 0, res_x, res_y)
        vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(0, 0, 0)), res_y, 0.1, 100, hg.ComputeAspectRatioX(res_x, res_y))
        hg.SetViewTransform(vid, vs.view, vs.proj)

        quad_uniform_set_texture_list.clear()
        quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.OpenVRGetColorTexture(vr_left_fb), 0))
        hg.SetT(quad_matrix, hg.Vec3(eye_t_x, 0, 1))
        hg.DrawModel(vid, quad_model, tex0_program, quad_uniform_set_value_list, quad_uniform_set_texture_list, quad_matrix, quad_render_state)

        quad_uniform_set_texture_list.clear()
        quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.OpenVRGetColorTexture(vr_right_fb), 0))
        hg.SetT(quad_matrix, hg.Vec3(-eye_t_x, 0, 1))
        hg.DrawModel(vid, quad_model, tex0_program, quad_uniform_set_value_list, quad_uniform_set_texture_list, quad_matrix, quad_render_state)

        hg.Frame()
        hg.OpenVRSubmitFrame(vr_left_fb, vr_right_fb)

        hg.UpdateWindow(win)

    hg.DestroyForwardPipeline(pipeline)
    hg.RenderShutdown()
    hg.DestroyWindow(win)

def get_button_by_id(device_config, id):
    for k, v in device_config.items():
        if v["type"] == "button" and v["id"] == id:
            return v
    return None

def get_axis_by_id(device_config, id):
    for k, v in device_config.items():
        if v["type"] == "axis" and v["id"] == id:
            return v
    return None

def test(device_configurations):
    hg.InputInit()
    hg.WindowSystemInit()

    res_x, res_y = 600, 800
    win = hg.NewWindow(res_x, res_y)
    hg.RenderInit(win, hg.RT_OpenGL)
    hg.RenderReset(res_x, res_y, hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

    hg.AddAssetsFolder("assets_compiled")

    imgui_prg = hg.LoadProgramFromAssets("core/shader/imgui")
    imgui_img_prg = hg.LoadProgramFromAssets("core/shader/imgui_image")

    hg.ImGuiInit(10, imgui_prg, imgui_img_prg)

    joysticks = hg.GetJoystickNames()
    for joystick_name in joysticks:
        joystick = hg.Joystick(joystick_name)
        dev_name = joystick.GetDeviceName()
        print(joystick_name + " - " + dev_name)
    vr_controller_names = hg.GetVRControllerNames()
    for vrc_name in vr_controller_names:
        print(vrc_name)

    while not hg.ReadKeyboard().Key(hg.K_Escape):
        hg.ImGuiBeginFrame(res_x, res_y, hg.TickClock(), hg.ReadMouse(), hg.ReadKeyboard())

        joysticks = hg.GetJoystickNames()

        for joystick_name in joysticks:
            if joystick_name != "default":
                generic_controller = hg.Joystick(joystick_name)
                generic_controller.Update()
                if generic_controller.IsConnected():
                    dev_name = generic_controller.GetDeviceName()
                    if hg.ImGuiCollapsingHeader(joystick_name + " - " + dev_name):
                        hg.ImGuiIndent()
                        for j in range(generic_controller.ButtonsCount()):
                            btn_config = get_button_by_id(device_configurations[dev_name], j)
                            if btn_config is not None:
                                hg.ImGuiText(f"button {j} - {btn_config['name']}: {generic_controller.Down(j)}")
                            else:
                                hg.ImGuiText(f"button {j} - undefined: {generic_controller.Down(j)}")
                        for j in range(generic_controller.AxesCount()):
                            axis_config = get_axis_by_id(device_configurations[dev_name], j)
                            if axis_config is not None:
                                hg.ImGuiText(f"axe {j} - {axis_config['name']}: {generic_controller.Axes(j)}")
                            else:
                                hg.ImGuiText(f"axe {j} - undefined: {generic_controller.Axes(j)}")
                        hg.ImGuiUnindent()
        
        hg.SetView2D(0, 0, 0, res_x, res_y, -1, 1, hg.CF_Color | hg.CF_Depth, hg.Color.Black, 1, 0)
        hg.ImGuiEndFrame(0)
        hg.Frame()
        hg.UpdateWindow(win)

    hg.RenderShutdown()
    hg.DestroyWindow(win)

test(device_configurations)