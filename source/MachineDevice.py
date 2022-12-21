# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
import json
from math import radians, degrees, pi, sqrt, exp, floor, acos, asin, sin, cos
from random import uniform
from Particles import *

# =====================================================================================================
#                                  Landing
# =====================================================================================================

class LandingTarget:
    def __init__(self, landing_node: hg.Node, horizontal_amplitude=6000, vertical_amplitude=500, smooth_level=5):
        self.landing_node = landing_node
        self.horizontal_amplitude = horizontal_amplitude
        self.vertical_amplitude = vertical_amplitude
        self.smooth_level = smooth_level
        self.extremum = self.calculate_extremum()

    def calculate_extremum(self):
        x = pi / 2
        for i in range(self.smooth_level):
            x = sin(x)
        return x * 2

    def get_position(self, distance):
        org = self.landing_node.GetTransform().GetWorld()
        o = hg.GetT(org)
        az = hg.GetZ(org) * -1
        ah = hg.Normalize(hg.Vec2(az.x, az.z)) * distance
        p = hg.Vec3(ah.x, 0, ah.y) + o
        x = distance / self.horizontal_amplitude
        if x >= 1:
            p.y += self.vertical_amplitude
        elif x > 0:
            x = x * pi - pi / 2
            for i in range(self.smooth_level):
                x = sin(x)
            p.y += (x / self.extremum + 0.5) * self.vertical_amplitude
        return p

    def get_landing_position(self):
        return hg.GetT(self.landing_node.GetTransform().GetWorld())

    def get_approach_entry_position(self):
        return self.get_position(self.horizontal_amplitude)

    def get_landing_vector(self):
        org = self.landing_node.GetTransform().GetWorld()
        az = hg.GetZ(org) * -1
        return hg.Normalize(hg.Vec2(az.x, az.z))

# ==============================================
#       MachineDevice
# ==============================================

class MachineDevice:

    framecount = 0 #Updated with Main.framecount
    timer = 0

    # Start state: activated or not.
    def __init__(self, name, machine, start_state=False):
        self.activated = start_state
        self.start_state = start_state
        self.machine = machine
        self.name = name
        self.wreck = False
        self.commands = {"RESET": self.reset, "ACTIVATE": self.activate, "DEACTIVATE": self.deactivate}

    def record_start_state(self, start_state=None):
        if start_state is None:
            self.start_state = self.activated
        else:
            self.start_state = start_state

    def reset(self):
        self.activated = self.start_state

    def update(self, dts):
        pass

    def activate(self):
        self.activated = True

    def deactivate(self):
        self.activated = False

    def is_activated(self):
        return self.activated


# ==============================================
#       Gear device
# ==============================================

class Gear(MachineDevice):

    def __init__(self, name, machine, scene=None, open_anim=None, retract_anim=None, start_state=True):
        MachineDevice.__init__(self, name, machine, start_state)
        self.flag_gear_moving = False
        self.gear_moving_delay = 3.55
        self.gear_moving_t = 0
        self.gear_level = 1
        self.gear_direction = 0
        self.gear_height = machine.gear_height

        self.scene = scene
        self.open_anim = open_anim
        self.retract_anim = retract_anim
        self.gear_anim_play = None

    def reset(self):
        MachineDevice.reset(self)
        self.flag_gear_moving = False
        if self.activated:
            self.gear_level = 1
        else:
            self.gear_level = 0

        # Animated gear:
        if self.scene is not None:
            if self.gear_anim_play is not None:
                self.scene.StopAnim(self.gear_anim_play)
                self.gear_anim_play = None
            if self.activated:
                # self.gear_moving_delay = Get anim time
                self.gear_anim_play = self.scene.PlayAnim(self.open_anim, hg.ALM_Once, hg.E_Linear, hg.time_from_sec_f(self.gear_moving_delay), hg.time_from_sec_f(self.gear_moving_delay), True, 1)
            else:
                # self.gear_moving_delay = Get anim time
                self.gear_anim_play = self.scene.PlayAnim(self.retract_anim, hg.ALM_Once, hg.E_Linear, hg.time_from_sec_f(self.gear_moving_delay), hg.time_from_sec_f(self.gear_moving_delay), True, 1)

    def activate(self):
        if not self.flag_gear_moving:
            self.start_moving_gear(1)
            self.activated = True

            if self.scene is not None:
                if self.gear_anim_play is not None: self.scene.StopAnim(self.gear_anim_play)
                # self.gear_moving_delay = Get anim time
                self.gear_anim_play = self.scene.PlayAnim(self.open_anim, hg.ALM_Once, hg.E_InOutSine, hg.time_from_sec_f(0), hg.time_from_sec_f(self.gear_moving_delay), False, 1)
                # self.gear_anim_play = self.scene.PlayAnim(self.parent_node.GetInstanceSceneAnim("gear_open"), hg.ALM_Once, hg.E_InOutSine, hg.time_from_sec_f(0), hg.time_from_sec_f(3.55), False, 1)

    def deactivate(self):
        if not self.flag_gear_moving:
            self.start_moving_gear(-1)
            self.activated = False

            if self.scene is not None:
                if self.gear_anim_play is not None: self.scene.StopAnim(self.gear_anim_play)
                # self.gear_moving_delay = Get anim time
                self.gear_anim_play = self.scene.PlayAnim(self.retract_anim, hg.ALM_Once, hg.E_InOutSine, hg.time_from_sec_f(0), hg.time_from_sec_f(self.gear_moving_delay), False, 1)

    def update(self, dts):
        if self.flag_gear_moving:
            lvl = self.gear_moving_t / self.gear_moving_delay
            if self.gear_direction < 0:
                lvl = 1 - lvl
            self.gear_level = max(0, min(1, lvl))
            if self.gear_moving_t < self.gear_moving_delay:
                self.gear_moving_t += dts
            else:
                self.flag_gear_moving = False

    def start_moving_gear(self, direction):  # Deploy: dir = 1, Retract: dir = -1
        self.gear_moving_t = 0
        self.gear_direction = direction
        if self.gear_direction < 0:
            self.gear_level = 1
        else:
            self.gear_level = 0
        self.flag_gear_moving = True

# ==============================================
#       Targetting device
#       Targets and hunter machine are Destroyable_Machine classes only
# ==============================================

