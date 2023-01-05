# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from Machines import *
from MachineDevice import *
from aircraft_miuss import *
from aircraft_tfx import *
from aircraft_f16 import *
from aircraft_f14 import *
from aircraft_f14_2 import *
from aircraft_rafale import *
from aircraft_eurofighter import *
from MissileLauncherS400 import *
from missile_Sidewinder import *
from missile_Meteor import *
from missile_Mica import *
from missile_aim_sl import *
from missile_karaoke import *
from missile_S400 import *
from addon_cft import *
from SmartCamera import *
import json
import data_converter as dc
import network_server as netws
from Sprites import *
from PostProcess import *
from HUD import *
from Missions import *
from planet_render import *
from WaterReflection import *
from overlays import *
from math import atan
import vcr


class Main:

    inputs_commands = None
    
    # Main display configuration (user-defined in "config.json" file)

    flag_fullscreen = False
    resolution = hg.Vec2(1920, 1080)
    flag_shadowmap = True
    flag_OpenGL = True
    antialiasing = 4
    flag_display_HUD = True
    flag_display_recorder = False

    # Control devices

    control_mode = ControlDevice.CM_KEYBOARD
    devices_configurations_file = "scripts/devices_config.json"
    aircraft_inputs_mapping_encoded = None # Used in menu state. Might be improved/remove in case of adding an input device configuration api.

    # VR mode
    flag_vr = False
    vr_left_fb = None
    vr_right_fb = None
    # VR screen display
    vr_quad_layout = None
    vr_quad_model = None
    vr_quad_render_state = None
    eye_t_x = 0
    vr_quad_matrix = None
    vr_tex0_program = None
    vr_quad_uniform_set_value_list = None
    vr_quad_uniform_set_texture_list = None
    vr_hud = None # vec3 width, height, zdistance

    vr_state = None # OpenVRState

    initial_head_matrix = None

    #
    flag_exit = False
    win = None

    framecount = 0  # Frame count.
    timer = 0 # clock in s (incremented at each frame)

    timestep = 1 / 60  # Frame dt
    simulation_dt = 0 # dt in ns used by simulation (kinetics & renderer) 

    flag_network_mode = False
    flag_client_update_mode = False
    flag_client_connected = False
    flag_client_ask_update_scene = False

    flag_renderless = False
    flag_running = False
    flag_display_radar_in_renderless = True
    frame_time = 0 # Used to synchronize Renderless display informations
    flag_activate_particles_mem = True
    flag_sfx_mem = True
    max_view_id = 0

    assets_compiled = "assets_compiled"

    allies_missiles_smoke_color = hg.Color(1.0, 1.0, 1.0, 1.0)
    ennemies_missiles_smoke_color = hg.Color(1.0, 1.0, 1.0, 1.0)

    flag_sfx = True
    flag_control_views = True
    flag_display_fps = False
    flag_display_landing_trajectories = False
    flag_display_selected_aircraft = False
    flag_display_machines_bounding_boxes = False
    flag_display_physics_debug = False
    nfps = [0] * 100
    nfps_i = 0
    num_fps = 0

    post_process = None
    render_data = None
    scene = None
    scene_physics = None
    clocks = None

    flag_gui = False

    sea_render = None
    water_reflexion = None

    num_start_frames = 10
    keyboard = None
    mouse = None
    pipeline = None

    current_state = None
    t = 0
    fading_to_next_state = False
    next_state = "main" #Used to switch to replay state
    end_state_timer = 0
    end_state_following_aircraft = None

    current_view = None
    camera = None
    camera_fps = None

    intro_anim_id = 2
    camera_intro = None
    anim_camera_intro_dist = None
    anim_camera_intro_rot = None
    display_dark_design = True
    display_logo = True

    satellite_camera = None
    satellite_view = False
    aircraft = None
    ennemy_aircraft = None
    user_aircraft = None
    player_view_mode = SmartCamera.TYPE_TRACKING

    aircraft_carrier_allies = []
    aircraft_carrier_ennemies = []

    missile_launchers_allies = []
    missile_launchers_ennemies = []

    smart_camera = None

    pl_resources = None

    background_color = 0x1070a0ff  # 0xb9efffff

    ennemyaircraft_nodes = None
    players_allies = []
    players_ennemies = []
    players_sfx = []
    missiles_allies = []
    missiles_ennemies = []
    missiles_sfx = []
    views_carousel = []
    views_carousel_ptr = 0

    sprites_display_list = []
    #texts_display_list = []

    destroyables_list = []  # whole missiles, aircrafts, ships used by HUD radar
    destroyables_items = {} # items stored by their names

    font_program = None
    title_font_path = "font/destroy.ttf"
    hud_font_path = "font/Furore.otf"
    title_font = None
    hud_font = None
    text_matrx = None
    text_uniform_set_values = hg.UniformSetValueList()
    text_uniform_set_texture_list = hg.UniformSetTextureList()
    text_render_state = None

    fading_cptr = 0
    menu_fading_cptr = 0

    spr_design_menu = None
    spr_logo = None

    main_music_ref = []
    main_music_state = []
    main_music_source = []

    master_sfx_volume = 0

    # Cockpit view:
    flag_cockpit_view = False
    
    
    scene_cockpit = None
    scene_cockpit_frameBuffer = None
    scene_cockpit_frameBuffer_left = None
    scene_cockpit_frameBuffer_right = None
    scene_cockpit_aircrafts = []  # Aircrafts models used for cockpit view (1 model by aircraft type)
    user_cockpit_aircraft = None
    cockpit_scene_quad_model = None
    cockpit_scene_quad_uniform_set_value_list = None
    cockpit_scene_quad_uniform_set_texture_list = None

    #======= Aircrafts view:
    selected_aircraft_id = 0
    selected_machine = None

    @classmethod
    def init(cls):
        cls.pl_resources = hg.PipelineResources()
        cls.keyboard = hg.Keyboard()
        cls.mouse = hg.Mouse()
        
        Overlays.init()
        ControlDevice.init(cls.keyboard, cls.mouse, cls.devices_configurations_file)

    @classmethod
    def setup_vr(cls):
        if not hg.OpenVRInit():
            return False

        cls.vr_left_fb = hg.OpenVRCreateEyeFrameBuffer(hg.OVRAA_MSAA4x)
        cls.vr_right_fb = hg.OpenVRCreateEyeFrameBuffer(hg.OVRAA_MSAA4x)

        body_mtx = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(0, 0, 0))
        cls.vr_state = hg.OpenVRGetState(body_mtx, 1, 1000)
        cls.vr_resolution = hg.Vec2(cls.vr_state.width, cls.vr_state.height)

        cls.update_initial_head_matrix(cls.vr_state)

        # Setup vr screen display:

        cls.vr_quad_layout = hg.VertexLayout()
        cls.vr_quad_layout.Begin().Add(hg.A_Position, 3, hg.AT_Float).Add(hg.A_TexCoord0, 3, hg.AT_Float).End()

        cls.vr_quad_model = hg.CreatePlaneModel(cls.vr_quad_layout, 1, 1, 1, 1)
        cls.vr_quad_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Disabled, hg.FC_Disabled)

        eye_t_size = cls.resolution.x / 2.5
        cls.eye_t_x = (cls.resolution.x - 2 * eye_t_size) / 6 + eye_t_size / 2
        cls.vr_quad_matrix = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(hg.Deg(90), hg.Deg(0), hg.Deg(0)), hg.Vec3(eye_t_size, 1, eye_t_size))

        cls.vr_tex0_program = hg.LoadProgramFromAssets("shaders/vrdisplay")

        cls.vr_quad_uniform_set_value_list = hg.UniformSetValueList()
        cls.vr_quad_uniform_set_value_list.clear()
        cls.vr_quad_uniform_set_value_list.push_back(hg.MakeUniformSetValue("color", hg.Vec4(1, 1, 1, 1)))

        cls.vr_quad_uniform_set_texture_list = hg.UniformSetTextureList()

        ratio = cls.resolution.x / cls.resolution.y
        size = 10
        cls.vr_hud = hg.Vec3(size * ratio, size, 12)

        return True

    @classmethod
    def init_game(cls):
        cls.init()
        cls.render_data = hg.SceneForwardPipelineRenderData()

        cls.scene = hg.Scene()
        cls.scene_physics = hg.SceneBullet3Physics()
        cls.clocks = hg.SceneClocks()
        cls.scene_physics.StepSimulation(hg.time_from_sec_f(1 / 60))

        hg.LoadSceneFromAssets("main.scn", cls.scene, cls.pl_resources, hg.GetForwardPipelineInfo())
        Destroyable_Machine.world_node = cls.scene.GetNode("world_node")

        # Remove Dummies objects:

        nl = cls.scene.GetAllNodes()
        num = nl.size()
        for i in range(num):
            nd = nl.at(i)
            node_name = nd.GetName()
            if node_name.split("_")[0] == "dummy":
                nd.RemoveObject()
                cls.scene.GarbageCollect()

        # print("GARBAGE: "+str(cls.scene.GarbageCollect()))

        cls.camera_cokpit = cls.scene.GetNode("Camera_cokpit")
        cls.camera = cls.scene.GetNode("Camera_follow")
        cls.camera_fps = cls.scene.GetNode("Camera_fps")
        cls.satellite_camera = cls.scene.GetNode("Camera_satellite")
        cls.smart_camera = SmartCamera(SmartCamera.TYPE_FOLLOW, cls.keyboard, cls.mouse)
        #  Camera used in start state :
        cls.camera_intro = cls.scene.GetNode("Camera_intro")

        # Shadows setup
        sun = cls.scene.GetNode("Sun")
        if cls.flag_shadowmap:
            sun.GetLight().SetShadowType(hg.LST_Map)
        else:
            sun.GetLight().SetShadowType(hg.LST_None)

        if cls.flag_vr:
            framebuffers_resolution = cls.vr_resolution
        else:
            framebuffers_resolution = cls.resolution

        # ---------- Post process setup

        cls.post_process = PostProcess(framebuffers_resolution, cls.antialiasing, cls.flag_vr)

        # ---------- Destroyable machines original nodes lists:

        F14.init(cls.scene)
        F14_2.init(cls.scene)
        Rafale.init(cls.scene)
        Sidewinder.init(cls.scene)
        Meteor.init(cls.scene)
        Mica.init(cls.scene)

        # -------------- Sprites:
        Sprite.init_system()

        HUD.init(cls.resolution)
        HUD_Radar.init(cls.resolution)
        HUD_MachineGun.init(cls.resolution)
        HUD_MissileTarget.init(cls.resolution)

        cls.spr_design_menu = Sprite(1280, 720, "sprites/design_menu_b.png")
        cls.spr_design_menu.set_size(cls.resolution.x / 1280)

        cls.spr_logo = Sprite(1920, 1080, "sprites/dogfight.png")
        cls.spr_logo.set_size(cls.resolution.x / 1920)

        # -------------- Fonts
        cls.font_program = hg.LoadProgramFromAssets("core/shader/font.vsb", "core/shader/font.fsb")
        cls.hud_font = hg.LoadFontFromAssets(cls.hud_font_path, 64)
        cls.title_font = hg.LoadFontFromAssets(cls.title_font_path, 80)
        cls.text_matrx = hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(hg.Deg(0), hg.Deg(0), hg.Deg(0)), hg.Vec3(1, -1, 1))
        cls.text_uniform_set_values.push_back(hg.MakeUniformSetValue("u_color", hg.Vec4(1, 1, 0, 1)))
        cls.text_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Disabled, hg.FC_Disabled)

        # --------------- Sky & sea render:

        cls.sea_render = PlanetRender(cls.scene, framebuffers_resolution, cls.scene.GetNode("island_clipped").GetTransform().GetPos(), hg.Vec3(-20740.2158, 0, 9793.1535))
        cls.sea_render.load_json_script()

        cls.water_reflexion = WaterReflection(cls.scene, framebuffers_resolution, cls.antialiasing, cls.flag_vr)

        # ---------------- Musics:
        cls.main_music_ref = [hg.LoadWAVSoundAsset("sfx/main_left.wav"), hg.LoadWAVSoundAsset("sfx/main_right.wav")]
        cls.main_music_state = [tools.create_stereo_sound_state(hg.SR_Loop), tools.create_stereo_sound_state(hg.SR_Loop)]

        # --------------- Missions:
        cls.load_json_script()
        Missions.init()

        # ---------------- Physics:
        Physics.init_physics(cls.scene, cls.scene_physics, "pictures/height.png", hg.Vec3(cls.sea_render.terrain_position.x, -292, cls.sea_render.terrain_position.z), hg.Vec3(cls.sea_render.terrain_scale.x, 1000, cls.sea_render.terrain_scale.z), hg.Vec2(0, 255))

        cls.scene.Update(0)

    @classmethod
    def update_user_control_mode(cls):
        for machine in cls.destroyables_list:
            user_control_device = machine.get_device("UserControlDevice")
            ia_control_device = machine.get_device("IAControlDevice")
            if user_control_device is not None:
                user_control_device.set_control_mode(cls.control_mode)
            if ia_control_device is not None:
                ia_control_device.set_control_mode(cls.control_mode)

    @classmethod
    def duplicate_scene_lighting(cls, scene_src, scene_dst):
        env0 = scene_src.environment
        env2 = scene_dst.environment
        env2.ambient = env0.ambient
        env2.brdf_map = env0.brdf_map
        env2.fog_color = env0.fog_color
        env2.fog_far = env0.fog_far
        env2.fog_near = env0.fog_near
        env2.irradiance_map = env0.irradiance_map
        env2.radiance_map = env0.radiance_map
        sun0 = scene_src.GetNode("Sun")
        light0 = sun0.GetLight()
        hg.CreateLinearLight(scene_dst, sun0.GetTransform().GetWorld(), light0.GetDiffuseColor(), 1, light0.GetSpecularColor(), 1, light0.GetPriority(), light0.GetShadowType(), 0.008, hg.Vec4(1, 2, 4, 10))

    @classmethod
    def set_activate_sfx(cls, flag):
        if flag != cls.flag_sfx:
            if flag:
                cls.setup_sfx()
            else:
                cls.destroy_sfx()
        cls.flag_sfx = flag

    @classmethod
    def clear_views(cls):
        for vid in range(cls.max_view_id+1):
            hg.SetViewFrameBuffer(vid, hg.InvalidFrameBufferHandle)
            hg.SetViewRect(vid, 0, 0, int(cls.resolution.x), int(cls.resolution.y))
            hg.SetViewClear(vid, hg.CF_Depth, 0x0, 1.0, 0)
            hg.Touch(vid)
        hg.Frame()

    @classmethod
    def set_renderless_mode(cls, flag: bool):
        cls.flag_renderless = flag
        cls.flag_running = False
        if flag:
            cls.flag_activate_particles_mem = Destroyable_Machine.flag_activate_particles
            cls.flag_sfx_mem = cls.flag_sfx
            cls.set_activate_sfx(False)
            Destroyable_Machine.set_activate_particles(False)
            cls.frame_time = 0
        else:
            cls.set_activate_sfx(cls.flag_sfx_mem)
            Destroyable_Machine.set_activate_particles(cls.flag_activate_particles_mem)

        vid = 0
        hg.SetViewFrameBuffer(vid, hg.InvalidFrameBufferHandle)
        hg.SetViewRect(vid, 0, 0, int(cls.resolution.x), int(cls.resolution.y))
        hg.SetViewClear(vid, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
        cls.flag_running = True

    @classmethod
    def update_num_fps(cls, dts):
        cls.nfps[cls.nfps_i] = 1 / dts
        cls.nfps_i = (cls.nfps_i + 1) % len(cls.nfps)
        cls.num_fps = 0
        for ne in cls.nfps:
            cls.num_fps += ne
        cls.num_fps = cls.num_fps / len(cls.nfps)

    @classmethod
    def clear_scene(cls):
        cls.selected_machine = None
        cls.user_aircraft = None
        cls.set_view_carousel("fps")
        cls.destroy_players()
        cls.destroy_sfx()
        ParticlesEngine.reset_engines()
        Destroyable_Machine.reset_machines()
        cls.setup_views_carousel(False)

    @classmethod
    def destroy_players(cls):
        """
        for aircraft in cls.players_ennemies:
            aircraft.destroy()
        for aircraft in cls.players_allies:
            aircraft.destroy()
        for carrier in cls.aircraft_carrier_allies:
            carrier.destroy()
        for carrier in cls.aircraft_carrier_ennemies:
            carrier.destroy()
        for ml in cls.missile_launchers_ennemies:
            ml.destroy()
        for ml in cls.missile_launchers_allies:
            ml.destroy()
        """
        for machine in cls.destroyables_list:
            machine.destroy()

        for cockpit in cls.scene_cockpit_aircrafts:
            cockpit.destroy()

        cls.missiles_allies = []
        cls.missiles_ennemies = []
        cls.players_ennemies = []
        cls.players_allies = []
        cls.destroyables_list = []
        cls.aircraft_carrier_allies = []
        cls.aircraft_carrier_ennemies = []
        cls.missile_launchers_allies = []
        cls.missile_launchers_ennemies = []

        cls.scene_cockpit_aircrafts = []

    @classmethod
    def create_aircraft_carrier(cls, name, nationality):
        carrier = Carrier(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality)
        if carrier is not None:
            if nationality == 1:
                cls.aircraft_carrier_allies.append(carrier)
            elif nationality == 2:
                cls.aircraft_carrier_ennemies.append(carrier)
            cls.destroyables_list.append(carrier)
            carrier.add_to_update_list()


    @classmethod
    def create_aircraft_carriers(cls, num_allies, num_ennemies):

        cls.aircraft_carrier_allies = []
        cls.aircraft_carrier_ennemies = []
        for i in range(num_allies):
            carrier = cls.create_aircraft_carrier("Ally_Carrier_" + str(i + 1), 1)
            
        for i in range(num_ennemies):
            carrier = cls.create_aircraft_carrier("Ennemy_Carrier_" + str(i + 1), 2)


    @classmethod
    def create_missile(cls, model_name, name, nationality):
        if model_name == Sidewinder.model_name:
            missile = Sidewinder(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality)
        elif model_name == Meteor.model_name:
            missile = Meteor(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality)
        elif model_name == Mica.model_name:
            missile = Mica(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality)
        elif model_name == AIM_SL.model_name:
            missile = AIM_SL(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality)
        elif model_name == Karaoke.model_name:
            missile = Karaoke(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality)
        elif model_name == CFT.model_name:
            missile = CFT(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality)
        elif model_name == S400.model_name:
            missile = S400(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality)
        else:
            missile = None
        if missile is not None:
            if nationality == 1:
                cls.missiles_allies.append(missile)
            elif nationality == 2:
                cls.missiles_ennemies.append(missile)
            cls.destroyables_list.append(missile)
        return missile


    @classmethod
    def create_missiles_from_machine_config(cls, machine:Destroyable_Machine, smoke_color):
        md = machine.get_device("MissilesDevice")
        md.set_missiles_config(machine.missiles_config)
        if md is not None:
            for j in range(md.num_slots):
                missile_type = md.missiles_config[j]
                missile = cls.create_missile(missile_type, machine.name + "-" + missile_type + "-" + str(j), machine.nationality)
                md.fit_missile(missile, j)
                missile.set_smoke_color(smoke_color)
            return md.missiles
        return None

    @classmethod
    def create_missile_launcher(cls, name, nationality):
        launcher = MissileLauncherS400(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality, hg.Vec3(0, 500, 0), hg.Vec3(0, 0, 0))
        if launcher is not None:
            if nationality == 1:
                cls.missile_launchers_allies.append(launcher)
            elif nationality == 2:
                cls.missile_launchers_ennemies.append(launcher)
            cls.destroyables_list.append(launcher)
            launcher.add_to_update_list()
        return launcher

    @classmethod
    def create_missile_launchers(cls, num_allies, num_ennemies):
        cls.missile_launchers_allies = []
        cls.missile_launchers_ennemies = []

        for i in range(num_allies):
            launcher = cls.create_missile_launcher("Ally_Missile_launcher_" + str(i + 1), 1)
            missiles = cls.create_missiles_from_machine_config(launcher, cls.allies_missiles_smoke_color)

        for i in range(num_ennemies):
            launcher = cls.create_missile_launcher("Ennemy_Missile_launcher_" + str(i + 1), 2)
            missiles = cls.create_missiles_from_machine_config(launcher, cls.ennemies_missiles_smoke_color)


    @classmethod
    def create_aircraft(cls,model_name, name, nationality):
        if model_name == F14_Parameters.model_name:
            aircraft = F14(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality, hg.Vec3(0, 500, 0), hg.Vec3(0, 0, 0))
        elif model_name == F14_2_Parameters.model_name:
            aircraft = F14_2(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality, hg.Vec3(0, 500, 0), hg.Vec3(0, 0, 0))
        elif model_name == Rafale_Parameters.model_name:
            aircraft = Rafale(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality, hg.Vec3(0, 500, 0), hg.Vec3(0, 0, 0))
        elif model_name == Eurofighter_Parameters.model_name:
            aircraft = Eurofighter(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality, hg.Vec3(0, 500, 0), hg.Vec3(0, 0, 0))
        elif model_name == F16_Parameters.model_name:
            aircraft = F16(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality, hg.Vec3(0, 500, 0), hg.Vec3(0, 0, 0))
        elif model_name == TFX_Parameters.model_name:
            aircraft = TFX(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality, hg.Vec3(0, 500, 0), hg.Vec3(0, 0, 0))
        elif model_name == Miuss_Parameters.model_name:
            aircraft = Miuss(name, cls.scene, cls.scene_physics, cls.pl_resources, nationality, hg.Vec3(0, 500, 0), hg.Vec3(0, 0, 0))
        else:
            aircraft = None
        
        if aircraft is not None:
            cls.destroyables_list.append(aircraft)
            aircraft.add_to_update_list()
            if nationality == 1:
                cls.players_allies.append(aircraft)
            elif nationality == 2:
                cls.players_ennemies.append(aircraft)
        
        return aircraft

    @classmethod
    def create_players(cls, allies_types, ennemies_types):
        cls.players_allies = []
        cls.players_ennemies = []
        cls.missiles_allies = []
        cls.missiles_ennemies = []
        cls.players_sfx = []
        cls.missiles_sfx = []

        for i, model_name in enumerate(allies_types):
            aircraft = cls.create_aircraft(model_name, "ally_" + str(i + 1), 1)
            missiles = cls.create_missiles_from_machine_config(aircraft, cls.allies_missiles_smoke_color)

        for i, model_name in enumerate(ennemies_types):
            aircraft = cls.create_aircraft(model_name, "ennemy_" + str(i + 1), 2)
            missiles = cls.create_missiles_from_machine_config(aircraft, cls.ennemies_missiles_smoke_color)

        if cls.flag_sfx:
            cls.setup_sfx()

        #cls.scene_physics.SceneCreatePhysicsFromAssets(cls.scene)
        cls.update_user_control_mode()

    @classmethod
    def setup_sfx(cls):
        hg.StopAllSources()
        cls.players_sfx = []
        cls.missiles_sfx = []
        for machine in cls.destroyables_list:
            if machine.type == Destroyable_Machine.TYPE_AIRCRAFT:
                cls.players_sfx.append(AircraftSFX(machine))
            elif machine.type == Destroyable_Machine.TYPE_MISSILE:
                cls.missiles_sfx.append(MissileSFX(machine))

    @classmethod
    def destroy_sfx(cls):
        hg.StopAllSources()
        cls.players_sfx = []
        cls.missiles_sfx = []

    @classmethod
    def init_playground(cls):

        cls.scene.Update(0)

        lt_allies = []
        for carrier in cls.aircraft_carrier_allies:
            lt_allies += carrier.landing_targets
        lt_ennemies = []
        for carrier in cls.aircraft_carrier_ennemies:
            lt_ennemies += carrier.landing_targets

        for i, pl in enumerate(cls.players_allies):
            td = pl.get_device("TargettingDevice")
            td.set_destroyable_targets(cls.players_ennemies)
            pl.set_landing_targets(lt_allies)
            td.targets = cls.players_ennemies
            if len(cls.players_ennemies) > 0:
                td.set_target_id(int(uniform(0, 1000) % len(cls.players_ennemies)))

        for i, pl in enumerate(cls.missile_launchers_allies):
            td = pl.get_device("TargettingDevice")
            td.set_destroyable_targets(cls.players_ennemies)
            td.targets = cls.players_ennemies
            if len(cls.players_ennemies) > 0:
                td.set_target_id(int(uniform(0, 1000) % len(cls.players_ennemies)))

        for i, pl in enumerate(cls.players_ennemies):
            td = pl.get_device("TargettingDevice")
            td.set_destroyable_targets(cls.players_allies)
            pl.set_landing_targets(lt_ennemies)
            td.targets = cls.players_allies
            if len(cls.players_allies) > 0:
                td.set_target_id(int(uniform(0, 1000) % len(cls.players_allies)))

        for i, pl in enumerate(cls.missile_launchers_ennemies):
            td = pl.get_device("TargettingDevice")
            td.set_destroyable_targets(cls.players_allies)
            td.targets = cls.players_allies
            if len(cls.players_allies) > 0:
                td.set_target_id(int(uniform(0, 1000) % len(cls.players_allies)))


        cls.destroyables_items = {}
        for dm in cls.destroyables_list:
            cls.destroyables_items[dm.name] = dm

        Destroyable_Machine.machines_list = cls.destroyables_list # !!! Move to Destroyable_Machine.__init__()
        Destroyable_Machine.machines_items = cls.destroyables_items # !!! Move to Destroyable_Machine.__init__()

        # Setup HUD systems:
        n_aircrafts = len(cls.players_allies) + len(cls.players_ennemies)
        n_missile_launchers = len(cls.missile_launchers_allies) + len(cls.missile_launchers_ennemies)
        n_missiles = len(cls.missiles_allies) + len(cls.missiles_ennemies)

        HUD_Radar.setup_plots(cls.resolution, n_aircrafts, n_missiles, len(cls.aircraft_carrier_allies) + len(cls.aircraft_carrier_ennemies), n_missile_launchers)

    # ----------------- Views -------------------------------------------------------------------
    @classmethod
    def update_initial_head_matrix(cls, vr_state: hg.OpenVRState):
        mat_head = hg.InverseFast(vr_state.body) * vr_state.head
        rot = hg.GetR(mat_head)
        rot.x = 0
        rot.z = 0
        cls.initial_head_matrix = hg.TransformationMat4(hg.GetT(mat_head), rot)

    @classmethod
    def setup_views_carousel(cls, flag_include_enemies=False):
        if len(cls.aircraft_carrier_allies) > 0:
            fps_start_matrix = cls.aircraft_carrier_allies[0].fps_start_point.GetTransform().GetWorld()
            cls.camera_fps.GetTransform().SetWorld(fps_start_matrix)

        cls.views_carousel = ["fps"]
        for i in range(len(cls.players_allies)):
            cls.views_carousel.append("Aircraft_ally_" + str(i + 1))
        for i in range(len(cls.missile_launchers_allies)):
            cls.views_carousel.append("MissileLauncher_ally_" + str(i + 1))
        if flag_include_enemies:
            for i in range(len(cls.players_ennemies)):
                cls.views_carousel.append("Aircraft_enemy_" + str(i + 1))
            for i in range(len(cls.missile_launchers_ennemies)):
                cls.views_carousel.append("MissileLauncher_enemy_" + str(i + 1))
        cls.views_carousel_ptr = 1

    @classmethod
    def get_player_from_caroursel_id(cls, view_id=""):
        if view_id == "":
            view_id = cls.views_carousel[cls.views_carousel_ptr]
        if view_id == "fps":
            return None

        spl = view_id.split("_")
        machine_type, nation, num = spl[0], spl[1], spl[2]
        m_id = int(num) - 1

        if machine_type == "Aircraft":
            if nation == "ally":
                return cls.players_allies[m_id]
            elif nation == "enemy":
                return cls.players_ennemies[m_id]
            else:
                return None
        if machine_type == "MissileLauncher":
            if nation == "ally":
                return cls.missile_launchers_allies[m_id]
            elif nation == "enemy":
                return cls.missile_launchers_ennemies[m_id]
            else:
                return None

    @classmethod
    def set_view_carousel(cls, view_id):
        if view_id == "fps":
            cls.views_carousel_ptr = 0
            cls.update_main_view_from_carousel()
        else:
            for i in range(len(cls.views_carousel)):
                if cls.views_carousel[i] == view_id:
                    cls.views_carousel_ptr = i
                    cls.update_main_view_from_carousel()

    @classmethod
    def update_main_view_from_carousel(cls):
        view_id = cls.views_carousel[cls.views_carousel_ptr]
        if view_id == "fps":
            cls.smart_camera.setup(SmartCamera.TYPE_FPS, cls.camera_fps)
            cls.scene.SetCurrentCamera(cls.camera_fps)
        else:
            player = cls.get_player_from_caroursel_id(view_id)
            cls.smart_camera.set_camera_tracking_target_distance(player.camera_track_distance)
            cls.smart_camera.set_camera_follow_distance(player.camera_follow_distance)
            cls.smart_camera.set_tactical_camera_distance(player.camera_tactical_distance)
            cls.smart_camera.set_tactical_min_altitude(player.camera_tactical_min_altitude)
            if cls.player_view_mode == SmartCamera.TYPE_TACTICAL:
                camera = cls.camera
                td = player.get_device("TargettingDevice")
                target = td.get_target()
                if target is not None:
                    target = target.get_parent_node()
                cls.smart_camera.setup_tactical(camera, player.get_parent_node(), target, None)

            else:
                if cls.player_view_mode == SmartCamera.TYPE_FIX:
                    target_node = player.get_current_pilot_head()
                    camera = cls.camera_cokpit
                else:
                    target_node = player.get_parent_node()
                    camera = cls.camera
                cls.smart_camera.setup(cls.player_view_mode, camera, target_node)

            cls.scene.SetCurrentCamera(camera)

    @classmethod
    def set_track_view(cls, view_name):
        if cls.satellite_view:
            cls.satellite_view = False
            cls.update_main_view_from_carousel()
        cls.smart_camera.set_track_view(view_name)
        

    @classmethod
    def activate_cockpit_view(cls):
        if not cls.flag_cockpit_view:
            if cls.user_aircraft is not None:
                if cls.user_aircraft.get_current_pilot_head() is not None:
                    cls.flag_cockpit_view = True
                    cls.player_view_mode = SmartCamera.TYPE_FIX

    @classmethod
    def deactivate_cockpit_view(cls):
        if cls.flag_cockpit_view:
            cls.player_view_mode = SmartCamera.TYPE_TRACKING
            cls.set_track_view("back")
            cls.flag_cockpit_view = False


    @classmethod
    def switch_cockpit_view(cls, new_user_aircraft: Aircraft):
        if cls.flag_cockpit_view:
            if new_user_aircraft.get_current_pilot_head() is None:
                cls.deactivate_cockpit_view()


    @classmethod
    def control_views(cls, keyboard):
        quit_sv = False
        if keyboard.Down(hg.K_Numpad2):
            cls.deactivate_cockpit_view()
            quit_sv = True
            cls.player_view_mode = SmartCamera.TYPE_TRACKING
            cls.update_main_view_from_carousel()
            cls.set_track_view("back")
        elif keyboard.Down(hg.K_Numpad8):
            cls.deactivate_cockpit_view()
            quit_sv = True
            cls.player_view_mode = SmartCamera.TYPE_TRACKING
            cls.update_main_view_from_carousel()
            cls.set_track_view("front")
        elif keyboard.Down(hg.K_Numpad4):
            cls.deactivate_cockpit_view()
            quit_sv = True
            cls.player_view_mode = SmartCamera.TYPE_TRACKING
            cls.update_main_view_from_carousel()
            cls.set_track_view("left")
        elif keyboard.Down(hg.K_Numpad6):
            cls.deactivate_cockpit_view()
            quit_sv = True
            cls.player_view_mode = SmartCamera.TYPE_TRACKING
            cls.update_main_view_from_carousel()
            cls.set_track_view("right")

        elif keyboard.Pressed(hg.K_Numpad5):
            tgt = cls.get_player_from_caroursel_id()
            if tgt is not None:
                cls.deactivate_cockpit_view()
                tgt = tgt.get_parent_node()
                if not cls.satellite_view:
                    cls.satellite_view = True
                    cls.smart_camera.setup(SmartCamera.TYPE_SATELLITE, cls.satellite_camera, tgt)
                    cls.scene.SetCurrentCamera(cls.satellite_camera)

        elif keyboard.Pressed(hg.K_Numpad1):
            if not cls.flag_network_mode:
                if cls.user_aircraft is not None:
                    uctrl = cls.user_aircraft.get_device("UserControlDevice")
                    if uctrl is not None:
                        uctrl.deactivate()
                    #ia = cls.user_aircraft.get_device("IAControlDevice")
                    #if ia is not None:
                    #    ia.activate()
            cls.views_carousel_ptr += 1
            if cls.views_carousel_ptr >= len(cls.views_carousel):
                cls.views_carousel_ptr = 0
            if cls.views_carousel[cls.views_carousel_ptr] != "fps":
                new_user_aircraft = cls.get_player_from_caroursel_id(cls.views_carousel[cls.views_carousel_ptr])
                cls.switch_cockpit_view(new_user_aircraft)
                cls.user_aircraft = new_user_aircraft
                cls.user_aircraft.set_focus()
                ia = cls.user_aircraft.get_device("IAControlDevice")
                if ia is None:
                    uctrl = cls.user_aircraft.get_device("UserControlDevice")
                    if uctrl is not None:
                        uctrl.activate()
                elif not ia.is_activated():
                    apctrl = cls.user_aircraft.get_device("AutopilotControlDevice")
                    if apctrl is not None:
                        apctrl.deactivate()
                    uctrl = cls.user_aircraft.get_device("UserControlDevice")
                    if uctrl is not None:
                        uctrl.activate()
                    else:
                        ia.activate()
                # cls.user_aircraft.deactivate_IA()
            else:
                cls.deactivate_cockpit_view()
                cls.satellite_view = False
                cls.user_aircraft = None
            cls.update_main_view_from_carousel()

        elif keyboard.Pressed(hg.K_Numpad3):
            quit_sv = True
            cls.activate_cockpit_view()
            cls.update_main_view_from_carousel()

        elif keyboard.Pressed(hg.K_Numpad9):
            cls.deactivate_cockpit_view()
            quit_sv = True
            cls.player_view_mode = SmartCamera.TYPE_FOLLOW
            cls.update_main_view_from_carousel()

        elif keyboard.Pressed(hg.K_Numpad7):
            cls.deactivate_cockpit_view()
            quit_sv = True
            cls.player_view_mode = SmartCamera.TYPE_TACTICAL
            cls.update_main_view_from_carousel()

        if quit_sv and cls.satellite_view:
            cls.satellite_view = False
            if cls.player_view_mode == SmartCamera.TYPE_FOLLOW:
                camera = cls.camera
            elif cls.player_view_mode == SmartCamera.TYPE_TRACKING:
                camera = cls.camera
            elif cls.player_view_mode == SmartCamera.TYPE_FIX:
                camera = cls.camera_cokpit
            elif cls.player_view_mode == SmartCamera.TYPE_TACTICAL:
                camera = cls.camera
            cls.scene.SetCurrentCamera(camera)

        if cls.satellite_view:
            if keyboard.Down(hg.K_Insert):
                cls.smart_camera.increment_satellite_view_size()
            elif keyboard.Down(hg.K_PageUp):
                cls.smart_camera.decrement_satellite_view_size()
        else:
            if keyboard.Down(hg.K_Insert):
                cls.scene.GetCurrentCamera().GetCamera().SetFov(cls.scene.GetCurrentCamera().GetCamera().GetFov() * 0.99)
            elif keyboard.Down(hg.K_PageUp):
                cls.scene.GetCurrentCamera().GetCamera().SetFov(cls.scene.GetCurrentCamera().GetCamera().GetFov() * 1.01)


    # =============================== Scene datas
    @classmethod
    def get_current_camera(cls):
        return cls.scene.GetCurrentCamera()

    # =============================== Displays =============================================

    @classmethod
    def display_landing_trajectory(cls, landing_target: LandingTarget):
        if landing_target is not None:
            num_steps = 100
            c = hg.Color(0, 1, 0, 1)
            p0 = landing_target.get_position(0)
            step = landing_target.horizontal_amplitude / num_steps * 2
            for i in range(1, num_steps):
                p1 = landing_target.get_position(step * i)
                Overlays.add_line(p0, p1, c, c)
                p0 = p1

    @classmethod
    def display_landing_projection(cls, aircraft: Aircraft):
        ia_ctrl = aircraft.get_device("IAControlDevice")
        if ia_ctrl is not None and ia_ctrl.IA_landing_target is not None:
            c = hg.Color(1, 0, 0, 1)
            c2 = hg.Color(0, 1, 0, 1)
            p = ia_ctrl.calculate_landing_projection(aircraft, ia_ctrl.IA_landing_target)
            target_point = ia_ctrl.calculate_landing_target_point(aircraft, ia_ctrl.IA_landing_target, p)
            if p is not None:
                v = ia_ctrl.IA_landing_target.get_landing_vector()
                vb = hg.Vec3(v.y, 0, -v.x)
                Overlays.add_line(p - vb * 50, p + vb * 50, c, c)
                Overlays.add_line(target_point, aircraft.parent_node.GetTransform().GetPos(), c2, c)

    @classmethod
    def display_machine_vectors(cls, machine: Destroyable_Machine):
        pos = machine.get_position()
        if machine.flag_display_linear_speed:
            Physics.display_vector(pos, machine.get_move_vector(), "linear speed", hg.Vec2(0, 0.03), hg.Color.Yellow)
        hs, vs = machine.get_world_speed()
        if machine.flag_display_vertical_speed:
            Physics.display_vector(pos, hg.Vec3.Up * vs, "Vertical speed", hg.Vec2(0, 0.02), hg.Color.Red)
        if machine.flag_display_horizontal_speed:
            az = machine.get_Z_axis()
            ah = hg.Normalize(hg.Vec3(az.x, 0, az.z))
            Physics.display_vector(pos, ah * hs, "Horizontal speed",hg.Vec2(0, 0.01), hg.Color.Green)

    # =============================== 2D HUD =============================================

    @classmethod
    def get_2d_hud(cls, point3d: hg.Vec3):
        if cls.flag_vr:
            cam = cls.scene.GetCurrentCamera()
            fov = atan(cls.vr_hud.y / (2 * cls.vr_hud.z)) * 2
            main_camera_matrix = cam.GetTransform().GetWorld()
            vs = hg.ComputePerspectiveViewState(main_camera_matrix, fov, cam.GetCamera().GetZNear(), cam.GetCamera().GetZFar(), hg.Vec2(cls.vr_hud.x / cls.vr_hud.y, 1))
            pos_view = vs.view * point3d
        else:
            vs = cls.scene.ComputeCurrentCameraViewState(hg.Vec2(cls.resolution.x / cls.resolution.y, 1))
            pos_view = vs.view * point3d
        f, pos2d = hg.ProjectToScreenSpace(vs.proj, pos_view, cls.resolution)
        if f:
            return hg.Vec2(pos2d.x, pos2d.y)
        else:
            return None

    # =============================== GUI =============================================
    @classmethod
    def update_missiles_smoke_color(cls):
        for missile_t in cls.missiles_allies:
            for missile in missile_t:
                missile.set_smoke_color(cls.allies_missiles_smoke_color)
        for missile_t in cls.missiles_ennemies:
            for missile in missile_t:
                missile.set_smoke_color(cls.ennemies_missiles_smoke_color)
    
    @classmethod
    def gui(cls):
        aircrafts = cls.players_allies + cls.players_ennemies

        if hg.ImGuiBegin("Main Settings"):

            hg.ImGuiSetWindowPos("Main Settings",hg.Vec2(10, 60), hg.ImGuiCond_Once)
            hg.ImGuiSetWindowSize("Main Settings",hg.Vec2(650,625), hg.ImGuiCond_Once)

            if hg.ImGuiButton("Load simulator parameters"):
                cls.load_json_script()
                cls.update_missiles_smoke_color()
            hg.ImGuiSameLine()
            if hg.ImGuiButton("Save simulator parameters"):
                cls.save_json_script()

            hg.ImGuiText("Num nodes: %d" % cls.scene.GetNodeCount())

            d, f = hg.ImGuiCheckbox("Display FPS", cls.flag_display_fps)
            if d: cls.flag_display_fps = f
            d, f = hg.ImGuiCheckbox("Display HUD", cls.flag_display_HUD)
            if d: cls.flag_display_HUD = f

            d, f = hg.ImGuiCheckbox("Renderless", cls.flag_renderless)
            if d: cls.set_renderless_mode(f)
            d, f = hg.ImGuiCheckbox("Display radar in renderless mode", cls.flag_display_radar_in_renderless)
            if d: cls.flag_display_radar_in_renderless = f
            d, f = hg.ImGuiCheckbox("Control views", cls.flag_control_views)
            if d: cls.flag_control_views = f
            d, f = hg.ImGuiCheckbox("Particles", Destroyable_Machine.flag_activate_particles)
            if d: Destroyable_Machine.set_activate_particles(f)
            d, f = hg.ImGuiCheckbox("SFX", cls.flag_sfx)
            if d: cls.set_activate_sfx(f)

            d, f = hg.ImGuiCheckbox("Display landing trajectories", cls.flag_display_landing_trajectories)
            if d: cls.flag_display_landing_trajectories = f

            d, f = hg.ImGuiCheckbox("Display machines bounds", cls.flag_display_machines_bounding_boxes)
            if d: cls.flag_display_machines_bounding_boxes = f

            d, f = hg.ImGuiCheckbox("Display physics debug", cls.flag_display_physics_debug)
            if d: cls.flag_display_physics_debug = f

            f, c = hg.ImGuiColorEdit("Allies missiles smoke color", cls.allies_missiles_smoke_color)
            if f:
                cls.allies_missiles_smoke_color = c
                cls.update_missiles_smoke_color()
            f, c = hg.ImGuiColorEdit("Ennmies missiles smoke color", cls.ennemies_missiles_smoke_color)
            if f:
                cls.ennemies_missiles_smoke_color = c
                cls.update_missiles_smoke_color()

            # Aircrafts:
            d, f = hg.ImGuiCheckbox("Display selected aircraft", cls.flag_display_selected_aircraft)
            if d: cls.flag_display_selected_aircraft = f

            if len(aircrafts) > 0:
                aircrafts_list = hg.StringList()

                for aircraft in aircrafts:
                    nm = aircraft.name
                    if aircraft == cls.user_aircraft:
                        nm += " - USER -"
                    aircrafts_list.push_back(nm)

                f, d = hg.ImGuiListBox("Aircrafts", cls.selected_aircraft_id, aircrafts_list,20)
                if f:
                    cls.selected_aircraft_id = d

        hg.ImGuiEnd()

        if len(aircrafts) > 0: 
            cls.selected_machine = aircrafts[cls.selected_aircraft_id]
            cls.selected_machine.gui()
        else:
            cls.selected_machine = None


    @classmethod
    def load_json_script(cls, file_name="scripts/simulator_parameters.json"):
        file = open(file_name, "r")
        
        #file = hg.OpenText(file_name)
        if not file:
            print("ERROR - Can't open json file : " + file_name)
        else:
            json_script = file.read()
            file.close()
            #json_script = hg.ReadString(file)
            #hg.Close(file)
            if json_script != "":
                script_parameters = json.loads(json_script)
                cls.allies_missiles_smoke_color = dc.list_to_color(script_parameters["allies_missiles_smoke_color"])
                cls.ennemies_missiles_smoke_color = dc.list_to_color(script_parameters["ennemies_missiles_smoke_color"])

    @classmethod
    def save_json_script(cls, output_filename="scripts/simulator_parameters.json"):
        script_parameters = {"allies_missiles_smoke_color": dc.color_to_list(cls.allies_missiles_smoke_color),
                             "ennemies_missiles_smoke_color": dc.color_to_list(cls.ennemies_missiles_smoke_color),
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

    # ================================ Scene update and rendering modes ============================================

    @classmethod
    def update_kinetics(cls, dts):
        #for dm in Destroyable_Machine.update_list:
        #    dm.update_collision_nodes_matrices()

        for dm in Destroyable_Machine.update_list:
            dm.update_kinetics(dts)
            cls.display_machine_vectors(dm)


    @classmethod
    def clear_display_lists(cls):
        cls.sprites_display_list = []
        #cls.texts_display_list = []
        Overlays.texts2D_display_list = []
        Overlays.texts3D_display_list = []
        Overlays.primitives3D_display_list = []
        Overlays.lines = []

    @classmethod
    def render_frame_vr(cls):

        vid = 0
        views = hg.SceneForwardPipelinePassViewId()

        camera = cls.scene.GetCurrentCamera()
        main_camera_matrix = camera.GetTransform().GetWorld()
        body_mtx = main_camera_matrix * hg.InverseFast(cls.initial_head_matrix)

        cls.vr_state = hg.OpenVRGetState(body_mtx, camera.GetCamera().GetZNear(), camera.GetCamera().GetZFar())
        vs_left, vs_right = hg.OpenVRStateToViewState(cls.vr_state)

        vr_eye_rect = hg.IntRect(0, 0, int(cls.vr_state.width), int(cls.vr_state.height))

        # ========== Display Reflect scene ===================

        # Deactivated because assymetric VR FOV not resolved.
        """
        cls.scene.canvas.color = hg.Color(1, 0, 0, 1)  # En attendant de fixer le pb de la depth texture du framebuffer.

        cls.scene.canvas.clear_z = True
        cls.scene.canvas.clear_color = True
        left_reflect, right_reflect = cls.water_reflexion.compute_vr_reflect(camera, cls.vr_state, vs_left, vs_right)

        vid, passId = hg.PrepareSceneForwardPipelineCommonRenderData(vid, cls.scene, cls.render_data, cls.pipeline, cls.pl_resources, views)

        # Prepare the left eye render data then draw to its framebuffer
        vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, left_reflect, cls.scene, cls.render_data, cls.pipeline, cls.pl_resources, views)
        vid, passId = hg.SubmitSceneToForwardPipeline(vid, cls.scene, vr_eye_rect, left_reflect, cls.pipeline, cls.render_data, cls.pl_resources, cls.water_reflexion.quad_frameBuffer_left.handle)

        # Prepare the right eye render data then draw to its framebuffer
        vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, right_reflect, cls.scene, cls.render_data, cls.pipeline, cls.pl_resources, views)
        vid, passId = hg.SubmitSceneToForwardPipeline(vid, cls.scene, vr_eye_rect, right_reflect, cls.pipeline, cls.render_data, cls.pl_resources, cls.water_reflexion.quad_frameBuffer_right.handle)
        """
    
        # ========== Display raymarch scene ===================
        output_fb_left = cls.vr_left_fb #cls.post_process.quad_frameBuffer_left
        output_fb_right = cls.vr_right_fb #cls.post_process.quad_frameBuffer_right
        cls.scene.canvas.clear_z = True
        cls.scene.canvas.clear_color = True

        #tex_reflect_left_color = hg.GetColorTexture(cls.water_reflexion.quad_frameBuffer_left)
        #tex_reflect_left_depth = hg.GetDepthTexture(cls.water_reflexion.quad_frameBuffer_left)
        #tex_reflect_right_color = hg.GetColorTexture(cls.water_reflexion.quad_frameBuffer_right)
        #tex_reflect_right_depth = hg.GetDepthTexture(cls.water_reflexion.quad_frameBuffer_right)
        vid = cls.sea_render.render_vr(vid, cls.vr_state, vs_left, vs_right, output_fb_left, output_fb_right) #, tex_reflect_left_color, tex_reflect_left_depth, tex_reflect_right_color, tex_reflect_right_depth)


        # ========== Display models scene =======================
        cls.scene.canvas.clear_z = False
        cls.scene.canvas.clear_color = False
        vid, passId = hg.PrepareSceneForwardPipelineCommonRenderData(vid, cls.scene, cls.render_data, cls.pipeline, cls.pl_resources, views)

        # Prepare the left eye render data then draw to its framebuffer
        vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs_left, cls.scene, cls.render_data, cls.pipeline, cls.pl_resources, views)
        vid, passId = hg.SubmitSceneToForwardPipeline(vid, cls.scene, vr_eye_rect, vs_left, cls.pipeline, cls.render_data, cls.pl_resources, output_fb_left.GetHandle())

        # Prepare the right eye render data then draw to its framebuffer
        vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs_right, cls.scene, cls.render_data, cls.pipeline, cls.pl_resources, views)
        vid, passId = hg.SubmitSceneToForwardPipeline(vid, cls.scene, vr_eye_rect, vs_right, cls.pipeline, cls.render_data, cls.pl_resources, output_fb_right.GetHandle())

        # ==================== Display 3D Overlays ===========

        #Overlays.add_text3D("HELLO WORLD", hg.Vec3(0, 50, 200), 1, hg.Color.Red)

        if len(Overlays.texts3D_display_list) > 0 or len(Overlays.lines) > 0:

            #hg.SetViewFrameBuffer(vid, cls.post_process.quad_frameBuffer_left.handle)
            hg.SetViewFrameBuffer(vid, output_fb_left.GetHandle())
            hg.SetViewRect(vid, 0, 0, int(cls.vr_state.width), int(cls.vr_state.height))
            hg.SetViewClear(vid, hg.CF_Depth, 0, 1.0, 0)
            hg.SetViewTransform(vid, vs_left.view, vs_left.proj)
            eye_left = cls.vr_state.head * cls.vr_state.left.offset
            Overlays.display_primitives3D(vid, eye_left)
            Overlays.display_texts3D(vid, eye_left)
            Overlays.draw_lines(vid)
            vid += 1

            #hg.SetViewFrameBuffer(vid, cls.post_process.quad_frameBuffer_right.handle)
            hg.SetViewFrameBuffer(vid, output_fb_right.GetHandle())
            hg.SetViewRect(vid, 0, 0, int(cls.vr_state.width), int(cls.vr_state.height))
            hg.SetViewClear(vid, hg.CF_Depth, 0, 1.0, 0)
            hg.SetViewTransform(vid, cls.vr_viewstate.vs_right.view, cls.vr_viewstate.vs_right.proj)
            eye_right = cls.vr_state.head * cls.vr_state.right.offset
            Overlays.display_primitives3D(vid, eye_right)
            Overlays.display_texts3D(vid, eye_right)
            Overlays.draw_lines(vid)
            vid += 1


        # ==================== Display 2D sprites ===========

        cam_mat = cls.scene.GetCurrentCamera().GetTransform().GetWorld()
        mat_spr = cam_mat  # * vr_state.initial_head_offset

        #hg.SetViewFrameBuffer(vid, cls.post_process.quad_frameBuffer_left.handle)
        hg.SetViewFrameBuffer(vid, output_fb_left.GetHandle())
        hg.SetViewRect(vid, 0, 0, int(cls.vr_state.width), int(cls.vr_state.height))
        hg.SetViewClear(vid, hg.CF_Depth, 0, 1.0, 0)
        hg.SetViewTransform(vid, vs_left.view, vs_left.proj)

        """
        for txt in cls.texts_display_list:
            if "h_align" in txt:
                cls.display_text_vr(vid, mat_spr, cls.resolution, txt["text"], txt["pos"], txt["size"], txt["font"], txt["color"], txt["h_align"])
            else:
                cls.display_text_vr(vid, mat_spr, cls.resolution, txt["text"], txt["pos"], txt["size"], txt["font"], txt["color"])
        """

        z_near, z_far = hg.ExtractZRangeFromProjectionMatrix(vs_left.proj)

        Overlays.display_texts2D_vr(vid, cls.initial_head_matrix, z_near, z_far, cls.resolution, mat_spr, cls.vr_hud)

        for spr in cls.sprites_display_list:
            spr.draw_vr(vid, mat_spr, cls.resolution, cls.vr_hud)
        vid += 1

        #hg.SetViewFrameBuffer(vid, cls.post_process.quad_frameBuffer_right.handle)
        hg.SetViewFrameBuffer(vid, output_fb_right.GetHandle())
        hg.SetViewRect(vid, 0, 0, int(cls.vr_state.width), int(cls.vr_state.height))
        hg.SetViewClear(vid, hg.CF_Depth, 0, 1.0, 0)
        hg.SetViewTransform(vid, vs_right.view, vs_right.proj)

        """
        for txt in cls.texts_display_list:
            if "h_align" in txt:
                cls.display_text_vr(vid, mat_spr, cls.resolution, txt["text"], txt["pos"], txt["size"], txt["font"], txt["color"], txt["h_align"])
            else:
                cls.display_text_vr(vid, mat_spr, cls.resolution, txt["text"], txt["pos"], txt["size"], txt["font"], txt["color"])
        """
        z_near, z_far = hg.ExtractZRangeFromProjectionMatrix(vs_right.proj)
        Overlays.display_texts2D_vr(vid, cls.initial_head_matrix, z_near, z_far, cls.resolution, mat_spr, cls.vr_hud)

        for spr in cls.sprites_display_list:
            spr.draw_vr(vid, mat_spr, cls.resolution, cls.vr_hud)
        vid += 1

        # ============= Post-process

        #vid = cls.post_process.display_vr(vid, cls.vr_state, vs_left, vs_right, cls.vr_left_fb, cls.vr_right_fb, cls.pl_resources)

        # ============= Display the VR eyes texture to the backbuffer =============
        hg.SetViewRect(vid, 0, 0, int(cls.resolution.x), int(cls.resolution.y))
        hg.SetViewClear(vid, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
        vs = hg.ComputeOrthographicViewState(hg.TranslationMat4(hg.Vec3(0, 0, 0)), cls.resolution.y, 0.1, 100, hg.ComputeAspectRatioX(cls.resolution.x, cls.resolution.y))
        hg.SetViewTransform(vid, vs.view, vs.proj)

        cls.vr_quad_uniform_set_texture_list.clear()
        #cls.vr_quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.OpenVRGetColorTexture(cls.vr_left_fb), 0))
        cls.vr_quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.GetColorTexture(cls.post_process.quad_frameBuffer_left), 0))
        hg.SetT(cls.vr_quad_matrix, hg.Vec3(cls.eye_t_x, 0, 1))
        hg.DrawModel(vid, cls.vr_quad_model, cls.vr_tex0_program, cls.vr_quad_uniform_set_value_list, cls.vr_quad_uniform_set_texture_list, cls.vr_quad_matrix, cls.vr_quad_render_state)

        cls.vr_quad_uniform_set_texture_list.clear()
        #cls.vr_quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.OpenVRGetColorTexture(cls.vr_right_fb), 0))
        cls.vr_quad_uniform_set_texture_list.push_back(hg.MakeUniformSetTexture("s_tex", hg.GetColorTexture(cls.post_process.quad_frameBuffer_right), 0))
        hg.SetT(cls.vr_quad_matrix, hg.Vec3(-cls.eye_t_x, 0, 1))
        hg.DrawModel(vid, cls.vr_quad_model, cls.vr_tex0_program, cls.vr_quad_uniform_set_value_list, cls.vr_quad_uniform_set_texture_list, cls.vr_quad_matrix, cls.vr_quad_render_state)


    @classmethod
    def render_frame(cls):
        vid = 0
        views = hg.SceneForwardPipelinePassViewId()
        res_x = int(cls.resolution.x)
        res_y = int(cls.resolution.y)
        # ========== Display Reflect scene ===================
        cls.water_reflexion.set_camera(cls.scene)

        #cls.scene.canvas.color = cls.sea_render.high_atmosphere_color
        cls.scene.canvas.color = hg.Color(1, 0, 0, 1) # En attendant de fixer le pb de la depth texture du framebuffer.

        cls.scene.canvas.clear_z = True
        cls.scene.canvas.clear_color = True
        # hg.SetViewClear(vid, 0, 0x0, 1.0, 0)

        vs = cls.scene.ComputeCurrentCameraViewState(hg.ComputeAspectRatioX(res_x, res_y))
        vid, passId = hg.PrepareSceneForwardPipelineCommonRenderData(vid, cls.scene, cls.render_data, cls.pipeline, cls.pl_resources, views)
        vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs, cls.scene, cls.render_data, cls.pipeline, cls.pl_resources, views)

        # Get quad_frameBuffer.handle to define output frameBuffer
        vid, passId = hg.SubmitSceneToForwardPipeline(vid, cls.scene, hg.IntRect(0, 0, res_x, res_y), vs, cls.pipeline, cls.render_data, cls.pl_resources, cls.water_reflexion.quad_frameBuffer.handle)

        cls.water_reflexion.restore_camera(cls.scene)

        # ========== Display raymarch scene ===================

        cls.scene.canvas.clear_z = True
        cls.scene.canvas.clear_color = True
        c = cls.scene.GetCurrentCamera()
        vid = cls.sea_render.render(vid, c, hg.Vec2(res_x, res_y), hg.GetColorTexture(cls.water_reflexion.quad_frameBuffer), hg.GetDepthTexture(cls.water_reflexion.quad_frameBuffer), cls.post_process.quad_frameBuffer)

        # ========== Display models scene ===================

        cls.scene.canvas.clear_z = False
        cls.scene.canvas.clear_color = False
        # hg.SetViewClear(vid, hg.ClearColor | hg.ClearDepth, 0x0, 1.0, 0)

        vs = cls.scene.ComputeCurrentCameraViewState(hg.ComputeAspectRatioX(res_x, res_y))
        vid, passId = hg.PrepareSceneForwardPipelineCommonRenderData(vid, cls.scene, cls.render_data, cls.pipeline, cls.pl_resources, views)
        vid, passId = hg.PrepareSceneForwardPipelineViewDependentRenderData(vid, vs, cls.scene, cls.render_data, cls.pipeline, cls.pl_resources, views)

        # Get quad_frameBuffer.handle to define output frameBuffer
        vid, passId = hg.SubmitSceneToForwardPipeline(vid, cls.scene, hg.IntRect(0, 0, res_x, res_y), vs, cls.pipeline, cls.render_data, cls.pl_resources, cls.post_process.quad_frameBuffer.handle)

        # ==================== Display 3D Overlays ===========
        hg.SetViewFrameBuffer(vid, cls.post_process.quad_frameBuffer.handle)
        hg.SetViewRect(vid, 0, 0, res_x, res_y)
        cam = cls.scene.GetCurrentCamera()
        hg.SetViewClear(vid, hg.CF_Depth, 0, 1.0, 0)
        cam_mat = cam.GetTransform().GetWorld()
        view_matrix = hg.InverseFast(cam_mat)
        c = cam.GetCamera()
        projection_matrix = hg.ComputePerspectiveProjectionMatrix(c.GetZNear(), c.GetZFar(), hg.FovToZoomFactor(c.GetFov()), hg.Vec2(res_x / res_y, 1))
        hg.SetViewTransform(vid, view_matrix, projection_matrix)

        #Overlays.add_text3D("HELLO WORLD", hg.Vec3(0, 50, 200), 1, hg.Color.Red)

        Overlays.display_primitives3D(vid, cls.scene.GetCurrentCamera().GetTransform().GetWorld())
        Overlays.display_texts3D(vid, cls.scene.GetCurrentCamera().GetTransform().GetWorld())
        Overlays.draw_lines(vid)
        if cls.flag_display_physics_debug:
            Overlays.display_physics_debug(vid, cls.scene_physics)

        vid += 1
        # ==================== Display 2D sprites ===========

        hg.SetViewFrameBuffer(vid, cls.post_process.quad_frameBuffer.handle)
        hg.SetViewRect(vid, 0, 0, res_x, res_y)

        Sprite.setup_matrix_sprites2D(vid, cls.resolution)

        for spr in cls.sprites_display_list:
            spr.draw(vid)

        vid += 1

        # ==================== Display 2D texts ===========

        hg.SetViewFrameBuffer(vid, cls.post_process.quad_frameBuffer.handle)
        hg.SetViewRect(vid, 0, 0, res_x, res_y)

        Sprite.setup_matrix_sprites2D(vid, cls.resolution)

        """
        for txt in cls.texts_display_list:
            if "h_align" in txt:
                cls.display_text(vid, txt["text"], txt["pos"], txt["size"], txt["font"], txt["color"], txt["h_align"])
            else:
                cls.display_text(vid, txt["text"], txt["pos"], txt["size"], txt["font"], txt["color"])
        """

        #Overlays.add_text2D_from_3D_position("HELLO World !", hg.Vec3(0, 50, 200), hg.Vec2(-0.1, 0), 0.02, hg.Color.Red)
        Overlays.display_texts2D(vid, cls.scene.GetCurrentCamera(), cls.resolution)


        vid += 1
        # ========== Post process:
        cls.scene.canvas.clear_z = True
        cls.scene.canvas.clear_color = True
        cls.post_process.display(vid, cls.pl_resources, cls.resolution)
        cls.max_view_id = vid


    @classmethod
    def update_renderless(cls, dt):
        vid = 0
        res_x = int(cls.resolution.x)
        res_y = int(cls.resolution.y)
        cls.frame_time += dt
        if hg.time_to_sec_f(cls.frame_time) >= 1 / 60:
            hg.SetViewRect(0, 0, 0, res_x, res_y)
            hg.SetViewClear(0, hg.CF_Color | hg.CF_Depth, 0x0, 1.0, 0)
            Sprite.setup_matrix_sprites2D(vid, cls.resolution)
            for spr in cls.sprites_display_list:
                spr.draw(vid)
            #cls.texts_display_list.append({"text": "RENDERLESS MODE", "font": cls.hud_font, "pos": hg.Vec2(0.5, 0.5), "size": 0.018, "color": hg.Color.Red})
            Overlays.add_text2D("RENDERLESS MODE", hg.Vec2(0.5, 0.5), 0.018, hg.Color.Red, cls.hud_font)
            """
            for txt in cls.texts_display_list:
                if "h_align" in txt:
                    cls.display_text(vid, txt["text"], txt["pos"], txt["size"], txt["font"], txt["color"], txt["h_align"])
                else:
                    cls.display_text(vid, txt["text"], txt["pos"], txt["size"], txt["font"], txt["color"])
            """
            Overlays.display_texts2D(vid, cls.scene.GetCurrentCamera(), cls.resolution)

            if cls.flag_gui:
                hg.ImGuiEndFrame(255)
            hg.Frame()
            hg.UpdateWindow(cls.win)
            cls.frame_time = 0

    @classmethod
    def update_inputs(cls):
        
        cls.keyboard.Update()
        cls.mouse.Update()

        if cls.flag_running:
            ControlDevice.update_input_devices()

    @classmethod
    def reset_timestamp(cls):
        cls.framecount = 0
        cls.timer = 0
        MachineDevice.framecount = 0
        Collisions_Object.framecount = 0

    @classmethod
    def update_timestamp(cls, dts):
        cls.framecount += 1
        cls.timer += dts
        MachineDevice.framecount = cls.framecount
        MachineDevice.timer = cls.timer
        Collisions_Object.framecount = cls.framecount
        Collisions_Object.timer = cls.timer

    @classmethod
    def client_update(cls):
        cls.flag_client_ask_update_scene = True

    @classmethod
    def update(cls):
        if cls.flag_running:
            #cls.t = hg.time_to_sec_f(hg.GetClock())
            #cls.update_inputs()

            real_dt = hg.TickClock()
            forced_dt = hg.time_from_sec_f(cls.timestep)

            if cls.keyboard.Pressed(hg.K_Escape):
                cls.flag_exit = True

            if cls.flag_vr:
                if cls.vr_state is not None and cls.keyboard.Pressed(hg.K_F11):
                    cls.update_initial_head_matrix(cls.vr_state)

            if cls.keyboard.Pressed(hg.K_F12):
                cls.flag_gui = not cls.flag_gui

            if cls.keyboard.Pressed(hg.K_F10):
                cls.flag_display_HUD = not cls.flag_display_HUD
            
            if cls.keyboard.Pressed(hg.K_F9):
                cls.flag_display_recorder = not cls.flag_display_recorder

            if not cls.flag_renderless:
                if cls.flag_gui or cls.flag_display_recorder:
                    hg.ImGuiBeginFrame(int(cls.resolution.x), int(cls.resolution.y), real_dt, hg.ReadMouse(), hg.ReadKeyboard())
                    cls.smart_camera.update_hovering_ImGui()
                if cls.flag_gui:
                    cls.gui()
                    cls.sea_render.gui(cls.scene.GetCurrentCamera().GetTransform().GetPos())
                    ParticlesEngine.gui()
            else:
                if cls.flag_display_recorder:
                    hg.ImGuiBeginFrame(int(cls.resolution.x), int(cls.resolution.y), real_dt, hg.ReadMouse(), hg.ReadKeyboard())

            if cls.flag_display_fps:
                cls.update_num_fps(hg.time_to_sec_f(real_dt))
                #cls.texts_display_list.append({"text": "FPS %d" % (cls.num_fps), "font": cls.hud_font, "pos": hg.Vec2(0.001, 0.999), "size": 0.018, "color": hg.Color.Yellow})
                Overlays.add_text2D("FPS %d" % (cls.num_fps), hg.Vec2(0.001, 0.999), 0.018, hg.Color.Yellow, cls.hud_font)

            if cls.flag_display_recorder: # and cls.current_state.__name__ == "main_state":
                if not vcr.is_init():
                    vcr.init()
                else:
                    vcr.update_gui(cls,cls.keyboard)
                    
            # =========== State update:
            if cls.flag_renderless:
                used_dt = forced_dt
                Main.simulation_dt = used_dt
            else:
                used_dt = min(forced_dt * 2, real_dt)
                Main.simulation_dt = used_dt
            
            # Simulation_dt is timestep for dogfight kinetics:

            cls.current_state = cls.current_state(hg.time_to_sec_f(Main.simulation_dt)) # Minimum frame rate security
            
            
            # Used_dt is timestep used for Harfang 3D:
            hg.SceneUpdateSystems(cls.scene, cls.clocks, used_dt, cls.scene_physics, used_dt, 1000)  # ,10,1000)

            # =========== Render scene visuals:
            
            # Renderless
            if cls.flag_renderless:
                if cls.flag_display_recorder:
                    hg.ImGuiEndFrame(255)
                cls.update_renderless(forced_dt)
            
            # Render
            else:

                if cls.flag_vr:
                    cls.render_frame_vr()
                else:
                    cls.render_frame()

                if cls.flag_gui or cls.flag_display_recorder:
                    hg.ImGuiEndFrame(255)
                hg.Frame()
                if cls.flag_vr:
                    hg.OpenVRSubmitFrame(cls.vr_left_fb, cls.vr_right_fb)
                #hg.UpdateWindow(cls.win)
                
            cls.clear_display_lists()

        cls.flag_client_ask_update_scene = False

    @classmethod
    def update_window(cls):
        #if not cls.flag_renderless_mode:
        hg.UpdateWindow(cls.win)

    # ================================ Network ============================================

    @classmethod
    def get_network(cls):
        return netws.get_network()