class TargettingDevice(MachineDevice):

    def __init__(self, name, machine, start_state=True):
        MachineDevice.__init__(self, name, machine, start_state)
        self.targets = []
        self.target_id = 0
        self.target_lock_range = hg.Vec2(100, 3000)  # Target lock distance range
        self.target_lock_delay = hg.Vec2(1, 5)  # Target lock delay in lock range
        self.target_lock_t = 0
        self.target_locking_state = 0  # 0 to 1
        self.target_locked = False
        self.target_out_of_range = False
        self.target_distance = 0
        self.target_heading = 0
        self.target_altitude = 0
        self.target_angle = 0
        self.destroyable_targets = []
        self.flag_front_lock_cone = True
        self.front_lock_angle = 15

    def set_target_lock_range(self, dmin, dmax):
        self.target_lock_range.x, self.target_lock_range.y = dmin, dmax

    def reset(self):
        self.target_id = 0
        self.target_lock_t = 0
        self.target_locked = False
        self.target_out_of_range = False
        self.target_locking_state = 0

    def get_targets(self):
        return self.targets

    def get_target(self):
        if self.target_id > 0:
            return self.targets[self.target_id - 1]
        else:
            return None

    def get_target_name(self):
        if self.target_id <= 0 or len(self.targets) == 0:
            return ""
        else:
            return self.targets[self.target_id - 1].name

    def get_target_id(self):
        return self.target_id

    def set_target_id(self, tid):
        self.target_id = tid
        if tid > 0:
            if self.targets is None or len(self.targets) == 0:
                self.target_id = 0
            target = self.targets[tid - 1]
            if target.wreck or not target.activated:
                self.next_target()

    def get_target_name(self):
        if self.target_id == 0:
            return None
        return self.targets[self.target_id-1].name

    def set_target_by_name(self, target_name):
        tid = 0
        for i, tgt in enumerate(self.targets):
            if tgt.name == target_name:
                tid = i + 1
                break
        self.set_target_id(tid)

    def set_destroyable_targets(self, targets):
        self.destroyable_targets = targets

    def search_target(self):
        if len(self.targets) == 0:
            self.target_id == 0
        else:
            self.target_id = int(uniform(0, len(self.targets) - 0.1)) + 1
            target = self.targets[self.target_id - 1]
            if target.wreck or not target.activated:
                self.next_target(False)

    def next_target(self, flag_empty=True):
        if self.targets is not None and len(self.targets) > 0:
            self.target_locked = False
            self.target_lock_t = 0
            self.target_locking_state = 0
            self.target_id += 1
            if self.target_id > len(self.targets):
                if flag_empty:
                    self.target_id = 0
                    return
                else:
                    self.target_id = 1
            t = self.target_id
            target = self.targets[t - 1]
            if target.wreck or not target.activated:
                while target.wreck or not target.activated:
                    self.target_id += 1
                    if self.target_id > len(self.targets):
                        self.target_id = 1
                    if self.target_id == t:
                        self.target_id = 0
                        break
                    target = self.targets[self.target_id - 1]
        else:
            self.target_id = 0

    def update_target_lock(self, dts):
        if self.target_id > 0:
            target = self.targets[self.target_id - 1]
            if target.wreck or not target.activated:
                self.next_target()
                if self.target_id == 0:
                    return
            t_mat, t_pos, t_rot, t_aX, t_aY, t_aZ = self.targets[self.target_id - 1].decompose_matrix()
            mat, pos, rot, aX, aY, dir = self.machine.decompose_matrix()

            v = t_pos - hg.GetT(mat)
            self.target_heading = self.machine.calculate_heading(hg.Normalize(v * hg.Vec3(1, 0, 1)))
            self.target_altitude = t_pos.y
            self.target_distance = hg.Len(v)

            if self.flag_front_lock_cone:
                t_dir = hg.Normalize(v)
                self.target_angle = degrees(acos(max(-1, min(1, hg.Dot(dir, t_dir)))))
                front_lock_angle = self.front_lock_angle
            else:
                self.target_angle = 0
                front_lock_angle = 180

            if self.target_angle < front_lock_angle and self.target_lock_range.x < self.target_distance < self.target_lock_range.y:
                t = (self.target_distance - self.target_lock_range.x) / (
                        self.target_lock_range.y - self.target_lock_range.x)
                delay = self.target_lock_delay.x + t * (self.target_lock_delay.y - self.target_lock_delay.x)
                self.target_out_of_range = False
                self.target_lock_t += dts
                self.target_locking_state = min(1, self.target_lock_t / delay)
                if self.target_lock_t >= delay:
                    self.target_locked = True
            else:
                self.target_locked = False
                self.target_lock_t = 0
                self.target_out_of_range = True
                self.target_locking_state = 0

    def update(self, dts):
        self.update_target_lock(dts)

# =====================================================================================================
#                                   Missiles
# =====================================================================================================

class MissilesDevice(MachineDevice):

    def __init__(self, name, machine, slots_nodes):
        MachineDevice.__init__(self, name, machine, True)
        self.slots_nodes = slots_nodes
        self.num_slots = len(slots_nodes)
        self.missiles_config = []
        self.missiles = [None] * self.num_slots
        self.missiles_started = [None] * self.num_slots
        self.flag_hide_fitted_missiles = False

    def destroy(self):
        #if self.missiles is not None:
        #    for missile in self.missiles:
        #        if missile is not None:
        #            missile.destroy()
        self.missiles = None
        self.num_slots = 0
        self.slots_nodes = None

    def set_missiles_config(self, missiles_config):
        self.missiles_config = missiles_config


    def fit_missile(self, missile, slot_id):
        nd = missile.get_parent_node()
        nd.GetTransform().SetParent(self.slots_nodes[slot_id])
        # print("Fit Missile"+str(slot_id)+" "+str(pos.x)+" "+str(pos.y)+" "+str(pos.z))
        missile.reset(hg.Vec3(0, 0, 0), hg.Vec3(0, 0, 0))
        self.missiles[slot_id] = missile
        if self.flag_hide_fitted_missiles:
            missile.disable_nodes()

    def get_missiles_state(self):
        state = [False] * self.num_slots
        for i in range(self.num_slots):
            if self.missiles[i] is not None:
                state[i] = True
        return state

    def fire_missile(self, slot_id=-1):
        flag_missile_found = False
        missile = None
        if not self.wreck and not self.machine.wreck and slot_id < self.num_slots:
            if slot_id == -1:
                for slot_id in range(self.num_slots):
                    missile = self.missiles[slot_id]
                    if missile is not None and missile.is_armed():
                        flag_missile_found = True
                        break
                if not flag_missile_found:
                    return False, None
            missile = self.missiles[slot_id]
            if missile is not None and missile.is_armed():
                flag_missile_found = True
                self.missiles[slot_id] = None
                trans = missile.get_parent_node().GetTransform()
                mat = trans.GetWorld()
                trans.ClearParent()
                trans.SetWorld(mat)
                td = self.machine.get_device("TargettingDevice")
                if td is not None and td.target_locked:
                    target = td.targets[td.target_id - 1]
                else:
                    target = None
                missile.start(target, self.machine.v_move)
                self.missiles_started[slot_id] = missile

            if self.flag_hide_fitted_missiles:
                if flag_missile_found:
                    missile.enable_nodes()

        return flag_missile_found, missile

    def rearm(self):
        for i in range(self.num_slots):
            if self.missiles[i] is None:
                missile = self.missiles_started[i]
                if missile is not None:
                    missile.deactivate()
                    self.missiles_started[i] = None
                    self.fit_missile(missile, i)

# =====================================================================================================
#                                   Machine Gun
# =====================================================================================================

class MachineGun(MachineDevice):

    def __init__(self, name, machine, slot_node, scene, scene_physics, num_bullets, bullet_node_name="gun_bullet"):
        MachineDevice.__init__(self, name, machine, True)
        self.scene = scene
        self.scene_physics = scene_physics
        self.slot_node = slot_node
        self.bullets_particles = ParticlesEngine(name, scene, bullet_node_name, 24, hg.Vec3(2, 2, 20), hg.Vec3(20, 20, 100), 0.1, 0, "uColor0", True)

        # ParticlesEngine.__init__(self, name, scene, bullet_node_name, 24, hg.Vec3(2, 2, 20), hg.Vec3(20, 20, 100), 0.1, 0, "uColor0", True)

        self.scene_physics = scene_physics
        self.bullets_particles.start_speed_range = hg.Vec2(2000, 2000)
        self.bullets_particles.delay_range = hg.Vec2(2, 2)
        self.bullets_particles.start_offset = 0  # self.start_scale.z
        self.bullets_particles.linear_damping = 0
        self.bullets_particles.scale_range = hg.Vec2(1, 1)
        self.bullets_particles.particles_cnt_max = num_bullets

        self.bullets_feed_backs = []
        #if Destroyable_Machine.flag_activate_particles:
        self.setup_particles()

    def reset(self):
        self.bullets_particles.reset()
        self.bullets_particles.flow = 0

    def setup_particles(self):
        if len(self.bullets_feed_backs) > 0:
            self.destroy_feedbacks()

        for i in range(self.bullets_particles.num_particles):
            fb = ParticlesEngine(self.name + ".fb." + str(i), self.scene, "bullet_impact", 5,
                                 hg.Vec3(1, 1, 1), hg.Vec3(10, 10, 10), 180)
            fb.delay_range = hg.Vec2(1, 1)
            fb.flow = 0
            fb.scale_range = hg.Vec2(1, 3)
            fb.start_speed_range = hg.Vec2(0, 20)
            fb.colors = [hg.Color(1., 1., 1., 1), hg.Color(1., .5, 0.25, 0.25), hg.Color(0.1, 0., 0., 0.)]
            fb.set_rot_range(radians(20), radians(50), radians(10), radians(45), radians(5), radians(15))
            fb.gravity = hg.Vec3(0, 0, 0)
            fb.loop = False
            self.bullets_feed_backs.append(fb)

    def destroy_feedbacks(self):
        for bfb in self.bullets_feed_backs:
            bfb.destroy()
        self.bullets_feed_backs = []

    def destroy_particles(self):
        self.destroy_feedbacks()
        #self.bullets_particles.destroy()

    def destroy_gun(self):
        self.destroy_feedbacks()
        self.bullets_particles.destroy()

    # scene.GarbageCollect()

    def strike(self, i):
        self.bullets_particles.particles[i].kill()
        if len(self.bullets_feed_backs) > 0:
            fb = self.bullets_feed_backs[i]
            fb.reset()
            fb.flow = 3000

    def update(self, dts):
        td = self.machine.get_device("TargettingDevice")
        if td is not None:
            targets = td.destroyable_targets
            mat, pos, rot, aX, axisY, direction = self.machine.decompose_matrix()
            pos_prec = hg.GetT(self.slot_node.GetTransform().GetWorld())
            v0 = self.machine.v_move
            position = pos_prec + v0 * dts

            self.bullets_particles.update_kinetics(position, direction, v0, axisY, dts)
            for i in range(self.bullets_particles.num_particles):
                bullet = self.bullets_particles.particles[i]
                mat = bullet.node.GetTransform()
                pos_fb = mat.GetPos()
                # pos = hg.GetT(mat) - hg.GetZ(mat)

                if bullet.get_enabled():
                    # spd = hg.Len(bullet.v_move)
                    if pos_fb.y < 1:
                        bullet.v_move *= 0
                        self.strike(i)

                    p1 = pos_fb + bullet.v_move

                    #Collision using distance:
                    """
                    for target in targets:
                        distance = hg.Len(target.get_parent_node().GetTransform().GetPos()-pos_fb)
                        if distance < 20: #2 * hg.Len(bullet.v_move) * dts:
                            target.hit(0.1)
                            bullet.v_move = target.v_move
                            self.strike(i)
                            break

                    """

                    #Collision using raycast:
                    rc_len = hg.Len(p1 - pos_fb)
                    hit = self.scene_physics.RaycastFirstHit(self.scene, pos_fb, p1)
                    if 0 < hit.t < rc_len:
                        v_impact = hit.P - pos_fb
                        if hg.Len(v_impact) < 2 * hg.Len(bullet.v_move) * dts:
                            for target in targets:
                                cnds = target.get_collision_nodes()
                                for nd in cnds:
                                    if nd == hit.node:
                                        target.hit(0.1, hit.P)
                                        bullet.v_move = target.v_move
                                        self.strike(i)
                                        break


                if len(self.bullets_feed_backs) > 0:
                    fb = self.bullets_feed_backs[i]
                    if not fb.end and fb.flow > 0:
                        fb.update_kinetics(pos_fb, hg.Vec3.Front, bullet.v_move, hg.Vec3.Up, dts)

    def get_num_bullets(self):
        return self.bullets_particles.particles_cnt_max - self.bullets_particles.particles_cnt

    def set_num_bullets(self, num):
        self.bullets_particles.particles_cnt_max = int(num)
        self.bullets_particles.reset()

    def activate(self):
        if not self.wreck:
            super().activate()
            self.bullets_particles.flow = 24 / 2
    
    def deactivate(self):
        super().deactivate()
        self.bullets_particles.flow = 0

    """
    def is_gun_activated(self):
        if self.bullets_particles.flow == 0:
            return False
        else:
            return True
    """

    def get_new_bullets_count(self):
        return self.bullets_particles.num_new

# ==============================================
#       Control device
# ==============================================

class ControlDevice(MachineDevice):

    CM_KEYBOARD = "Keyboard"
    CM_GAMEPAD = "GamePad"
    CM_MOUSE = "Mouse"
    CM_LOGITECH_EXTREME_3DPRO = "Logitech extreme 3DPro"
    CM_LOGITECH_ATTACK_3 = "Logitech Attack 3"
    CM_NONE = "None"

    keyboard = None
    mouse = None
    gamepad = None
    generic_controller = None

    device_configurations = None
    devices = {}

    @classmethod
    def init(cls, keyboard, mouse, gamepad, generic_controller, devices_configurations_file):
        cls.keyboard = keyboard
        cls.mouse = mouse
        cls.gamepad = gamepad
        cls.generic_controller = generic_controller
        cls.device_configurations = cls.load_devices_configurations_file(devices_configurations_file)
        cls.devices = {
            cls.CM_KEYBOARD: cls.keyboard,
            cls.CM_GAMEPAD: cls.gamepad,
            cls.CM_LOGITECH_ATTACK_3: cls.generic_controller,
            cls.CM_LOGITECH_EXTREME_3DPRO: cls.generic_controller
        }
    
    @classmethod
    def get_device_input_name(cls, device_name, input_type, id):
        if device_name in cls.device_configurations:
            for inpt in cls.device_configurations[device_name].values():
                if inpt["type"] == input_type and inpt["id"] == id:
                    return inpt["name"]
        return ""

    @classmethod
    def load_devices_configurations_file(cls, file_name):
        #file = hg.OpenText(file_name)
        file = open(file_name, "r")
        if not file:
            print("ERROR - Can't open json file : " + file_name)
        else:
            #json_script = hg.ReadString(file)
            #hg.Close(file)
            json_script = file.read()
            file.close()
            if json_script != "":
                jsonscript = json.loads(json_script)
                for name, device in jsonscript.items():
                    for i_name, inpt in device.items():
                        if "reset" in inpt:
                            inpt["reset"] = True if inpt["reset"] == "true" else False
                        if "invert" in inpt:
                            inpt["invert"] = True if inpt["invert"] == "true" else False
                return jsonscript

    @staticmethod
    def load_inputs_mapping_file(file_name, input_mapping_name):
        #file = hg.OpenText(file_name)
        file = open(file_name, "r")
        inputs_mapping_encoded = None
        inputs_mapping = None
        if not file:
            print("ERROR - Can't open json file : " + file_name)
        else:
            #json_script = hg.ReadString(file)
            #hg.Close(file)
            json_script = file.read()
            file.close()
            if json_script != "":
                inputs_mapping_encoded = json.loads(json_script)
                im = inputs_mapping_encoded[input_mapping_name]
                cmode_decode = {}
                for cmode, maps in im.items():
                    maps_decode = {}
                    # If inputs names refers to Harfang Enums...:
                    if cmode == "Keyboard":
                        for cmd, hg_enum in maps.items():
                            if hg_enum != "":
                                if not hg_enum.isdigit():
                                    try:
                                        exec("maps_decode['%s'] = hg.%s" % (cmd, hg_enum))
                                    except AttributeError:
                                        print("ERROR - Harfang Enum not implemented ! - " + "hg." + hg_enum)
                                        maps_decode[cmd] = ""
                                else:
                                    maps_decode[cmd] = int(hg_enum)
                            else:
                                maps_decode[cmd] = ""
                    # ...Else
                    else:
                        maps_decode = maps
                    cmode_decode[cmode] = maps_decode
                inputs_mapping = {input_mapping_name: cmode_decode}
            else:
                print("ERROR - Inputs parameters empty : " + file_name)
        return inputs_mapping_encoded, inputs_mapping

    @classmethod
    def normalize_axis_value(cls, device_id, axis_def):
        if axis_def["type"] == "axis":
            v = ControlDevice.devices[device_id].Axes(axis_def["id"])
            v = min(max(v, axis_def["min"]), axis_def["max"])
            if axis_def["zero"] - axis_def["zero_epsilon"] < v < axis_def["zero_epsilon"] + axis_def["zero"]:
                return 0  
            elif v > axis_def["zero"]:
                v = (v - axis_def["zero"]) / (axis_def["max"] - axis_def["zero"])
            elif v < axis_def["zero"]:
                v = - (v - axis_def["zero"]) / (axis_def["min"] - axis_def["zero"])
            if axis_def["invert"]:
                v = -v
            return v
        return 0


    def __init__(self, name, machine, inputs_mapping_file="", input_mapping_name="", control_mode=CM_KEYBOARD, start_state=False):
        MachineDevice.__init__(self, name, machine, start_state)
        self.flag_user_control = True
        self.control_mode = control_mode
        self.inputs_mapping_file = inputs_mapping_file
        self.inputs_mapping_encoded = {}
        self.inputs_mapping = {}
        self.input_mapping_name = input_mapping_name
        if self.inputs_mapping_file != "":
            self.inputs_mapping_encoded, self.inputs_mapping = self.load_inputs_mapping_file(self.inputs_mapping_file, input_mapping_name)

    def set_control_mode(self, cmode):
        self.control_mode = cmode

    def activate_user_control(self):
        self.flag_user_control = True

    def deactivate_user_control(self):
        self.flag_user_control = False

    def is_user_control_active(self):
        return self.flag_user_control

# ==============================================
#       Missile user control device - Dubug mode
# ==============================================

class MissileUserControlDevice(ControlDevice):

    def __init__(self, name, machine, control_mode=ControlDevice.CM_KEYBOARD, start_state=False):
        ControlDevice.__init__(self, name, machine, "", "MissileLauncherUserInputsMapping", control_mode, start_state)
        self.pos_mem = None

    def update(self, dts):
        if self.is_activated():
            mat, pos, rot, aX, aY, aZ = self.machine.decompose_matrix()
            step = 0.5
            if ControlDevice.keyboard.Down(hg.K_Up):
                pos += aY * step
            if ControlDevice.keyboard.Down(hg.K_Down):
                pos -= aY * step
            if ControlDevice.keyboard.Down(hg.K_Left):
                pos -= aX * step
            if ControlDevice.keyboard.Down(hg.K_Right):
                pos += aX * step
            if ControlDevice.keyboard.Down(hg.K_Add):
                pos += aZ * step
            if ControlDevice.keyboard.Down(hg.K_Sub):
                pos -= aZ * step
            self.pos_mem = pos


# ==============================================
#       Missile launcher user control device
# ==============================================

class MissileLauncherUserControlDevice(ControlDevice):

    def __init__(self, name, machine, inputs_mapping_file, control_mode=ControlDevice.CM_KEYBOARD, start_state=False):
        ControlDevice.__init__(self, name, machine, inputs_mapping_file, "MissileLauncherUserInputsMapping", control_mode, start_state)
        self.set_control_mode(control_mode)
        self.commands.update({
                "SWITCH_ACTIVATION": self.switch_activation,
                "NEXT_PILOT": self.next_pilot,
                "INCREASE_HEALTH_LEVEL": self.increase_health_level,
                "DECREASE_HEALTH_LEVEL": self.decrease_health_level,
                "NEXT_TARGET": self.next_target,
                "FIRE_MISSILE": self.fire_missile,
                "REARM": self.rearm
            })

    # ====================================================================================

    def update_cm_keyboard(self, dts):
        im = self.inputs_mapping["MissileLauncherUserInputsMapping"][self.control_mode]
        for cmd, input_code in im.items():
            if cmd in self.commands and input_code != "":
                self.commands[cmd]({"id": input_code})

    def update_cm_joystick(self, dts):
        im = self.inputs_mapping["MissileLauncherUserInputsMapping"][self.control_mode]
        for cmd, input_name in im.items():
            if cmd in self.commands and input_name != "":
                i_def = ControlDevice.device_configurations[self.control_mode][input_name]
                self.commands[cmd](i_def)

    def update_cm_mouse(self, dts):
        im = self.inputs_mapping["MissileLauncherUserInputsMapping"][self.control_mode]

    def update(self, dts):
        if self.activated:
            if self.flag_user_control and self.machine.has_focus():
                if self.control_mode == ControlDevice.CM_KEYBOARD:
                    self.update_cm_keyboard(dts)
                elif self.control_mode == ControlDevice.CM_GAMEPAD:
                    self.update_cm_joystick(dts)
                elif self.control_mode == ControlDevice.CM_MOUSE:
                    self.update_cm_mouse(dts)
                elif self.control_mode == ControlDevice.CM_LOGITECH_ATTACK_3:
                    self.update_cm_joystick(dts)

    # =============================== Keyboard commands ====================================

    def switch_activation(self, value):
        pass

    def next_pilot(self, value):
        pass

    def increase_health_level(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_health_level(self.machine.health_level + 0.01)

    def decrease_health_level(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_health_level(self.machine.health_level - 0.01)

    def next_target(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            td = self.machine.get_device("TargettingDevice")
            if td is not None:
                td.next_target()

    def fire_missile(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            md = self.machine.get_device("MissilesDevice")
            if md is not None:
                md.fire_missile()

    def rearm(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            self.machine.rearm()

# ==============================================
#       Aircraft user control device
# ==============================================

class AircraftUserControlDevice(ControlDevice):

    def __init__(self, name, machine, inputs_mapping_file, control_mode=ControlDevice.CM_KEYBOARD, start_state=False):
        ControlDevice.__init__(self, name, machine, inputs_mapping_file, "AircraftUserInputsMapping", control_mode, start_state)
        self.set_control_mode(control_mode)
        self.commands.update({
                "SWITCH_ACTIVATION": self.switch_activation,
                "NEXT_PILOT": self.next_pilot,
                "INCREASE_HEALTH_LEVEL": self.increase_health_level,
                "DECREASE_HEALTH_LEVEL": self.decrease_health_level,
                "INCREASE_THRUST_LEVEL": self.increase_thrust_level,
                "DECREASE_THRUST_LEVEL": self.decrease_thrust_level,
                "SET_THRUST_LEVEL": self.set_thrust_level,
                "INCREASE_BRAKE_LEVEL": self.increase_brake_level,
                "DECREASE_BRAKE_LEVEL": self.decrease_brake_level,
                "INCREASE_FLAPS_LEVEL": self.increase_flaps_level,
                "DECREASE_FLAPS_LEVEL": self.decrease_flaps_level,
                "ROLL_LEFT": self.roll_left,
                "ROLL_RIGHT": self.roll_right,
                "SET_ROLL": self.set_roll,
                "PITCH_UP": self.pitch_up,
                "PITCH_DOWN": self.pitch_down,
                "SET_PITCH": self.set_pitch,
                "YAW_LEFT": self.yaw_left,
                "YAW_RIGHT": self.yaw_right,
                "SET_YAW": self.set_yaw,
                "SWITCH_POST_COMBUSTION": self.switch_post_combustion,
                "NEXT_TARGET": self.next_target,
                "SWITCH_GEAR": self.switch_gear,
                "ACTIVATE_IA": self.activate_ia,
                "ACTIVATE_AUTOPILOT": self.activate_autopilot,
                "SWITCH_EASY_STEERING": self.switch_easy_steering,
                "FIRE_MACHINE_GUN": self.fire_machine_gun,
                "FIRE_MISSILE": self.fire_missile,
                "REARM": self.rearm
            })

    # =================== Functions =================================================================

    def update_cm_keyboard(self, dts):
        im = self.inputs_mapping["AircraftUserInputsMapping"][self.control_mode]
        for cmd, input_code in im.items():
            if cmd in self.commands and input_code != "":
                self.commands[cmd]({"id":input_code})

    def update_cm_joystick(self, dts):
        im = self.inputs_mapping["AircraftUserInputsMapping"][self.control_mode]
        for cmd, input_name in im.items():
            if cmd in self.commands and input_name != "":
                i_def = ControlDevice.device_configurations[self.control_mode][input_name]
                self.commands[cmd](i_def)

    def update_cm_mouse(self, dts):
        im = self.inputs_mapping["AircraftUserInputsMapping"][self.control_mode]

    def update(self, dts):
        if self.activated:
            if self.flag_user_control and self.machine.has_focus():
                if self.control_mode == ControlDevice.CM_KEYBOARD:
                    self.update_cm_keyboard(dts)
                elif self.control_mode == ControlDevice.CM_GAMEPAD:
                    self.update_cm_joystick(dts)
                elif self.control_mode == ControlDevice.CM_MOUSE:
                    self.update_cm_mouse(dts)
                elif self.control_mode == ControlDevice.CM_LOGITECH_ATTACK_3:
                    self.update_cm_joystick(dts)

    # =============================== Keyboard commands ====================================

    def switch_activation(self, value):
        pass

    def next_pilot(self, value):
        pass

    def increase_health_level(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_health_level(self.machine.health_level + 0.01)

    def decrease_health_level(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_health_level(self.machine.health_level - 0.01)

    def increase_thrust_level(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_thrust_level(self.machine.thrust_level_dest + 0.01)

    def decrease_thrust_level(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_thrust_level(self.machine.thrust_level_dest - 0.01)

    def set_thrust_level(self, value):
        v = ControlDevice.normalize_axis_value(self.control_mode, value)
        if value["reset"]:
            v = v * 0.01 + self.machine.thrust_level_dest
        self.machine.set_thrust_level(v)

    def increase_brake_level(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_brake_level(self.machine.brake_level_dest + 0.01)

    def decrease_brake_level(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_brake_level(self.machine.brake_level_dest - 0.01)

    def increase_flaps_level(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_flaps_level(self.machine.flaps_level + 0.01)

    def decrease_flaps_level(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_flaps_level(self.machine.flaps_level - 0.01)

    def roll_left(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_roll_level(1)
        elif ControlDevice.devices[self.control_mode].Released(value["id"]):
            self.machine.set_roll_level(0)

    def roll_right(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_roll_level(-1)
        elif ControlDevice.devices[self.control_mode].Released(value["id"]):
            self.machine.set_roll_level(0)

    def set_roll(self, value):
        v = -ControlDevice.normalize_axis_value(self.control_mode, value)
        self.machine.set_roll_level(v)

    def pitch_up(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_pitch_level(1)
        elif ControlDevice.devices[self.control_mode].Released(value["id"]):
            self.machine.set_pitch_level(0)

    def pitch_down(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_pitch_level(-1)
        elif ControlDevice.devices[self.control_mode].Released(value["id"]):
            self.machine.set_pitch_level(0)

    def set_pitch(self, value):
        v = -ControlDevice.normalize_axis_value(self.control_mode,value)
        self.machine.set_pitch_level(v)

    def yaw_left(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_yaw_level(-1)
        elif ControlDevice.devices[self.control_mode].Released(value["id"]):
            self.machine.set_yaw_level(0)

    def yaw_right(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.machine.set_yaw_level(1)
        elif ControlDevice.devices[self.control_mode].Released(value["id"]):
            self.machine.set_yaw_level(0)

    def set_yaw(self, value):
        v = ControlDevice.normalize_axis_value(self.control_mode,value)
        self.machine.set_yaw_level(v)

    def switch_post_combustion(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            if self.machine.post_combustion:
                self.machine.deactivate_post_combustion()
            else:
                self.machine.activate_post_combustion()

    def next_target(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            td = self.machine.get_device("TargettingDevice")
            if td is not None:
                td.next_target()

    def switch_gear(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            if "Gear" in self.machine.devices and self.machine.devices["Gear"] is not None:
                gear = self.machine.devices["Gear"]
                if not self.machine.flag_landed:
                    if gear.activated:
                        gear.deactivate()
                    else:
                        gear.activate()

    def activate_autopilot(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            autopilot_device = self.machine.get_device("AutopilotControlDevice")
            if autopilot_device is not None:
                self.deactivate()
                autopilot_device.activate()


    def activate_ia(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            ia_device = self.machine.get_device("IAControlDevice")
            if ia_device is not None:
                self.deactivate()
                ia_device.activate()

    def switch_easy_steering(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            self.machine.flag_easy_steering = not self.machine.flag_easy_steering

    def fire_machine_gun(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            n = self.machine.get_machinegun_count()
            for i in range(n):
                mgd = self.machine.get_device("MachineGunDevice_%02d" % i)
                if mgd is not None and not mgd.is_activated():
                    mgd.activate()
        elif ControlDevice.devices[self.control_mode].Released(value["id"]):
            n = self.machine.get_machinegun_count()
            for i in range(n):
                mgd = self.machine.get_device("MachineGunDevice_%02d" % i)
                if mgd is not None and mgd.is_activated():
                    mgd.deactivate()

    def fire_missile(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            md = self.machine.get_device("MissilesDevice")
            if md is not None:
                md.fire_missile()

    def rearm(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            self.machine.rearm()

# ===================================================================
#       Aircraft Autopilot control device
#       Autopilot device con controls only one aircraft
# ===================================================================

class AircraftAutopilotControlDevice(ControlDevice):

    def __init__(self, name, machine, inputs_mapping_file, control_mode=ControlDevice.CM_KEYBOARD, start_state=False):
        ControlDevice.__init__(self, name, machine, inputs_mapping_file, "AircraftAutopilotInputsMapping", control_mode, start_state)

        self.autopilot_speed = -1  # m.s-1
        self.autopilot_heading = 0  # degrees
        self.autopilot_altitude = 500  # m

        self.autopilot_roll_attitude = 0
        self.autopilot_pitch_attitude = 0

        self.heading_step = 1

        self.altitude_step = 10
        self.altitude_range = [0, 50000]

        self.speed_step = 10
        self.speed_range = [-1, 3000 * 3.6]

        self.flag_easy_steering_mem = False

        self.set_control_mode(control_mode)
        self.commands.update({
                "ACTIVATE_USER_CONTROL": self.activate_user_control_device,
                "INCREASE_SPEED": self.increase_speed,
                "DECREASE_SPEED": self.decrease_speed,
                "SET_SPEED": self.set_speed,
                "INCREASE_HEADING": self.increase_heading,
                "DECREASE_HEADING": self.decrease_heading,
                "SET_HEADING": self.set_heading,
                "INCREASE_ALTITUDE": self.increase_altitude,
                "DECREASE_ALTITUDE": self.decrease_altitude,
                "SET_ALTITUDE": self.set_altitude
            })


    # ============================== functions

    def activate(self):
        if not self.activated:
            ControlDevice.activate(self)
            self.flag_easy_steering_mem = self.machine.flag_easy_steering
            self.machine.flag_easy_steering = True

    def deactivate(self):
        if self.activated:
            ControlDevice.deactivate(self)
            self.machine.flag_easy_steering = self.flag_easy_steering_mem

    def set_autopilot_speed(self, value):
        self.autopilot_speed = value

    def set_autopilot_heading(self, value):
        self.autopilot_heading = max(min(360, value), 0)

    def set_autopilot_altitude(self, value):
        self.autopilot_altitude = value

    # =============================== Keyboard commands ====================================

    def activate_user_control_device(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            uctrl = self.machine.get_device("UserControlDevice")
            if uctrl is not None:
                self.deactivate()
                uctrl.activate()

    def increase_speed(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.autopilot_speed = min(self.autopilot_speed + self.speed_step, self.speed_range[1])

    def decrease_speed(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.autopilot_speed = max(self.autopilot_speed - self.speed_step, self.speed_range[0])

    def set_speed(self, value):
        pass

    def increase_heading(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.autopilot_heading = (self.autopilot_heading + self.heading_step) % 360

    def decrease_heading(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.autopilot_heading = (self.autopilot_heading - self.heading_step) % 360

    def set_heading(self, value):
        pass

    def increase_altitude(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.autopilot_altitude = min(self.autopilot_altitude + self.altitude_step, self.altitude_range[1])

    def decrease_altitude(self, value):
        if ControlDevice.devices[self.control_mode].Down(value["id"]):
            self.autopilot_altitude = max(self.autopilot_altitude - self.altitude_step, self.altitude_range[0])

    def set_altitude(self, value):
        pass


    # ====================================================================================

    def update_cm_keyboard(self, dts):
        im = self.inputs_mapping["AircraftAutopilotInputsMapping"][self.control_mode]
        for cmd, input_code in im.items():
            if cmd in self.commands and input_code != "":
                self.commands[cmd]({"id": input_code})

    def update_cm_joystick(self, dts):
        im = self.inputs_mapping["AircraftAutopilotInputsMapping"][self.control_mode]
        for cmd, input_name in im.items():
            if cmd in self.commands and input_name != "":
                i_def = ControlDevice.device_configurations[self.control_mode][input_name]
                self.commands[cmd](i_def)

    def update_cm_mouse(self, dts):
        im = self.inputs_mapping["AircraftAutopilotInputsMapping"][self.control_mode]

    def update_controlled_devices(self, dts):
        aircraft = self.machine
        if not aircraft.wreck and not aircraft.flag_going_to_takeoff_position and not aircraft.flag_landed:
            if self.autopilot_speed >= 0:
                a_range = 1
                v = aircraft.get_linear_speed()
                a = aircraft.get_linear_acceleration()
                f = v / self.autopilot_speed * 100

                if f < 80:
                    aircraft.set_brake_level(0)
                    # self.set_flaps_level(0)
                    aircraft.set_thrust_level(1)
                    aircraft.activate_post_combustion()
                elif f > 120:
                    aircraft.set_thrust_level(0.25)
                    aircraft.set_brake_level(0.5)
                elif f < 100:
                    if a < -a_range:
                        aircraft.set_brake_level(0)
                        # self.set_flaps_level(0)
                        aircraft.set_thrust_level(1)
                        aircraft.activate_post_combustion()
                    else:
                        # fa = 1+(a/a_range) #1 - ((f - 80) / 20)
                        fa = 1 - ((f - 80) / 20)
                        aircraft.set_thrust_level(0.5 + fa * 0.5)
                elif f > 100:
                    if a > a_range:
                        aircraft.set_thrust_level(0.25)
                        aircraft.set_brake_level(0.5)
                    else:
                        fa = (120 - f) / 20
                        # fa = max(0,(a/a_range)) #(120-f)/20
                        aircraft.set_brake_level(0.5 * fa)
                        aircraft.set_thrust_level(0.75)
                # vkm=v*3.6
                # if vkm<self.landing_max_speed:
                #    f=1-max(0,min(1,(vkm-self.minimum_flight_speed)/(self.landing_max_speed-self.minimum_flight_speed)))
                #    self.set_flaps_level(self.f)

            # straighten aircraft:
            mat = aircraft.parent_node.GetTransform().GetWorld()
            aY = hg.GetY(mat)
            if aY.y < 0:
                aircraft.set_roll_level(0)
                aircraft.set_pitch_level(0)
                aircraft.set_yaw_level(0)
            else:
                # heading / roll_attitude:
                diff = self.autopilot_heading - aircraft.heading
                if diff > 180:
                    diff -= 360
                elif diff < -180:
                    diff += 360

                tc = max(-1, min(1, -diff / 90))
                if tc < 0:
                    tc = -pow(-tc, 0.5)
                else:
                    tc = pow(tc, 0.5)

                self.autopilot_roll_attitude = max(min(180, tc * 85), -180)

                diff = self.autopilot_roll_attitude - aircraft.roll_attitude
                tr = max(-1, min(1, diff / 20))
                aircraft.set_roll_level(tr)

                # altitude / pitch_attitude:
                diff = self.autopilot_altitude - aircraft.get_altitude()
                ta = max(-1, min(1, diff / 500))

                if ta < 0:
                    ta = -pow(-ta, 0.7)
                else:
                    ta = pow(ta, 0.7)

                self.autopilot_pitch_attitude = max(min(180, ta * 45), -180)

                diff = self.autopilot_pitch_attitude - aircraft.pitch_attitude
                tp = max(-1, min(1, diff / 10))
                aircraft.set_pitch_level(-tp)

    def update(self, dts):
        if self.activated:
            if self.flag_user_control and self.machine.has_focus():
                if self.control_mode == ControlDevice.CM_KEYBOARD:
                    self.update_cm_keyboard(dts)
                elif self.control_mode == ControlDevice.CM_GAMEPAD:
                    self.update_cm_joystick(dts)
                elif self.control_mode == ControlDevice.CM_MOUSE:
                    self.update_cm_mouse(dts)
                elif self.control_mode == ControlDevice.CM_LOGITECH_ATTACK_3:
                     self.update_cm_joystick(dts)

            self.update_controlled_devices(dts)


# ===========================================================
#       Aircraft IA control device
#       IA control device can control only one aicraft.
# ===========================================================


class AircraftIAControlDevice(ControlDevice):
    IA_COM_IDLE = 0
    IA_COM_LIFTOFF = 1
    IA_COM_FIGHT = 2
    IA_COM_RETURN_TO_BASE = 3
    IA_COM_LANDING = 4

    def __init__(self, name, machine, inputs_mapping_file, control_mode=ControlDevice.CM_KEYBOARD, start_state=False):
        ControlDevice.__init__(self, name, machine, inputs_mapping_file, "AircraftIAInputsMapping", control_mode, start_state)
        self.set_control_mode(control_mode)

        self.IA_commands_labels = ["IA_COM_IDLE", "IA_COM_LIFTOFF", "IA_COM_FIGHT", "IA_COM_RETURN_TO_BASE", "IA_COM_LANDING"]

        self.flag_IA_start_liftoff = True
        self.IA_liftoff_delay = 0
        self.IA_fire_missiles_delay = 10
        self.IA_target_distance_fight = 3000  # Set altitude to target altitude under this distance
        self.IA_fire_missile_cptr = 0
        self.IA_flag_altitude_correction = False
        self.IA_flag_position_correction = False
        self.IA_position_correction_heading = 0
        self.IA_flag_speed_correction = False
        self.IA_flag_go_to_target = False
        self.IA_altitude_min = 500
        self.IA_altitude_max = 8000
        self.IA_altitude_safe = 1500
        self.IA_gun_distance_max = 1000
        self.IA_gun_angle = 10
        self.IA_cruising_altitude = 500
        self.IA_command = AircraftIAControlDevice.IA_COM_IDLE

        self.IA_target_point = hg.Vec3(0, 0, 0)
        self.IA_trajectory_fit_distance = 1000
        self.IA_landing_target = None
        self.IA_flag_landing_target_found = False
        self.IA_flag_goto_landing_approach_point = False
        self.IA_flag_reached_landing_point = False

        self.commands.update({
                "ACTIVATE_USER_CONTROL": self.activate_user_control
            })

    # ==================================== functions

    def activate(self):
        if not self.activated:
            ControlDevice.activate(self)
            aircraft = self.machine
            if not aircraft.wreck:

                td = aircraft.get_device("TargettingDevice")
                if td.target_id == 0:
                    td.search_target()

                n = aircraft.get_machinegun_count()
                for i in range(n):
                    mgd = aircraft.get_device("MachineGunDevice_%02d" % i)
                    if mgd is not None and mgd.is_activated():
                        mgd.deactivate()

                self.IA_flag_go_to_target = False
                if aircraft.flag_landed:
                    if self.IA_liftoff_delay <= 0:
                        self.IA_liftoff_delay = 1
                    self.IA_command = AircraftIAControlDevice.IA_COM_LIFTOFF
                else:
                    if td.target_id == 0:
                        self.IA_command = AircraftIAControlDevice.IA_COM_LANDING
                    else:
                        self.IA_command = AircraftIAControlDevice.IA_COM_FIGHT
                ap_ctrl = aircraft.get_device("AutopilotControlDevice")
                if ap_ctrl is not None:
                    ap_ctrl.activate()
                    ap_ctrl.deactivate_user_control()
                    ap_ctrl.set_autopilot_altitude(aircraft.get_altitude())

    def deactivate(self):
        if self.activated:
            ControlDevice.deactivate(self)
            aircraft = self.machine
            n = aircraft.get_machinegun_count()
            for i in range(n):
                mgd = aircraft.get_device("MachineGunDevice_%02d" % i)
                if mgd is not None and mgd.is_activated():
                    mgd.deactivate()
            self.IA_flag_go_to_target = False
            aircraft.set_flaps_level(0)
            self.IA_flag_landing_target_found = False
            ap_ctrl = aircraft.get_device("AutopilotControlDevice")
            if ap_ctrl is not None:
                ap_ctrl.deactivate()
                ap_ctrl.activate_user_control()

    def set_IA_landing_target(self, landing_target: LandingTarget):
        self.IA_landing_target = landing_target

    def calculate_landing_projection(self, aircraft, landing_target: LandingTarget):
        pos = aircraft.parent_node.GetTransform().GetPos()
        o = landing_target.get_landing_position()
        oa = pos - o
        uap = landing_target.get_landing_vector()
        dot = hg.Dot(hg.Vec2(oa.x, oa.z), uap)
        oap = uap * dot
        d = hg.Len(oap)
        if dot < 0: d = -d
        return landing_target.get_position(d)

    def calculate_landing_approach_factor(self, landing_target: LandingTarget, landing_projection: hg.Vec3):
        o = landing_target.get_landing_position()
        v = landing_projection - o
        vh = hg.Vec2(v.x, v.z)
        vl = landing_target.get_landing_vector()
        dist = hg.Len(vh)
        if hg.Dot(vl, vh) < 0:
            dist = -dist
        return dist / landing_target.horizontal_amplitude

    def calculate_landing_target_point(self, aircraft, landing_target, landing_proj):
        fit_distance = aircraft.get_linear_speed() * 0.5 * 3.6
        o = landing_target.get_landing_position()
        o = hg.Vec2(o.x, o.z)
        ap = hg.Vec2(landing_proj.x, landing_proj.z)
        pos = aircraft.parent_node.GetTransform().GetPos()
        a = hg.Vec2(pos.x, pos.z)
        dist = hg.Len(ap - a)
        if dist < fit_distance:
            dx = sqrt(fit_distance * fit_distance - dist * dist)
            tdist = hg.Len(ap - o) - dx
            return landing_target.get_position(tdist)
        else:
            return landing_proj

    def update_controlled_device(self, dts):
        aircraft = self.machine
        if not aircraft.wreck and not aircraft.flag_going_to_takeoff_position:
            if self.IA_command == AircraftIAControlDevice.IA_COM_IDLE:
                self.update_IA_idle(aircraft)
            elif self.IA_command == AircraftIAControlDevice.IA_COM_LIFTOFF:
                self.update_IA_liftoff(aircraft, dts)
            elif self.IA_command == AircraftIAControlDevice.IA_COM_FIGHT:
                self.update_IA_fight(aircraft, dts)
            elif self.IA_command == AircraftIAControlDevice.IA_COM_LANDING:
                self.update_IA_landing(aircraft, dts)

    def update_IA_liftoff(self, aircraft, dts):
        self.IA_flag_landing_target_found = False
        aircraft.set_flaps_level(1)
        if self.flag_IA_start_liftoff:
            self.IA_liftoff_delay -= dts
        if self.IA_liftoff_delay <= 0:
            if aircraft.thrust_level < 1 or not aircraft.post_combustion:
                aircraft.set_brake_level(0)
                aircraft.set_flaps_level(1)
                aircraft.set_thrust_level(1)
                aircraft.activate_post_combustion()
                aircraft.angular_levels_dest.z = 0
                aircraft.angular_levels_dest.x = radians(-5)
            if aircraft.ground_node_collision is None:
                aircraft.flag_landed = False
                gear = aircraft.get_device("Gear")
                if gear is not None:
                    if gear.activated:
                        gear.deactivate()
                autopilot = aircraft.get_device("AutopilotControlDevice")
                if autopilot is not None:
                    autopilot.set_autopilot_altitude(200)
                    if aircraft.parent_node.GetTransform().GetPos().y > 100:
                        # if abs(vs) > 1:
                        aircraft.set_flaps_level(0)
                        td = aircraft.get_device("TargettingDevice")
                        if td is not None:
                            td.search_target()
                            if td.target_id == 0:
                                self.IA_command = AircraftIAControlDevice.IA_COM_LANDING
                            else:
                                self.IA_command = AircraftIAControlDevice.IA_COM_FIGHT

    def update_IA_idle(self, aircraft):
        autopilot = aircraft.devices["AutopilotControlDevice"]
        if autopilot is not None:
            autopilot.set_autopilot_speed(400 / 3.6)
            n = aircraft.get_machinegun_count()
            for i in range(n):
                mgd = aircraft.get_device("MachineGunDevice_%02d" % i)
                if mgd is not None and mgd.is_activated():
                    mgd.deactivate()
            autopilot.set_autopilot_altitude(self.IA_cruising_altitude)
            autopilot.set_autopilot_heading(0)

            if aircraft.pitch_attitude > 15:
                aircraft.set_thrust_level(1)
                aircraft.activate_post_combustion()
            elif -15 < aircraft.pitch_attitude < 15:
                aircraft.deactivate_post_combustion()
                aircraft.set_thrust_level(1)
            else:
                aircraft.deactivate_post_combustion()
                aircraft.set_thrust_level(0.5)

    def get_nearest_landing_target(self, aircraft):
        distances = []
        pos = aircraft.parent_node.GetTransform().GetPos()
        for lt in aircraft.landing_targets:
            p = lt.get_approach_entry_position()
            distances.append({"landing_target": lt, "distance": hg.Len(p - pos)})
        distances.sort(key=lambda p: p["distance"])
        return distances[0]["landing_target"]

    def update_IA_landing(self, aircraft, dts):
        if "AutopilotControlDevice" in aircraft.devices and aircraft.devices["AutopilotControlDevice"] is not None:
            autopilot = aircraft.devices["AutopilotControlDevice"]
            if not self.IA_flag_landing_target_found:
                n = aircraft.get_machinegun_count()
                for i in range(n):
                    mgd = aircraft.get_device("MachineGunDevice_%02d" % i)
                    if mgd is not None and mgd.is_activated():
                        mgd.deactivate()
                self.IA_landing_target = self.get_nearest_landing_target(aircraft)
                if self.IA_landing_target is not None:
                    self.IA_flag_landing_target_found = True
                    self.IA_flag_goto_landing_approach_point = True
                    self.IA_flag_reached_landing_point = False
            else:
                pos = aircraft.parent_node.GetTransform().GetPos()
                landing_proj = self.calculate_landing_projection(aircraft, self.IA_landing_target)
                landing_f = self.calculate_landing_approach_factor(self.IA_landing_target, landing_proj)
                if self.IA_flag_goto_landing_approach_point:
                    if landing_f > 1:
                        self.IA_flag_goto_landing_approach_point = False
                    else:
                        p = self.IA_landing_target.get_approach_entry_position()
                        v = p - pos
                        if hg.Len(v) < self.IA_trajectory_fit_distance:
                            self.IA_flag_goto_landing_approach_point = False
                        else:
                            autopilot.set_autopilot_heading(aircraft.calculate_heading(hg.Normalize(v * hg.Vec3(1, 0, 1))))
                            autopilot.set_autopilot_altitude(p.y)
                            autopilot.set_autopilot_speed(2000 / 3.6)
                            aircraft.set_flaps_level(0)
                            aircraft.set_brake_level(0)
                else:
                    # 2D Distance to trajectory:
                    lf = (landing_f - 0.3) / (1 - 0.3)  # lf: near approach parameter (0.3 of total approach)
                    # far approach
                    if lf > 0:
                        self.IA_target_point = self.calculate_landing_target_point(aircraft, self.IA_landing_target, landing_proj)
                        v = self.IA_target_point - pos
                        autopilot.set_autopilot_heading(aircraft.calculate_heading(hg.Normalize(v * hg.Vec3(1, 0, 1))))
                        lfq = floor(lf * 10) / 10
                        autopilot.set_autopilot_speed((2000 * lfq + aircraft.landing_max_speed * (1 - lfq)) / 3.6)
                        aircraft.set_flaps_level(pow(1 - lf, 2) * 0.5)
                        autopilot.set_autopilot_altitude(self.IA_target_point.y)
                    # Near approach
                    else:
                        if "Gear" in aircraft.devices and aircraft.devices["Gear"] is not None:
                            gear = aircraft.devices["Gear"]
                            if not gear.activated:
                                gear.activate()
                            o = self.IA_landing_target.get_landing_position()
                        if landing_f > 0:
                            autopilot.set_autopilot_speed(aircraft.minimum_flight_speed / 3.6)
                            lv = aircraft.get_linear_speed() * 3.6
                            vh = self.IA_landing_target.get_landing_vector() * -100
                            v = hg.Vec3(o.x + vh.x, o.y, o.z + vh.y) - pos
                            autopilot.set_autopilot_heading(aircraft.calculate_heading(hg.Normalize(v * hg.Vec3(1, 0, 1))))
                            alt = hg.GetT(aircraft.parent_node.GetTransform().GetWorld()).y
                            f = max(-1, min(1, ((o.y + 4) - alt) / 2))
                            aircraft.set_flaps_level(0.5 + 0.5 * f)
                            if f < 0:
                                autopilot.set_autopilot_altitude(self.IA_target_point.y + 30 * (1 - aircraft.health_level) + 0 * f)
                            else:
                                autopilot.set_autopilot_altitude(self.IA_target_point.y + 60 * (1 - aircraft.health_level) + 30 * f)
                        else:
                            if not self.IA_flag_reached_landing_point:
                                self.IA_flag_reached_landing_point = True
                                if pos.y < o.y or pos.y > o.y + 10:
                                    self.IA_flag_landing_target_found = False
                            else:
                                autopilot.set_autopilot_speed(-1)
                                aircraft.set_brake_level(1)
                                aircraft.set_thrust_level(0)
                                aircraft.set_flaps_level(0)
                                if aircraft.ground_node_collision is not None:
                                    hs, vs = aircraft.get_world_speed()
                                    if hs < 1 and abs(vs) < 1:
                                        aircraft.set_landed()
                                        self.IA_liftoff_delay = 2
                                        self.IA_command = AircraftIAControlDevice.IA_COM_LIFTOFF

    def update_IA_fight(self, aircraft, dts):
        autopilot = aircraft.devices["AutopilotControlDevice"]
        if autopilot is not None:
            if "Gear" in aircraft.devices and aircraft.devices["Gear"] is not None:
                gear = aircraft.devices["Gear"]
                if gear.activated:
                    gear.deactivate()
            autopilot.set_autopilot_speed(-1)
            speed = aircraft.get_linear_speed() * 3.6  # convert to km/h
            aircraft.set_brake_level(0)
            if speed < aircraft.minimum_flight_speed:
                if not self.IA_flag_speed_correction:
                    self.IA_flag_speed_correction = True
                    aircraft.set_flaps_level(1)
                    aircraft.set_thrust_level(1)
                    aircraft.activate_post_combustion()
                    autopilot.set_autopilot_altitude(aircraft.get_altitude())
                    autopilot.set_autopilot_heading(aircraft.heading)
            else:
                self.IA_flag_speed_correction = False
                aircraft.set_flaps_level(0)
                alt = aircraft.get_altitude()
                td = aircraft.get_device("TargettingDevice")
                if td.target_id > 0:
                    if self.IA_flag_position_correction:
                        if aircraft.playfield_distance < aircraft.playfield_safe_distance / 2:
                            self.IA_flag_position_correction = False

                    elif self.IA_flag_altitude_correction:
                        self.IA_flag_go_to_target = False
                        autopilot.set_autopilot_altitude(self.IA_altitude_safe)
                        if self.IA_altitude_safe - 100 < alt < self.IA_altitude_safe + 100:
                            self.IA_flag_altitude_correction = False

                    else:
                        target_distance = hg.Len(td.targets[td.target_id - 1].get_parent_node().GetTransform().GetPos() - aircraft.parent_node.GetTransform().GetPos())
                        autopilot.set_autopilot_heading(td.target_heading)
                        if target_distance < self.IA_target_distance_fight:
                            self.IA_flag_go_to_target = False
                            autopilot.set_autopilot_altitude(td.target_altitude)
                        else:
                            if not self.IA_flag_go_to_target:
                                self.IA_flag_go_to_target = True
                                aircraft.set_thrust_level(1)
                                aircraft.activate_post_combustion()
                            autopilot.set_autopilot_altitude((td.target_altitude - alt) / 10 + alt)
                        if aircraft.playfield_distance > aircraft.playfield_safe_distance:
                            v = aircraft.parent_node.GetTransform().GetPos() * -1
                            self.IA_position_correction_heading = aircraft.calculate_heading(hg.Normalize(v * hg.Vec3(1, 0, 1)))
                            autopilot.set_autopilot_heading(self.IA_position_correction_heading)
                            self.IA_flag_position_correction = True

                        if alt < self.IA_altitude_min or alt > self.IA_altitude_max:
                            self.IA_flag_altitude_correction = True

                    md = aircraft.get_device("MissilesDevice")

                    if td.target_locked:
                        if md is not None:
                            if self.IA_fire_missile_cptr <= 0:
                                md.fire_missile()
                                self.IA_fire_missile_cptr = self.IA_fire_missiles_delay
                            else:
                                self.IA_fire_missile_cptr -= dts

                    if td.target_angle < self.IA_gun_angle and td.target_distance < self.IA_gun_distance_max:
                        n = aircraft.get_machinegun_count()
                        for i in range(n):
                            mgd = aircraft.get_device("MachineGunDevice_%02d" % i)
                            if mgd is not None and not mgd.is_activated():
                                mgd.activate()
                    else:
                        n = aircraft.get_machinegun_count()
                        for i in range(n):
                            mgd = aircraft.get_device("MachineGunDevice_%02d" % i)
                            if mgd is not None and mgd.is_activated():
                                mgd.deactivate()

                    flag_missiles_ok = False
                    if md is not None:
                        for missile in md.missiles:
                            if missile is not None:
                                flag_missiles_ok = True
                    else:
                        flag_missiles_ok = True

                    if not flag_missiles_ok or aircraft.get_num_bullets() == 200 or aircraft.health_level < 0.33:
                        self.IA_flag_landing_target_found = False
                        self.IA_command = AircraftIAControlDevice.IA_COM_LANDING
                        return

                else:
                    self.IA_flag_go_to_target = False
                    n = aircraft.get_machinegun_count()
                    for i in range(n):
                        mgd = aircraft.get_device("MachineGunDevice_%02d" % i)
                        if mgd is not None and mgd.is_activated():
                            mgd.deactivate()
                    self.IA_flag_landing_target_found = False
                    self.IA_command = AircraftIAControlDevice.IA_COM_LANDING
                    # self.set_autopilot_altitude(self.IA_cruising_altitude)
                    # self.set_autopilot_heading(0)
                # self.stop_machine_gun()

                if not self.IA_flag_go_to_target:
                    if aircraft.pitch_attitude > 15:
                        aircraft.set_thrust_level(1)
                        aircraft.activate_post_combustion()
                    elif -15 < aircraft.pitch_attitude < 15:
                        aircraft.deactivate_post_combustion()
                        aircraft.set_thrust_level(1)
                    else:
                        aircraft.deactivate_post_combustion()
                        aircraft.set_thrust_level(0.5)

    def controlled_device_hitted(self):
        aircraft = self.machine
        td = aircraft.get_device("TargettingDevice")
        offenders = []
        for target_id, target in enumerate(td.targets):
            td_t = target.get_device("TargettingDevice")
            if td_t is not None:
                offender_target = td_t.get_target()
                if offender_target == aircraft:
                    offenders.append([target_id, hg.Len(target.get_parent_node().GetTransform().GetPos() - aircraft.parent_node.GetTransform().GetPos())])
        if len(offenders) > 0:
            if len(offenders) > 1:
                offenders.sort(key=lambda p: p[1])
            td.set_target_id(offenders[0][0])

    # =============================== Keyboard commands ====================================

    def activate_user_control(self, value):
        if ControlDevice.devices[self.control_mode].Pressed(value["id"]):
            uctrl = self.machine.get_device("UserControlDevice")
            if uctrl is not None:
                self.deactivate()
                uctrl.activate()

    # ====================================================================================

    def update_cm_keyboard(self, dts):
        im = self.inputs_mapping["AircraftIAInputsMapping"][self.control_mode]
        for cmd, input_code in im.items():
            if cmd in self.commands and input_code != "":
                self.commands[cmd]({"id": input_code})

    def update_cm_joystick(self, dts):
        im = self.inputs_mapping["AircraftIAInputsMapping"][self.control_mode]
        for cmd, input_name in im.items():
            if cmd in self.commands and input_name != "":
                i_def = ControlDevice.device_configurations[self.control_mode][input_name]
                self.commands[cmd](i_def)

    def update_cm_mouse(self, dts):
        im = self.inputs_mapping["AircraftIAInputsMapping"][self.control_mode]

    def update(self, dts):
        if self.activated:
            if self.flag_user_control and self.machine.has_focus():
                if self.control_mode == ControlDevice.CM_KEYBOARD:
                    self.update_cm_keyboard(dts)
                elif self.control_mode == ControlDevice.CM_GAMEPAD:
                    self.update_cm_joystick(dts)
                elif self.control_mode == ControlDevice.CM_MOUSE:
                    self.update_cm_mouse(dts)

            self.update_controlled_device(dts)
