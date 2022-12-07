# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from math import radians, degrees, pi, sqrt, exp, floor, acos, asin
import MathsSupp as ms
from Particles import *
import tools
import Physics
from MachineDevice import *
import math
from overlays import *



#============================================================
#   Collision object
#============================================================

class Collisions_Object(MachineDevice):

    _instances = []
    framecount = 0   #Updated with Main.framecount
    timer = 0

    @classmethod
    def reset_collisions_objects(cls):
        cls._instances = []

    @classmethod
    def get_object_by_collision_node(cls, node: hg.Node):
        #nm0 = node.GetName()
        for col_obj in cls._instances:
            nds = col_obj.get_collision_nodes()
            if len(nds) > 0:
                for nd in nds:
                    #nm = nd.GetName()
                    if node.GetUid() == nd.GetUid():
                        return col_obj
        return None

    def __init__(self, name):
        MachineDevice.__init__(self, name, None, True)
        self.collision_nodes = []
        Collisions_Object._instances.append(self)
        self.instance_id = len(Collisions_Object._instances) - 1

        self.event_listeners = []   #list of functions used to listen events - Current lestenable events : "hit"
                                    # listener prototype: listener(str event_name, dict parameters)

    def get_collision_nodes(self):
        return self.collision_nodes

    def test_collision(self, nd: hg.Node):
        if len(self.collision_nodes) > 0:
            for ndt in self.collision_nodes:
                if nd == ndt: return True
        return False
    
    def add_listener(self, listener_call_back):
        self.event_listeners.append(listener_call_back)

    def hit(self, value, position):
        for listener in self.event_listeners:
            listener("hit",{"value":value, "position": position, "timestamp": Collisions_Object.timer}) # ??? position or hg.Vec3(position) ???


# =====================================================================================================
#                                  Animated model
# =====================================================================================================
class AnimatedModel(Collisions_Object):

    def __init__(self, name, model_name, scene, pipeline_ressource: hg.PipelineResources, instance_scene_name):
        Collisions_Object.__init__(self, name)
        self.commands.update({"SET_CURRENT_PILOT": self.set_current_pilot})
        self.model_name = model_name
        self.scene = scene
        self.res = pipeline_ressource

        self.parent_node, f = hg.CreateInstanceFromAssets(scene, hg.TranslationMat4(hg.Vec3(0, 0, 0)), instance_scene_name, pipeline_ressource, hg.GetForwardPipelineInfo())

        self.parent_node.SetName(self.name)
        self.remove_dummies_objects()

        # Pilots for cocpit view
        self.pilots = self.get_pilots_slots()
        self.current_pilot = 0
        self.set_current_pilot(1)

        # Mobile parts:
        self.parts = {}

    def destroy_particles(self):
        pass

    def setup_particles(self):
        pass

    def reset(self):
        Collisions_Object.reset(self)
        self.set_current_pilot(1)

    def show_objects(self):
        sv = self.parent_node.GetInstanceSceneView()
        nodes = sv.GetNodes(self.scene)
        for i in range(nodes.size()):
            nd = nodes.at(i)
            if nd.HasObject():
                nd.Enable()

    def hide_objects(self):
        sv = self.parent_node.GetInstanceSceneView()
        nodes = sv.GetNodes(self.scene)
        for i in range(nodes.size()):
            nd = nodes.at(i)
            if nd.HasObject():
                nd.Disable()

    def destroy_nodes(self):
        self.scene.DestroyNode(self.parent_node)
        self.parent_node = None
        hg.SceneGarbageCollectSystems(self.scene)

    def get_slots(self, slots_name):
        slots_names = []
        scene_view = self.parent_node.GetInstanceSceneView()
        nodes = scene_view.GetNodes(self.scene)
        n = nodes.size()
        if n == 0:
            raise OSError("ERROR - Empty Instance '" + self.name + "'- Unloaded scene ?")
        for i in range(nodes.size()):
            nd = nodes.at(i)
            nm = nd.GetName()
            if slots_name in nm:
                slots_names.append(nm)
        if len(slots_name) == 0:
            return None
        slots_names.sort()
        slots = []
        for nm in slots_names:
            slots.append(scene_view.GetNode(self.scene, nm))
        return slots

    #  -------- Pilots handler --------------------

    def set_current_pilot(self, pilot_id):
        np = len(self.pilots)
        if np == 0:
            pilot_id = 0
        elif pilot_id > np:
            pilot_id = min(1, len(self.pilots))
        self.current_pilot = pilot_id

    def update_vr_head(self, pilot_id, vr_head_origin: hg.Mat4):
        if pilot_id == 0:
            return
        pilot_id = min(pilot_id, len(self.pilots))
        head_node = self.pilots[pilot_id - 1]["head"]
        v = self.pilots[pilot_id - 1]["nativ_head_position"] - hg.GetT(vr_head_origin)
        head_node.GetTransform().SetPos(v)

    def get_current_pilot_head(self):
        if self.pilots is None or len(self.pilots) == 0:
            return None
        else:
            if self.current_pilot == 0:
                return self.parent_node
            else:
                return self.pilots[self.current_pilot - 1]["head"]

    def get_pilots_slots(self):
        pilots_bodies = self.get_slots("pilote_body")
        heads = self.get_slots("pilote_head")
        pilots = []
        for i in range(len(pilots_bodies)):
            head_pos0 = heads[i].GetTransform().GetPos()
            pilots.append({"body": pilots_bodies[i], "head": heads[i], "nativ_head_position": head_pos0})
        return pilots

    def get_pilots(self):
        return self.pilots

    # ----------- Animations handler----------------------

    def get_animation(self, animation_name):
        return self.parent_node.GetInstanceSceneAnim(animation_name)

    # ---------------------------------------------------

    def get_position(self):
        return self.parent_node.GetTransform().GetPos()

    def get_Euler(self):
        return self.parent_node.GetTransform().GetRot()

    def reset_matrix(self, pos, rot):
        self.parent_node.GetTransform().SetPos(pos)
        self.parent_node.GetTransform().SetRot(rot)
        mat = hg.TransformationMat4(pos, rot)
        self.parent_node.GetTransform().SetWorld(mat)

    def decompose_matrix(self, matrix=None):
        if matrix is None:
            matrix = self.parent_node.GetTransform().GetWorld()
        aX = hg.GetX(matrix)
        aY = hg.GetY(matrix)
        aZ = hg.GetZ(matrix)
        pos = hg.GetT(matrix)
        rot = hg.GetR(matrix)
        return matrix, pos, rot, aX, aY, aZ

    def get_X_axis(self):
        return hg.GetX((self.parent_node.GetTransform().GetWorld()))

    def get_Y_axis(self):
        return hg.GetY((self.parent_node.GetTransform().GetWorld()))

    def get_Z_axis(self):
        return hg.GetZ((self.parent_node.GetTransform().GetWorld()))

    def define_mobile_parts(self, mobile_parts_definitions):
        for mpd in mobile_parts_definitions:
            self.add_mobile_part(mpd[0], mpd[1], mpd[2], mpd[3], mpd[4], mpd[5])

    def add_mobile_part(self, name, angle_min, angle_max, angle_0, node_name, rotation_axis_id):
        sv = self.parent_node.GetInstanceSceneView()
        node = sv.GetNode(self.scene, node_name)
        if angle_0 is None:
            rot = node.GetTransform().GetRot()
            if rotation_axis_id == "X":
                angle_0 = degrees(rot.x)
            elif rotation_axis_id == "Y":
                angle_0 = degrees(rot.y)
            elif rotation_axis_id == "Z":
                angle_0 = degrees(rot.z)
            angle_min += angle_0
            angle_max += angle_0
        self.parts[name] = {"angle_min": angle_min, "angle_max": angle_max, "angle_0": angle_0, "level": 0, "node": node, "part_axis": rotation_axis_id}

    def get_mobile_parts(self):
        return self.parts

    def remove_objects_by_name_pattern(self, name_pattern):
        sv = self.parent_node.GetInstanceSceneView()
        nodes = sv.GetNodes(self.scene)
        for i in range(nodes.size()):
            nd = nodes.at(i)
            nm = nd.GetName()
            if name_pattern in nm:
                if nd.HasObject():
                    nd.RemoveObject()

    def remove_collision_boxes_objects(self):
        self.remove_objects_by_name_pattern("col_shape")

    def remove_dummies_objects(self):
        # RATIONALISER #
        self.remove_objects_by_name_pattern("dummy")
        self.remove_objects_by_name_pattern("slot")
        self.remove_objects_by_name_pattern("pilot_head")
        self.remove_objects_by_name_pattern("pilot_body")

    def get_parent_node(self):
        return self.parent_node

    def enable_nodes(self):
        nodes = self.parent_node.GetInstanceSceneView().GetNodes(self.scene)
        for i in range(nodes.size()):
            nodes.at(i).Enable()

    def disable_nodes(self):
        nodes = self.parent_node.GetInstanceSceneView().GetNodes(self.scene)
        for i in range(nodes.size()):
            nodes.at(i).Disable()

    def copy_mobile_parts_levels(self, src_parts):
        for lbl in self.parts.keys():
            if lbl in src_parts:
                part_main = src_parts[lbl]
                part = self.parts[lbl]
                part["level"] = part_main["level"]

    def update_mobile_parts(self, dts):
        for part in self.parts.values():
            if part["level"] < 0:
                angle = part["angle_0"] * (1 + part["level"]) + part["angle_min"] * -part["level"]
            else:
                angle = part["angle_0"] * (1 - part["level"]) + part["angle_max"] * part["level"]

            trans = part["node"].GetTransform()
            rot = trans.GetRot()

            if part["part_axis"] == "X":
                rot.x = radians(angle)
            elif part["part_axis"] == "Y":
                rot.y = radians(angle)
            elif part["part_axis"] == "Z":
                rot.z = radians(angle)

            trans.SetRot(rot)


# =====================================================================================================
#                                  Destroyable machine
# =====================================================================================================

class Destroyable_Machine(AnimatedModel):

    TYPE_GROUND = 0
    TYPE_SHIP = 1
    TYPE_AIRCRAFT = 2
    TYPE_MISSILE = 3
    TYPE_LANDVEHICLE = 4
    TYPE_MISSILE_LAUNCHER = 5


    flag_activate_particles = True
    flag_update_particles = True
    playfield_max_distance = 50000
    playfield_safe_distance = 40000

    types_labels = ["GROUND", "SHIP", "AICRAFT", "MISSILE", "LANDVEHICLE", "MISSILE_LAUNCHER"]
    update_list = []
    machines_list = []
    machines_items = {}

    @classmethod
    def get_machine_by_node(cls, node:hg.Node):
        collision_object = cls.get_object_by_collision_node(node)
        if collision_object.name in cls.machines_items:
            return cls.machines_items[collision_object.name]
        else:
            return None

    @classmethod
    def reset_machines(cls):
        Collisions_Object.reset_collisions_objects()
        cls.update_list = []

    @classmethod
    def set_activate_particles(cls, flag):
        if flag != cls.flag_activate_particles:
            if flag:
                for machine in cls._instances:
                    machine.setup_particles()
            else:
                for machine in cls._instances:
                    machine.destroy_particles()
        cls.flag_activate_particles = flag

    def __init__(self, name, model_name, scene: hg.Scene, scene_physics, pipeline_ressource: hg.PipelineResources, instance_scene_name, type, nationality, start_position=None, start_rotation=None):

        AnimatedModel.__init__(self, name, model_name, scene, pipeline_ressource, instance_scene_name)

        self.flag_focus = False

        self.hits = []

        self.playfield_distance = 0

        self.commands.update({"SET_HEALTH_LEVEL": self.set_health_level})

        self.start_position = start_position
        self.start_rotation = start_rotation

        self.flag_custom_physics_mode = False
        self.custom_matrix = None
        self.custom_v_move = None

        self.flag_display_linear_speed = False
        self.flag_display_vertical_speed = False
        self.flag_display_horizontal_speed = False

        self.terrain_altitude = 0
        self.terrain_normale = None

        self.type = type

        self.scene_physics = scene_physics
        self.flag_destroyed = False
        self.flag_crashed = False
        self.nationality = nationality

        self.health_level = 1
        self.wreck = False
        self.v_move = hg.Vec3(0, 0, 0)

        # Linear acceleration:
        self.linear_acceleration = 0
        self.linear_speeds = [0] * 10
        self.linear_spd_rec_cnt = 0

        # Physic Wakeup check:
        self.pos_prec = hg.Vec3(0, 0, 0)
        self.rot_prec = hg.Vec3(0, 0, 0)
        self.flag_moving = False

        self.bottom_height = 1

        # Vertex model:
        self.vs_decl = hg.VertexLayout()
        self.vs_decl.Begin()
        self.vs_decl.Add(hg.A_Position, 3, hg.AT_Float)
        self.vs_decl.Add(hg.A_Normal, 3, hg.AT_Uint8, True, True)
        self.vs_decl.End()
        self.ground_node_collision = None
        # Used by spatialized sound:
        self.view_v_move = hg.Vec3(0, 0, 0)
        self.mat_view = None
        self.mat_view_prec = None

        # Views parameters
        self.camera_track_distance = 40
        self.camera_follow_distance = 40

        # Devices
        self.devices = {}

        # Views parameters
        self.camera_track_distance = 40
        self.camera_follow_distance = 40
        self.camera_tactical_distance = 40
        self.camera_tactical_min_altitude = 10

        # Bounds positions used by collisions raycasts:
        self.collision_boxes = []
        self.bounding_boxe = None
        self.bound_front = hg.Vec3(0, 0, 0)
        self.bound_back = hg.Vec3(0, 0, 0)
        self.bound_up = hg.Vec3(0, 0, 0)
        self.bound_down = hg.Vec3(0, 0, 0)
        self.bound_left = hg.Vec3(0, 0, 0)
        self.bound_right = hg.Vec3(0, 0, 0)

    #============= Devices

    def add_device(self, device: MachineDevice):
        self.devices[device.name] = device

    def remove_device(self, device_name):
        if device_name in self.devices:
            return self.devices.pop(device_name)
        return None

    def update_devices(self, dts):
        for name, device in self.devices.items():
            device.update(dts)

    def get_device(self, device_name):
        if device_name in self.devices:
            return self.devices[device_name]
        else:
            return None

    #==============

    def set_focus(self):
        for machine in self.machines_list:
            if machine.flag_focus:
                machine.flag_focus = False
                break
        self.flag_focus = True

    def has_focus(self):
        return self.flag_focus

    #==============

    def reset(self, position=None, rotation=None):
        AnimatedModel.reset(self)
        self.hits = []
        if position is not None:
            self.start_position = position
        if rotation is not None:
            self.start_rotation = rotation

        self.set_custom_physics_mode(False)

        self.reset_matrix(self.start_position, self.start_rotation)

    def add_to_update_list(self):
        if self not in Destroyable_Machine.update_list:
            Destroyable_Machine.update_list.append(self)

    def remove_from_update_list(self):
        for i in range(len(Destroyable_Machine.update_list)):
            dm = Destroyable_Machine.update_list
            if dm == self:
                Destroyable_Machine.update_list.pop(i)
                break

    def update_view_v_move(self, dts):
        if self.mat_view_prec is None or self.mat_view is None:
            self.view_v_move.x, self.view_v_move.y, self.view_v_move.z = 0, 0, 0
        else:
            self.view_v_move = (hg.GetT(self.mat_view) - hg.GetT(self.mat_view_prec)) / dts

    def calculate_view_matrix(self, camera):
        cam_mat = camera.GetTransform().GetWorld()
        cam_mat_view = hg.InverseFast(cam_mat)
        self.mat_view_prec = self.mat_view
        self.mat_view = cam_mat_view * self.parent_node.GetTransform().GetWorld()


    def hit(self, value, position):
        Collisions_Object.hit(self, value, position)
        if not self.wreck:
            self.set_health_level(self.health_level - value)

    def destroy_nodes(self):
        AnimatedModel.destroy_nodes(self)
        for nd in self.collision_nodes:
            self.scene.DestroyNode(nd)
        self.collision_nodes = []
        hg.SceneGarbageCollectSystems(self.scene, self.scene_physics)

    def setup_collisions(self):

        self.scene.Update(1000)
        self.collision_nodes = []
        self.collision_boxes = []

        nodes = self.parent_node.GetInstanceSceneView().GetNodes(self.scene)
        n = nodes.size()
        for i in range(n):
            nd = nodes.at(i)
            nm = nd.GetName()
            if "col_shape" in nm:
                f, mm = nd.GetObject().GetMinMax(self.res)
                size = (mm.mx - mm.mn)
                mdl = hg.CreateCubeModel(self.vs_decl, size.x, size.y, size.z)
                ref = self.res.AddModel('col_shape' + str(i), mdl)
                pos = nd.GetTransform().GetPos()
                rot = nd.GetTransform().GetRot()
                parent = nd.GetTransform().GetParent()
                material = nd.GetObject().GetMaterial(0)
                new_node_local_matrix = hg.TransformationMat4(pos, rot)
                new_node = hg.CreatePhysicCube(self.scene, hg.Vec3(size), new_node_local_matrix, ref, [material], 0)
                new_node.SetName(self.name + "_ColBox")
                new_node.GetRigidBody().SetType(hg.RBT_Kinematic)
                new_node.GetTransform().SetParent(parent)
                new_node.RemoveObject()
                self.scene.DestroyNode(nd)
                self.collision_nodes.append(new_node)
                self.collision_boxes.append({"node": new_node, "size": hg.Vec3(size)})
                self.scene_physics.NodeCreatePhysicsFromAssets(new_node)
        hg.SceneGarbageCollectSystems(self.scene, self.scene_physics)

    def setup_bounds_positions(self):
        self.scene.Update(1000)
        if len(self.collision_boxes) == 0:
            # Bounds from geometries
            self.setup_objects_bounds_positions()
        else:
            # Bounds from collision shapes
            mdl_mat = hg.InverseFast(self.parent_node.GetTransform().GetWorld())
            bounds = None

            for cb in self.collision_boxes:
                nd = cb["node"]
                mat = mdl_mat * nd.GetTransform().GetWorld()
                size = cb["size"] * 0.5
                bounding_box = [hg.Vec3(-size.x, -size.y, -size.z), hg.Vec3(-size.x, size.y, -size.z), hg.Vec3(size.x, size.y, -size.z), hg.Vec3(size.x, -size.y, -size.z),
                                hg.Vec3(-size.x, -size.y, size.z), hg.Vec3(-size.x, size.y, size.z), hg.Vec3(size.x, size.y, size.z), hg.Vec3(size.x, -size.y, size.z)]

                for pt in bounding_box:
                    pt = mat * pt
                    if bounds is None:
                        bounds = [pt.x, pt.x, pt.y, pt.y, pt.z, pt.z]
                    else:
                        def update_bounds(p, bidx):
                            if p < bounds[bidx]:
                                bounds[bidx] = p
                            elif p > bounds[bidx + 1]:
                                bounds[bidx + 1] = p

                        update_bounds(pt.x, 0)
                        update_bounds(pt.y, 2)
                        update_bounds(pt.z, 4)

            if bounds is not None:
                self.bounding_boxe = [hg.Vec3(bounds[0], bounds[2], bounds[4]), hg.Vec3(bounds[0], bounds[3], bounds[4]), hg.Vec3(bounds[1], bounds[3], bounds[4]), hg.Vec3(bounds[1], bounds[2], bounds[4]),
                                      hg.Vec3(bounds[0], bounds[2], bounds[5]), hg.Vec3(bounds[0], bounds[3], bounds[5]), hg.Vec3(bounds[1], bounds[3], bounds[5]), hg.Vec3(bounds[1], bounds[2], bounds[5])]

                def compute_average(id0, id1, id2, id3):
                    return (self.bounding_boxe[id0] + self.bounding_boxe[id1] + self.bounding_boxe[id2] + self.bounding_boxe[id3]) * 0.25

                self.bound_front = compute_average(4, 5, 6, 7)
                self.bound_back = compute_average(0, 1, 2, 3)
                self.bound_up = compute_average(1, 2, 5, 6)
                self.bound_down = compute_average(0, 3, 4, 7)
                self.bound_left = compute_average(0, 1, 4, 5)
                self.bound_right = compute_average(2, 3, 6, 7)

    def setup_objects_bounds_positions(self):
        #self.scene.Update(0)
        nodes = self.parent_node.GetInstanceSceneView().GetNodes(self.scene)
        n = nodes.size()
        mdl_mat = hg.InverseFast(self.parent_node.GetTransform().GetWorld())
        bounds = None

        for i in range(n):
            nd = nodes.at(i)
            if nd.HasObject():
                mat = nd.GetTransform().GetWorld() * mdl_mat
                f, mm = nd.GetObject().GetMinMax(self.res)
                bounding_box = [hg.Vec3(mm.mn.x, mm.mn.y, mm.mn.z), hg.Vec3(mm.mn.x, mm.mx.y, mm.mn.z), hg.Vec3(mm.mx.x, mm.mx.y, mm.mn.z), hg.Vec3(mm.mx.x, mm.mn.y, mm.mn.z),
                                hg.Vec3(mm.mn.x, mm.mn.y, mm.mx.z), hg.Vec3(mm.mn.x, mm.mx.y, mm.mx.z), hg.Vec3(mm.mx.x, mm.mx.y, mm.mx.z), hg.Vec3(mm.mx.x, mm.mn.y, mm.mx.z)]

                for pt in bounding_box:
                    pt = mat * pt
                    if bounds is None:
                        bounds = [pt.x, pt.x, pt.y, pt.y, pt.z, pt.z]
                    else:
                        def update_bounds(p, bidx):
                            if p < bounds[bidx]:
                                bounds[bidx] = p
                            elif p > bounds[bidx + 1]:
                                bounds[bidx + 1] = p

                        update_bounds(pt.x, 0)
                        update_bounds(pt.y, 2)
                        update_bounds(pt.z, 4)
        if bounds is not None:
            self.bounding_boxe = [hg.Vec3(bounds[0], bounds[2], bounds[4]), hg.Vec3(bounds[0], bounds[3], bounds[4]), hg.Vec3(bounds[1], bounds[3], bounds[4]), hg.Vec3(bounds[1], bounds[2], bounds[4]),
                            hg.Vec3(bounds[0], bounds[2], bounds[5]), hg.Vec3(bounds[0], bounds[3], bounds[5]), hg.Vec3(bounds[1], bounds[3], bounds[5]), hg.Vec3(bounds[1], bounds[2], bounds[5])]

            def compute_average(id0, id1, id2, id3):
                return (self.bounding_boxe[id0] + self.bounding_boxe[id1] + self.bounding_boxe[id2] + self.bounding_boxe[id3]) * 0.25

            self.bound_front = compute_average(4, 5, 6, 7)
            self.bound_back = compute_average(0, 1, 2, 3)
            self.bound_up = compute_average(1, 2, 5, 6)
            self.bound_down = compute_average(0, 3, 4, 7)
            self.bound_left = compute_average(0, 1, 4, 5)
            self.bound_right = compute_average(2, 3, 6, 7)

    def get_world_bounding_boxe(self):
        if self.bounding_boxe is not None:
            matrix = self.parent_node.GetTransform().GetWorld()
            bb = []
            for p in self.bounding_boxe:
                bb.append(matrix * p)
            return bb
        return None

    def get_health_level(self):
        return self.health_level

    def set_health_level(self, level):
        if not self.wreck:
            self.health_level = min(1, max(0, level))
        else:
            self.health_level = 0

    def setup_particles(self):
        pass

    def destroy_particles(self):
        pass

    def get_world_speed(self):
        sX = hg.Vec3.Right * (hg.Dot(hg.Vec3.Right, self.v_move))
        sZ = hg.Vec3.Front * (hg.Dot(hg.Vec3.Front, self.v_move))
        vs = hg.Dot(hg.Vec3.Up, self.v_move)
        hs = hg.Len(sX + sZ)
        return hs, vs

    def get_move_vector(self):
        return self.v_move

    def get_linear_speed(self):
        return hg.Len(self.v_move)

    def set_linear_speed(self, value):
        aZ = hg.GetZ(self.parent_node.GetTransform().GetWorld())
        self.v_move = aZ * value

    def get_altitude(self):
        return self.parent_node.GetTransform().GetPos().y

    def get_pitch_attitude(self):
        aZ = hg.GetZ(self.get_parent_node().GetTransform().GetWorld())
        horizontal_aZ = hg.Normalize(hg.Vec3(aZ.x, 0, aZ.z))
        pitch_attitude = degrees(acos(max(-1, min(1, hg.Dot(horizontal_aZ, aZ)))))
        if aZ.y < 0: pitch_attitude *= -1
        return pitch_attitude

    def get_roll_attitude(self):
        matrix = self.get_parent_node().GetTransform().GetWorld()
        aX = hg.GetX(matrix)
        aY = hg.GetY(matrix)
        aZ = hg.GetZ(matrix)
        if aY.y > 0:
            y_dir = 1
        else:
            y_dir = -1
        horizontal_aZ = hg.Normalize(hg.Vec3(aZ.x, 0, aZ.z))
        horizontal_aX = hg.Cross(hg.Vec3.Up, horizontal_aZ) * y_dir
        roll_attitude = degrees(acos(max(-1, min(1, hg.Dot(horizontal_aX, aX)))))
        if aX.y < 0: roll_attitude *= -1
        return roll_attitude

    def calculate_heading(self, h_dir: hg.Vec3):
        heading = degrees(acos(max(-1, min(1, hg.Dot(h_dir, hg.Vec3.Front)))))
        if h_dir.x < 0: heading = 360 - heading
        return heading

    def get_heading(self):
        aZ = hg.GetZ(self.get_parent_node().GetTransform().GetWorld())
        horizontal_aZ = hg.Normalize(hg.Vec3(aZ.x, 0, aZ.z))
        return self.calculate_heading(horizontal_aZ)

    def set_custom_physics_mode(self, flag: bool):
        if not flag:
            self.custom_matrix = None
            self.custom_v_move = None
        self.flag_custom_physics_mode = flag

    def get_custom_physics_mode(self):
        return self.flag_custom_physics_mode

    def set_custom_kinetics(self, matrix: hg.Mat4, v_move: hg.Vec3):
        self.custom_matrix = matrix
        self.custom_v_move = v_move

    def update_collisions(self, matrix, dts):
        mat, pos, rot, aX, aY, aZ = self.decompose_matrix(matrix)

        collisions_raycasts = [
            {"name": "down", "position": self.bound_down, "direction": hg.Vec3(0, -4, 0)}
        ]
        ray_hits, self.terrain_altitude, self.terrain_normale = Physics.update_collisions(mat, self, collisions_raycasts)

        alt = self.terrain_altitude
        bottom_alt = self.bottom_height
        self.ground_node_collision = None

        for collision in ray_hits:
            if collision["name"] == "down":
                if len(collision["hits"]) > 0:
                    hit = collision["hits"][0]
                    self.ground_node_collision = hit.node
                    alt = hit.P.y + bottom_alt

        if self.flag_crashed:
            pos.y = alt
            self.v_move *= pow(0.9, 60 * dts)

        else:
            if pos.y < alt:
                    pos.y += (alt - pos.y) * 0.1
                    if self.v_move.y < 0: self.v_move.y *= pow(0.8, 60 * dts)

        return hg.TransformationMat4(pos, rot)

    def rec_linear_speed(self):
        self.linear_speeds[self.linear_spd_rec_cnt] = hg.Len(self.v_move)
        self.linear_spd_rec_cnt = (self.linear_spd_rec_cnt + 1) % len(self.linear_speeds)

    def update_linear_acceleration(self):
        m = 0
        for s in self.linear_speeds:
            m += s
        m /= len(self.linear_speeds)
        self.linear_acceleration = hg.Len(self.v_move) - m

    def get_linear_acceleration(self):
        return self.linear_acceleration

    def update_feedbacks(self, dts):
        pass

    def update_physics_wakeup(self):
        for nd in self.collision_nodes:
            self.scene_physics.NodeWake(nd)
        return
        trans = self.get_parent_node().GetTransform()
        pos = trans.GetPos()
        rot = trans.GetRot()
        rv = rot - self.rot_prec
        v = hg.Len(pos - self.pos_prec)
        if self.flag_moving:
            if v < 0.1 and abs(rv.x) < 0.01 and abs(rv.y) < 0.01 and abs(rv.z) < 0.01:
                self.flag_moving = False
            else:
                self.pos_prec.x, self.pos_prec.y, self.pos_prec.z = pos.x, pos.y, pos.z
                self.rot_prec.x, self.rot_prec.y, self.rot_prec.z = rot.x, rot.y, rot.z
        else:
            if v > 0.1 or abs(rv.x) > 0.001 or abs(rv.y) > 0.001 or abs(rv.z) > 0.001:
                self.flag_moving = True
                if self.type == Destroyable_Machine.TYPE_AIRCRAFT:
                    print("YOUPLA")
                for nd in self.collision_nodes:
                    self.scene_physics.NodeWake(nd)


    def get_physics_parameters(self):
        return {"v_move": self.v_move,
                "thrust_level": 0,
                "thrust_force": 0,
                "lift_force": 0,
                "drag_coefficients": hg.Vec3(0, 0, 0),
                "health_wreck_factor": 1,
                "angular_levels": hg.Vec3(0, 0, 0),
                "angular_frictions": hg.Vec3(0, 0, 0),
                "speed_ceiling": 0,
                "flag_easy_steering": False
                }

    def update_kinetics(self, dts):
        if self.activated:
            if self.custom_matrix is not None:
                matrix = self.custom_matrix
            else:
                matrix = self.get_parent_node().GetTransform().GetWorld()
            if self.custom_v_move is not None:
                v_move = self.custom_v_move
            else:
                v_move = self.v_move

            if not self.flag_crashed:
                self.v_move = v_move

            # Apply displacement vector and gravity
            if not self.flag_custom_physics_mode:
                self.v_move += Physics.F_gravity * dts
                pos = hg.GetT(matrix)
                pos += self.v_move * dts
                hg.SetT(matrix, pos)

            # Collisions
            mat = self.update_collisions(matrix, dts)

            mat, pos, rot, aX, aY, aZ = self.decompose_matrix(mat)

            self.parent_node.GetTransform().SetPos(pos)
            self.parent_node.GetTransform().SetRot(rot)

            self.rec_linear_speed()
            self.update_linear_acceleration()

            self.update_devices(dts)

            self.update_mobile_parts(dts)
            self.update_feedbacks(dts)

    def rearm(self):
        pass

# =====================================================================================================
#                                  Missile
# =====================================================================================================

class Missile(Destroyable_Machine):
    num_smoke_parts = 17

    def __init__(self, name, model_name, nationality, scene: hg.Scene, scene_physics, pipeline_ressource: hg.PipelineResources, instance_scene_name,
                 smoke_color: hg.Color = hg.Color.White, start_position=hg.Vec3.Zero, start_rotation=hg.Vec3.Zero):

        self.flag_user_control = False

        self.angular_levels = hg.Vec3(0, 0, 0)

        self.start_position = start_position
        self.start_rotation = start_rotation
        self.smoke_color = smoke_color
        self.smoke_color_label = "uColor"

        Destroyable_Machine.__init__(self, name, model_name, scene, scene_physics, pipeline_ressource, instance_scene_name, Destroyable_Machine.TYPE_MISSILE, nationality)
        self.commands.update({"SET_ROLL_LEVEL": self.set_roll_level,
                              "SET_PITCH_LEVEL": self.set_pitch_level,
                              "SET_YAW_LEVEL": self.set_yaw_level
                              })

        self.target = None
        self.target_collision_test_distance_max = 100

        # Missile constantes:
        self.thrust_force = 100
        self.smoke_parts_distance = 1.44374
        self.drag_coeff = hg.Vec3(0.37, 0.37, 0.0003)
        self.angular_frictions = hg.Vec3(0.0001, 0.0001, 0.0001)  # pitch, yaw, roll
        self.life_delay = 20
        self.smoke_delay = 1
        self.speed_ceiling = 4000

        self.smoke_time = 0
        self.life_cptr = 0

        self.engines_slots = self.get_engines_slots()

        # Feed-backs and particles:
        self.smoke = []
        self.explode = None
        if len(self.engines_slots) > 0:
            if Destroyable_Machine.flag_activate_particles:
                self.setup_particles()

        self.flag_armed = True

        self.setup_bounds_positions()

        # UserControlDevice used for debugging
        self.add_device(MissileUserControlDevice("MissileUserControlDevice", self))

    def set_roll_level(self, value):
        pass

    def set_pitch_level(self, value):
        pass

    def set_yaw_level(self, value):
        pass

    def get_valid_targets_list(self):
        targets = []
        for machine in Destroyable_Machine.machines_list:
            if machine.nationality != self.nationality and (machine.type == Destroyable_Machine.TYPE_AIRCRAFT):
                targets.append(machine)
        return targets

    def set_life_delay(self, life_delay):
        self.life_delay = life_delay

    def is_armed(self):
        return self.flag_armed

    def destroy(self):
        if not self.flag_destroyed:
            self.get_parent_node().GetTransform().ClearParent()
            self.destroy_particles()
            self.destroy_nodes()
            self.flag_destroyed = True
            self.remove_from_update_list()
        # scene.GarbageCollect()

    def setup_particles(self):
        for i in range(Missile.num_smoke_parts):
            node = tools.duplicate_node_object(self.scene, self.scene.GetNode("enemymissile_smoke" + "." + str(i)), self.name + ".smoke_" + str(i))
            self.smoke.append({"node":node, "alpha": 0})
        self.set_smoke_color(self.smoke_color)

        if self.explode is not None:
            self.destroy_particles()
        self.explode = ParticlesEngine(self.name + ".explode", self.scene, "feed_back_explode",
                                       50, hg.Vec3(5, 5, 5), hg.Vec3(100, 100, 100), 180, 0)
        self.explode.delay_range = hg.Vec2(1, 2)
        self.explode.flow = 0
        self.explode.scale_range = hg.Vec2(0.25, 2)
        self.explode.start_speed_range = hg.Vec2(0, 100)
        self.explode.colors = [hg.Color(1., 1., 1., 1), hg.Color(1., 0., 0., 0.5), hg.Color(0., 0., 0., 0.25),
                               hg.Color(0., 0., 0., 0.125), hg.Color(0., 0., 0., 0.0)]
        self.explode.set_rot_range(radians(20), radians(50), radians(10), radians(45), radians(5), radians(15))
        self.explode.gravity = hg.Vec3(0, -9.8, 0)
        self.explode.loop = False

    def destroy_particles(self):
        if self.explode is not None:
            self.explode.destroy()
            self.explode = None
        for p in self.smoke:
            self.scene.DestroyNode(p["node"])
            self.scene.GarbageCollect()
        self.smoke = []

    def activate(self):
        if self.explode is not None:
            self.explode.activate()
        for p in self.smoke:
            p["node"].Enable()
        self.enable_nodes()
        Destroyable_Machine.activate(self)

    def deactivate(self):
        # CONFUSION - ADD HIDE() Function
        Destroyable_Machine.deactivate(self)
        self.disable_nodes()
        for p in self.smoke:
            p["node"].Disable()
        if self.explode is not None:
            self.explode.deactivate()
        self.remove_from_update_list()

    def get_engines_slots(self):
        return self.get_slots("engine_slot")

    def reset(self, position=None, rotation=None):

        # Don't call parent's function, World Matrix mustn't be reseted !
        #Destroyable_Machine.reset(self, position, rotation)
        self.hits = []

        if position is not None:
            self.start_position = position
        if rotation is not None:
            self.start_rotation = rotation

        self.parent_node.GetTransform().SetPos(self.start_position)
        self.parent_node.GetTransform().SetRot(self.start_rotation)

        self.set_custom_physics_mode(False)

        self.smoke_time = 0

        self.remove_from_update_list()
        self.deactivate()
        for p in self.smoke:
            p["node"].GetTransform().SetPos(hg.Vec3(0, 0, 0))
            p["node"].Enable()
        if self.explode is not None:
            self.explode.reset()
            self.explode.flow = 0
        self.enable_nodes()
        self.wreck = False
        self.v_move *= 0
        self.life_cptr = 0

    def set_smoke_color(self, color: hg.Color):
        self.smoke_color = color
        for p in self.smoke:
            p["node"].GetTransform().SetPos(hg.Vec3(0, 0, 0))
            hg.SetMaterialValue(p["node"].GetObject().GetMaterial(0), self.smoke_color_label, hg.Vec4(self.smoke_color.r, self.smoke_color.g, self.smoke_color.b, self.smoke_color.a))

    def get_target_id(self):
        if self.target is not None:
            return self.target.name
        else:
            return ""

    def set_target(self, target: Destroyable_Machine):
        if target is not None and target.nationality != self.nationality:
            self.target = target
        else:
            self.target = None

    def set_target_by_name(self, target_name):
        self.target = None
        if target_name != "":
            for target in Destroyable_Machine.machines_list:
                if target.name == target_name:
                    self.set_target(target)
                    break


    def start(self, target: Destroyable_Machine, v0: hg.Vec3):
        if not self.activated:
            self.smoke_time = 0
            self.life_cptr = 0
            self.set_target(target)
            self.v_move = hg.Vec3(v0)
            self.activated = True
            self.add_to_update_list()
            pos = self.parent_node.GetTransform().GetPos()
            for p in self.smoke:
                p["node"].Enable()
                p["node"].GetTransform().SetPos(pos)

    def update_smoke(self, target_point: hg.Vec3, dts):
        spd = self.get_linear_speed() * 0.033
        t = min(1, abs(self.smoke_time) / self.smoke_delay)
        new_t = self.smoke_time + dts
        if self.smoke_time < 0 and new_t >= 0:
            # pos0=hg.Vec3(0,-1000,0)
            for i in range(len(self.smoke)):
                node = self.smoke[i]["node"]
                node.Disable()  # GetTransform().SetPos(pos0)
            self.smoke_time = new_t
        else:
            self.smoke_time = new_t
            n = len(self.smoke)
            color_end = self.smoke_color * t + hg.Color(1., 1., 1., 0.) * (1 - t)
            for i in range(n):
                node = self.smoke[i]["node"]

                if self.wreck:
                     alpha = self.smoke[i]["alpha"] * (1 - i / n) * t
                else:
                    mat = node.GetTransform().GetWorld()
                    hg.SetScale(mat, hg.Vec3(1, 1, 1))
                    pos = hg.GetT(mat)
                    v = target_point - pos
                    smoke_part_spd = hg.Len(v)
                    dir = hg.Normalize(v)
                    # Position:
                    if smoke_part_spd > self.smoke_parts_distance * spd:
                        pos = target_point - dir * self.smoke_parts_distance * spd
                        node.GetTransform().SetPos(hg.Vec3(pos))
                        alpha = color_end.a * (1 - i / n)
                    else:
                        alpha = 0
                    
                    self.smoke[i]["alpha"] = alpha
                    # node.Enable()
                    # else:
                    # node.Disable()
                    # Orientation:
                    aZ = hg.Normalize(hg.GetZ(mat))
                    axis_rot = hg.Cross(aZ, dir)
                    angle = hg.Len(axis_rot)
                    if angle > 0.001:
                        # Rotation matrix:
                        ay = hg.Normalize(axis_rot)
                        rot_mat = hg.Mat3(hg.Cross(ay, dir), ay, dir)
                        node.GetTransform().SetRot(hg.ToEuler(rot_mat))
                    node.GetTransform().SetScale(hg.Vec3(1, 1, spd))
                    target_point = pos

                hg.SetMaterialValue(node.GetObject().GetMaterial(0), self.smoke_color_label, hg.Vec4(color_end.r, color_end.g, color_end.b, alpha))

               

    def get_hit_damages(self):
        raise NotImplementedError

    def update_collisions(self, matrix, dts):

        smoke_start_pos = hg.GetT(self.engines_slots[0].GetTransform().GetWorld())

        collisions_raycasts = []
        if self.target is not None:
            distance = hg.Len(self.target.get_parent_node().GetTransform().GetPos() - hg.GetT(matrix))
            if distance < self.target_collision_test_distance_max:


                #debug
                """
                if not self.flag_user_control:
                    self.flag_user_control = True
                    ucd = self.get_device("MissileUserControlDevice")
                    if ucd is not None:
                        ucd.activate()
                        ucd.pos_mem = hg.GetT(matrix)
                """

                #Ajouter des slots pour les points de départ des raycasts
                raycast_length = hg.Len(self.v_move) #50
                collisions_raycasts.append({"name": "front", "position": self.bound_front + hg.Vec3(0, 0, 0.4), "direction": hg.Vec3(0, 0, raycast_length)}) #)})

            """
            else:
                # debug
                if self.flag_user_control:
                    self.flag_user_control = False
                    ucd = self.get_device("MissileUserControlDevice")
                    if ucd is not None:
                        ucd.deactivate()
            """



        rays_hits, self.terrain_altitude, self.terrain_normale = Physics.update_collisions(matrix, self, collisions_raycasts)

        pos = hg.GetT(matrix)
        rot = hg.GetR(matrix)
        self.parent_node.GetTransform().SetRot(rot)
        # self.v_move = physics_parameters["v_move"]

        # Collision
        if self.target is not None:

            for collision in rays_hits:
                if collision["name"] == "front":
                    if len(collision["hits"]) > 0:
                        hit = collision["hits"][0]
                        if 0 < hit.t < raycast_length:
                            v_impact = hit.P - pos
                            if hg.Len(v_impact) < 2 * hg.Len(self.v_move) * dts:
                                collision_object = Collisions_Object.get_object_by_collision_node(hit.node)
                                if collision_object is not None and hasattr(collision_object, "nationality") and collision_object.nationality != self.nationality:
                                    self.start_explosion()
                                    collision_object.hit(self.get_hit_damages(), hit.P)

        #debug:
        if self.flag_user_control:
            ucd = self.get_device("MissileUserControlDevice")
            if ucd is not None:
                self.parent_node.GetTransform().SetPos(ucd.pos_mem)

        else:
            self.parent_node.GetTransform().SetPos(pos)

        if pos.y < self.terrain_altitude:
            self.start_explosion()
        smoke_start_pos += self.v_move * dts
        self.update_smoke(smoke_start_pos, dts)

    def get_physics_parameters(self):
        return {"v_move": self.v_move,
                "thrust_level": 1,
                "thrust_force": self.thrust_force,
                "lift_force": 0,
                "drag_coefficients": self.drag_coeff,
                "health_wreck_factor": 1,
                "angular_levels": self.angular_levels,
                "angular_frictions": self.angular_frictions,
                "speed_ceiling": self.speed_ceiling,
                "flag_easy_steering": False
                }

    def update_kinetics(self, dts):

        if self.activated:

            self.update_devices(dts)

            self.life_cptr += dts

            if 0 < self.life_delay < self.life_cptr:
                self.start_explosion()
            if not self.wreck:

                if not self.flag_custom_physics_mode:
                    mat, pos, rot, aX, aY, aZ = self.decompose_matrix()
                    # Rotation
                    self.angular_levels.x, self.angular_levels.y, self.angular_levels.z = 0, 0, 0
                    if self.target is not None:
                        target_node = self.target.get_parent_node()
                        target_dir = hg.Normalize((target_node.GetTransform().GetPos() - pos))
                        axis_rot = hg.Cross(aZ, target_dir)
                        if hg.Len(axis_rot) > 0.001:
                            moment = hg.Normalize(axis_rot)
                            self.angular_levels.x = hg.Dot(aX, moment)
                            self.angular_levels.y = hg.Dot(aY, moment)
                            self.angular_levels.z = hg.Dot(aZ, moment)

                    physics_parameters = self.get_physics_parameters()

                    mat, physics_parameters = Physics.update_physics(self.parent_node.GetTransform().GetWorld(), self, physics_parameters, dts)
                    self.v_move = physics_parameters["v_move"]

                    #debug
                    if self.flag_user_control:
                        self.v_move *= 0


                else:
                    if self.custom_matrix is not None:
                        mat = self.custom_matrix
                    else:
                        mat = self.get_parent_node().GetTransform().GetWorld()
                    if self.custom_v_move is not None:
                        self.v_move = self.custom_v_move


                self.update_collisions(mat, dts)

            else:
                pos = self.parent_node.GetTransform().GetPos()
                smoke_start_pos = hg.GetT(self.engines_slots[0].GetTransform().GetWorld())

                if self.explode is not None:
                    self.explode.update_kinetics(pos, hg.Vec3.Front, self.v_move, hg.Vec3.Up, dts)
                    if len(self.smoke) > 0:
                        if self.smoke_time < 0:
                            self.update_smoke(smoke_start_pos, dts)
                        if self.explode.end and self.smoke_time >= 0:
                            self.deactivate()
                    elif self.explode.end:
                        self.deactivate()
                else:
                    if len(self.smoke) > 0:
                        if self.smoke_time < 0:
                            self.update_smoke(smoke_start_pos, dts)
                        if self.smoke_time >= 0:
                            self.deactivate()
                    else:
                        self.deactivate()

    def start_explosion(self):
        if not self.wreck:
            self.wreck = True
            if self.explode is not None:
                self.explode.flow = 3000
            self.disable_nodes()
            self.smoke_time = -self.smoke_delay
        # self.parent_node.RemoveObject()

    def get_target_name(self):

        if self.target is None:
            return ""
        else:
            return self.target.name
    
    def set_thrust_force(self, value:float):
        self.thrust_force = value
    
    def set_angular_friction(self, x, y, z):
        self.angular_frictions.x, self.angular_frictions.y, self.angular_frictions.z = x, y, z
    
    def set_drag_coefficients(self, x, y, z):
        self.drag_coeff.x, self.drag_coeff.y, self.drag_coeff.z = x, y, z

# =====================================================================================================
#                                  Aircraft
# =====================================================================================================

class Aircraft(Destroyable_Machine):
    IA_COM_IDLE = 0
    IA_COM_LIFTOFF = 1
    IA_COM_FIGHT = 2
    IA_COM_RETURN_TO_BASE = 3
    IA_COM_LANDING = 4

    def __init__(self, name, model_name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, instance_scene_name, nationality, start_position, start_rotation):

        Destroyable_Machine.__init__(self, name, model_name, scene, scene_physics, pipeline_ressource, instance_scene_name, Destroyable_Machine.TYPE_AIRCRAFT, nationality, start_position, start_rotation)
        self.commands.update({"SET_THRUST_LEVEL": self.set_thrust_level,
                              "SET_BRAKE_LEVEL": self.set_brake_level,
                              "SET_FLAPS_LEVEL": self.set_flaps_level,
                              "SET_ROLL_LEVEL": self.set_roll_level,
                              "SET_PITCH_LEVEL": self.set_pitch_level,
                              "SET_YAW_LEVEL": self.set_yaw_level,
                              "ACTIVATE_POST_COMBUSTION": self.activate_post_combustion,
                              "DEACTIVATE_POST_COMBUSTION": self.deactivate_post_combustion
                              })

        self.add_device(AircraftUserControlDevice("UserControlDevice", self, "scripts/aircraft_user_inputs_mapping.json"))
        self.add_device(AircraftAutopilotControlDevice("AutopilotControlDevice", self, "scripts/aircraft_autopilot_inputs_mapping.json"))
        self.add_device(AircraftIAControlDevice("IAControlDevice", self, "scripts/aircraft_ia_inputs_mapping.json"))
        self.add_device(TargettingDevice("TargettingDevice", self, True))
        self.setup_collisions()

        # Aircraft vars:
        self.post_combustion = False
        self.angular_levels = hg.Vec3(0, 0, 0)  # 0 to 1
        self.brake_level = 0
        self.flag_landing = False
        self.thrust_level = 0

        self.start_landed = True

        self.start_gear_state = True # !!!!!!!!!!!!!!!!!!!!!!!

        self.start_thrust_level = 0
        self.start_linear_speed = 0

        # Setup slots
        self.engines_slots = self.get_engines_slots()

        self.machine_gun_slots = self.get_machines_guns_slots()

        # Missiles:
        self.missiles_slots = self.get_missiles_slots()
        if self.missiles_slots is not None:
            self.add_device(MissilesDevice("MissilesDevice", self, self.missiles_slots))

        """
        self.missiles_slots = self.get_missiles_slots()
        self.missiles = [None] * len(self.missiles_slots)

        self.missiles_started = [None] * len(self.missiles_slots)
        """

        # Gun machine:
        n = len(self.machine_gun_slots)
        for i in range(n):
            self.add_device(MachineGun(("MachineGunDevice_%02d") % i, self, self.machine_gun_slots[i], scene, scene_physics, 1000 / n))
            #self.gun_machines.append(MachineGun(self.name + ".gun." + str(i + 1), self.scene, self.scene_physics, 1000))

        # Particles:
        self.explode = None
        self.smoke = None
        self.post_combustion_particles = []
        if Destroyable_Machine.flag_activate_particles:
            self.setup_particles()


        #self.IA_commands_labels = ["IA_COM_IDLE", "IA_COM_LIFTOFF", "IA_COM_FIGHT", "IA_COM_RETURN_TO_BASE", "IA_COM_LANDING"]

        # Aircraft constants:

        self.landing_max_speed = 300  # km/h
        self.bottom_height = 0.96
        self.gear_height = 2
        self.parts_angles = hg.Vec3(radians(15), radians(45), radians(45))
        self.thrust_force = 10
        self.post_combustion_force = self.thrust_force / 2
        self.drag_coeff = hg.Vec3(0.033, 0.06666, 0.0002)
        self.wings_lift = 0.0005
        self.brake_drag = 0.006
        self.flaps_lift = 0.0025
        self.flaps_drag = 0.002
        self.gear_drag = 0.001
        self.angular_frictions = hg.Vec3(0.000175, 0.000125, 0.000275)  # pitch, yaw, roll
        self.speed_ceiling = 1750  # maneuverability is not guaranteed beyond this speed !
        self.angular_levels_inertias = hg.Vec3(3, 3, 3)
        self.max_safe_altitude = 20000
        self.max_altitude = 30000
        self.landing_max_speed = 300  # km/h

        # Aircraft vars:
        self.flag_going_to_takeoff_position = False
        self.takeoff_position = None

        self.flag_easy_steering = True
        self.flag_easy_steering_mem = True  # Used in IA on/off switching
        self.thrust_level_inertia = 1
        self.thrust_level_dest = 0
        self.thrust_disfunction_noise = ms.Temporal_Perlin_Noise(0.1)
        self.brake_level_dest = 0
        self.brake_level_inertia = 1
        self.flaps_level = 0
        self.flaps_level_dest = 0
        self.flaps_level_inertia = 1
        self.angular_levels_dest = hg.Vec3(0, 0, 0)

        self.landing_targets = []

        # Attitudes calculation:
        self.pitch_attitude = 0
        self.roll_attitude = 0
        self.heading = 0

        self.flag_landed = True
        self.minimum_flight_speed = 250
        self.reset()

    def reset(self, position=None, rotation=None):
        Destroyable_Machine.reset(self, position, rotation)

        # print("Start_position: " + str(self.start_position.x) + " " + str(self.start_position.y) + " " + str(self.start_position.z))

        self.v_move = hg.GetZ(self.parent_node.GetTransform().GetWorld()) * self.start_linear_speed
        self.angular_levels = hg.Vec3(0, 0, 0)

        if self.smoke is not None: self.smoke.reset()
        if self.explode is not None: self.explode.reset()
        self.wreck = False
        self.flag_crashed = False

        #self.flag_gear_deployed = self.start_gear_state
        if "Gear" in self.devices and self.devices["Gear"] is not None:
            self.devices["Gear"].reset()

        n = self.get_machinegun_count()
        for i in range(n):
            gmd = self.get_device("MachineGunDevice_%02d" % i)
            if gmd is not None:
                gmd.reset()

        td = self.get_device("TargettingDevice")
        if td is not None:
            td.reset()
        self.rearm()

        self.reset_thrust_level(self.start_thrust_level)
        self.reset_brake_level(0)
        self.reset_flaps_level(0)

        self.post_combustion = False

        #self.deactivate_autopilot()
        #self.deactivate_IA()
        ia = self.get_device("IAControlDevice")
        if ia is not None:
            ia.deactivate()
        apctrl = self.get_device("AutopilotControlDevice")
        if apctrl is not None:
            apctrl.deactivate()


        self.set_health_level(1)
        self.angular_levels_dest = hg.Vec3(0, 0, 0)

        self.linear_speeds = [self.start_linear_speed] * 10
        self.linear_acceleration = 0

        self.flag_landed = self.start_landed

    def hit(self, value, position):
        Destroyable_Machine.hit(self, value, position)
        if not self.wreck:
            if self.health_level == 0 and not self.wreck:
                self.start_explosion()
            ia_ctrl = self.get_device("IAControlDevice")
            if ia_ctrl is not None and ia_ctrl.is_activated():
                ia_ctrl.controlled_device_hitted()

    def show_objects(self):
        AnimatedModel.show_objects(self)
        # A MODIFIER
        self.devices["Gear"].start_state = self.devices["Gear"].activated
        self.devices["Gear"].reset()

    def destroy(self):

        md = self.get_device("MissilesDevice")
        if md is not None:
            md.destroy()

        n = self.get_machinegun_count()
        for i in range(n):
            gmd = self.get_device("MachineGunDevice_%02d" % i)
            if gmd is not None:
                gmd.destroy_gun()

        if self.explode is not None:
            self.explode.destroy()
            self.explode = None
        if self.smoke is not None:
            self.smoke.destroy()
            self.smoke = None

        for pcp in self.post_combustion_particles:
            pcp.destroy()
        self.post_combustion_particles = []
        self.destroy_nodes()
        self.flag_destroyed = True

    def set_health_level(self, value):
        self.health_level = min(max(value, 0), 1)
        if self.smoke is not None:
            if self.health_level < 1:
                self.smoke.flow = int(self.smoke.num_particles / 10)
            else:
                self.smoke.flow = 0
            self.smoke.delay_range = hg.Vec2(1, 10) * pow(1 - self.health_level, 3)
            self.smoke.scale_range = hg.Vec2(0.1, 5) * pow(1 - self.health_level, 3)
            self.smoke.stream_angle = pow(1 - self.health_level, 2.6) * 180

    def setup_bounds_positions(self):
        Destroyable_Machine.setup_bounds_positions(self)
        self.bound_down.y -= 0.4

    # ===================== Start state:

    def record_start_state(self):
        self.start_position = self.parent_node.GetTransform().GetPos()
        self.start_rotation = self.parent_node.GetTransform().GetRot()
        self.devices["Gear"].start_state = self.devices["Gear"].activated
        self.start_landed = self.flag_landed
        self.start_thrust_level = self.thrust_level
        self.start_linear_speed = self.get_linear_speed()

    # ==================== Thrust ===================================

    def get_thrust_level(self):
        return self.thrust_level

    def set_thrust_level(self, value):
        self.thrust_level_dest = min(max(value, 0), 1)

    def reset_thrust_level(self, value):
        self.thrust_level_dest = min(max(value, 0), 1)
        self.thrust_level = self.thrust_level_dest

    def update_thrust_level(self, dts):

        # Altitude disfunctions:
        alt = self.get_altitude()
        collapse = 1
        if alt > self.max_safe_altitude:
            f = pow((alt - self.max_safe_altitude) / (self.max_altitude - self.max_safe_altitude), 2)
            perturb = (self.thrust_disfunction_noise.temporal_Perlin_noise(dts) * 0.5 + 0.5) * f
            collapse = 1 - perturb
            self.hit(self.thrust_level * 0.001 * perturb, self.parent_node.GetTransform().GetPos())

        dest = self.thrust_level_dest * collapse

        if dest > self.thrust_level:
            self.thrust_level = min(dest, self.thrust_level + self.thrust_level_inertia * dts)
        else:
            self.thrust_level = max(dest, self.thrust_level - self.thrust_level_inertia * dts)

        # Clamp:
        self.thrust_level = min(1, max(0, self.thrust_level))

        if self.thrust_level < 1: self.deactivate_post_combustion()

    def activate_post_combustion(self):
        if self.thrust_level == 1:
            self.post_combustion = True
            for pcp in self.post_combustion_particles:
                pcp.flow = 35

    def deactivate_post_combustion(self):
        self.post_combustion = False
        for pcp in self.post_combustion_particles:
            pcp.flow = 0

    # ==================== Brakes ==========================

    def get_brake_level(self):
        return self.brake_level

    def reset_brake_level(self, value):
        self.brake_level_dest = min(max(value, 0), 1)
        self.brake_level = self.brake_level_dest

    def set_brake_level(self, value):
        self.brake_level_dest = min(max(value, 0), 1)

    def update_brake_level(self, dts):
        if self.brake_level_dest > self.brake_level:
            self.brake_level = min(self.brake_level_dest, self.brake_level + self.brake_level_inertia * dts)
        else:
            self.brake_level = max(self.brake_level_dest, self.brake_level - self.brake_level_inertia * dts)

    # ==================== flaps ==========================

    def get_flaps_level(self):
        return self.flaps_level

    def reset_flaps_level(self, value):
        self.flaps_level_dest = min(max(value, 0), 1)
        self.flaps_level = self.flaps_level_dest

    def set_flaps_level(self, value):
        self.flaps_level_dest = min(max(value, 0), 1)

    def update_flaps_level(self, dts):
        if self.flaps_level_dest > self.flaps_level:
            self.flaps_level = min(self.flaps_level_dest, self.flaps_level + self.flaps_level_inertia * dts)
        else:
            self.flaps_level = max(self.flaps_level_dest, self.flaps_level - self.flaps_level_inertia * dts)

    # ==================== Rotations ===============================

    def set_pitch_level(self, value):
        self.angular_levels_dest.x = max(min(1, value), -1)

    def set_yaw_level(self, value):
        self.angular_levels_dest.y = max(min(1, value), -1)

    def set_roll_level(self, value):
        self.angular_levels_dest.z = max(min(1, value), -1)

    def get_pilot_pitch_level(self):
        return self.angular_levels_dest.x

    def get_pilot_yaw_level(self):
        return self.angular_levels_dest.y

    def get_pilot_roll_level(self):
        return self.angular_levels_dest.z

    # ===================== Particles ==============================

    def setup_particles(self):
        # Explode particles:
        self.explode = ParticlesEngine(self.name + ".explode", self.scene, "feed_back_explode", 100, hg.Vec3(10, 10, 10), hg.Vec3(100, 100, 100), 180, 0)
        self.explode.delay_range = hg.Vec2(1, 4)
        self.explode.flow = 0
        self.explode.scale_range = hg.Vec2(0.25, 2)
        self.explode.start_speed_range = hg.Vec2(10, 150)
        self.explode.colors = [hg.Color(1., 1., 1., 1), hg.Color(1., 1., 0.9, 0.5), hg.Color(0.6, 0.525, 0.5, 0.25),
                               hg.Color(0.5, 0.5, 0.5, 0.125), hg.Color(0., 0., 0., 0.0)]
        self.explode.set_rot_range(radians(20), radians(150), radians(50), radians(120), radians(45), radians(120))
        self.explode.gravity = hg.Vec3(0, -9.8, 0)
        self.explode.loop = False

        # Smoke particles:
        self.smoke = ParticlesEngine(self.name + ".smoke", self.scene, "feed_back_explode", int(uniform(200, 400)), hg.Vec3(5, 5, 5), hg.Vec3(50, 50, 50), 180, 0)
        self.smoke.flow_decrease_date = 0.5
        self.smoke.delay_range = hg.Vec2(4, 8)
        self.smoke.flow = 0
        self.smoke.scale_range = hg.Vec2(0.1, 5)
        self.smoke.start_speed_range = hg.Vec2(5, 15)
        self.smoke.colors = [hg.Color(1., 1., 1., 1), hg.Color(1., 0.2, 0.1, 0.3), hg.Color(.7, .7, .7, 0.2),
                             hg.Color(.5, .5, .5, 0.1), hg.Color(0., 0., 0., 0.05), hg.Color(0., 0.5, 1., 0)]
        self.smoke.set_rot_range(0, 0, radians(120), radians(120), 0, 0)
        self.smoke.gravity = hg.Vec3(0, 30, 0)
        self.smoke.linear_damping = 0.5
        self.smoke.loop = True

        # Post-combustion particles:
        for i in range(len(self.engines_slots)):
            self.post_combustion_particles.append(self.create_post_combustion_particles(".pc" + str(i + 1)))

    def destroy_particles(self):
        if len(self.post_combustion_particles) > 0:
            for i in range(len(self.engines_slots)):
                self.post_combustion_particles[i].destroy()
            self.post_combustion_particles = []
        if self.smoke is not None:
            self.smoke.destroy()
            self.smoke = None
        if self.explode is not None:
            self.explode.destroy()
            self.explode = None

        n = self.get_machinegun_count()
        for i in range(n):
            gmd = self.get_device("MachineGunDevice_%02d" % i)
            if gmd is not None:
                gmd.destroy_particles()

    def create_post_combustion_particles(self, engine_name):
        pc = ParticlesEngine(self.name + engine_name, self.scene, "bullet_impact", 15,
                             hg.Vec3(1, 1, 1), hg.Vec3(0.2, 0.2, 0.2), 15, 0)
        pc.delay_range = hg.Vec2(0.3, 0.4)
        pc.flow = 0
        pc.scale_range = hg.Vec2(1, 1)
        pc.start_speed_range = hg.Vec2(1, 1)
        pc.colors = [hg.Color(1., 1., 1., 1), hg.Color(1., 0.9, 0.7, 0.5), hg.Color(0.9, 0.7, 0.1, 0.25),
                     hg.Color(0.9, 0.5, 0., 0.), hg.Color(0.85, 0.5, 0., 0.25), hg.Color(0.8, 0.4, 0., 0.15),
                     hg.Color(0.8, 0.1, 0.1, 0.05), hg.Color(0.5, 0., 0., 0.)]
        pc.set_rot_range(radians(1200), radians(2200), radians(1420), radians(1520), radians(1123), radians(5120))
        pc.gravity = hg.Vec3(0, 0, 0)
        pc.linear_damping = 1.0
        pc.loop = True
        return pc

    def start_explosion(self):

        if self.explode is not None:
            self.explode.flow = int(self.explode.num_particles * 5 / 4)
        if self.smoke is not None:
            self.smoke.reset_life_time(uniform(30, 60))

        self.set_thrust_level(0)
        n = self.get_machinegun_count()
        for i in range(n):
            mgd = self.get_device("MachineGunDevice_%02d" % i)
            if mgd is not None:
                mgd.stop_machine_gun()

        self.wreck = True

    def update_post_combustion_particles(self, dts, pos, rot_mat):
        for i, pcp in enumerate(self.post_combustion_particles):
            pos_prec = hg.GetT(self.engines_slots[i].GetTransform().GetWorld())
            pcp.update_kinetics(pos_prec + self.v_move * dts, hg.GetZ(rot_mat) * -1, self.v_move, hg.GetY(rot_mat), dts)

    def update_feedbacks(self, dts):
        if Destroyable_Machine.flag_activate_particles and Destroyable_Machine.flag_update_particles:

            mat, pos, rot, aX, aY, aZ = self.decompose_matrix()
            engines_pos = hg.Vec3(0, 0, 0)
            for i, pcp in enumerate(self.post_combustion_particles):
                engines_pos += hg.GetT(self.engines_slots[i].GetTransform().GetWorld())
            engines_pos /= len(self.post_combustion_particles)

            if self.smoke is not None:
                if (self.health_level < 1 or self.smoke.num_alive > 0) and not self.smoke.end:
                    self.smoke.update_kinetics(engines_pos, aZ * -1, self.v_move, aY, dts)  # AJOUTER UNE DUREE LIMITE AU FOURNEAU LORSQUE WRECK=TRUE !
            if self.explode is not None:
                if self.wreck and not self.explode.end:
                    self.explode.update_kinetics(pos, aZ * -1, self.v_move, aY, dts)

            self.update_post_combustion_particles(dts, pos, hg.GetRMatrix(mat))

    # ===================== Weapons ==============================

    def get_machines_guns_slots(self):
        return self.get_slots("machine_gun_slot")

    def get_machinegun_count(self):
        return len(self.machine_gun_slots)

    def get_num_bullets(self):
        n = self.get_machinegun_count()
        for i in range(n):
            gmd = self.get_device("MachineGunDevice_%02d" % i)
            if gmd is not None:
                n += gmd.get_num_bullets()
        return n

    # =========================== Missiles

    def get_missiles_slots(self):
        return self.get_slots("missile_slot")

    def get_num_missiles_slots(self):
        return len(self.missiles_slots)

    def rearm(self):
        self.set_health_level(1)
        n = self.get_machinegun_count()
        for i in range(n):
            gmd = self.get_device("MachineGunDevice_%02d" % i)
            if gmd is not None:
                gmd.reset()
        md = self.get_device("MissilesDevice")
        if md is not None:
            md.rearm()


    # ============================ Engines

    def get_engines_slots(self):
        return self.get_slots("engine_slot")

    def activate_easy_steering(self):
        if self.autopilot_activated or self.IA_activated:
            self.flag_easy_steering_mem = True
        else:
            self.flag_easy_steering = True

    def deactivate_easy_steering(self):
        if self.autopilot_activated or self.IA_activated:
            self.flag_easy_steering_mem = False
        else:
            self.flag_easy_steering = False

    def update_takoff_positionning(self, dts):
        self.v_move.x = self.v_move.y = self.v_move.z = 0
        self.t_going_to_takeoff_position += dts / 5
        if self.t_going_to_takeoff_position >= 1:
            self.flag_going_to_takeoff_position = False
        else:
            t = MathsSupp.smoothstep(0, 1, self.t_going_to_takeoff_position)
            pos = self.takeoff_position_start * (1 - t) + self.takeoff_position_dest * t
            self.parent_node.GetTransform().SetPos(pos)

    def set_landed(self):
        if not self.flag_landed:
            if self.ground_node_collision is not None:
                destroyable_machine = Destroyable_Machine.get_object_by_collision_node(self.ground_node_collision)
                if destroyable_machine is not None:
                    if destroyable_machine.nationality == self.nationality:
                        if destroyable_machine.type == Destroyable_Machine.TYPE_SHIP and not destroyable_machine.wreck:
                            mat = self.parent_node.GetTransform().GetWorld()
                            az = hg.GetZ(mat)
                            pos = hg.GetT(mat)
                            self.takeoff_position_start = pos
                            self.takeoff_position_dest = pos - az * 50
                            self.flag_going_to_takeoff_position = True
                            self.t_going_to_takeoff_position = 0
                            self.rearm()
            self.flag_landed = True

    def set_landing_targets(self, targets):
        self.landing_targets = targets

    # ============================= Physics ====================================

    def compute_z_drag(self):
        if "Gear" in self.devices and self.devices["Gear"] is not None:
            gear = self.devices["Gear"]
            gear_lvl = gear.gear_level
        else:
            gear_lvl = 0
        return self.drag_coeff.z + self.brake_drag * self.brake_level + self.flaps_level * self.flaps_drag + self.gear_drag * gear_lvl

    def stabilize(self, p, y, r):
        if p: self.set_pitch_level(0)
        if y: self.set_yaw_level(0)
        if r: self.set_roll_level(0)

    def update_inertial_value(self, v0, vd, vi, dts):
        vt = vd - v0
        if vt < 0:
            v = v0 - vi * dts
            if v < vd: v = vd
        elif vt > 0:
            v = v0 + vi * dts
            if v > vd: v = vd
        else:
            v = vd
        return v

    def update_collisions(self, matrix, dts):

        mat, pos, rot, aX, aY, aZ = self.decompose_matrix(matrix)

        collisions_raycasts = [
            {"name": "down", "position": self.bound_down, "direction": hg.Vec3(0, -5, 0)}
        ]

        ray_hits, self.terrain_altitude, self.terrain_normale = Physics.update_collisions(mat, self, collisions_raycasts)

        alt = self.terrain_altitude
        if "Gear" in self.devices and self.devices["Gear"] is not None and self.devices["Gear"].activated:
            bottom_alt = self.devices["Gear"].gear_height
        else:
            bottom_alt = self.bottom_height
        self.ground_node_collision = None

        for collision in ray_hits:
            if collision["name"] == "down":
                if len(collision["hits"]) > 0:
                    hit = collision["hits"][0]
                    machine = self.get_machine_by_node(hit.node)
                    if machine is not None and machine.type != Destroyable_Machine.TYPE_SHIP and machine.type != Destroyable_Machine.TYPE_GROUND:
                        self.hit(1, hit.P)
                    else:
                        self.ground_node_collision = hit.node
                        alt = hit.P.y + bottom_alt

        self.flag_landing = False

        if self.flag_crashed:
            pos.y = alt
            self.v_move *= pow(0.9, 60 * dts)

        else:
            if pos.y < alt:
                flag_crash = True
                if "Gear" in self.devices and self.devices["Gear"] is not None:
                    gear = self.devices["Gear"]
                    linear_speed = self.get_linear_speed()
                    if gear.activated and degrees(abs(asin(aZ.y))) < 15 and degrees(abs(asin(aX.y))) < 10 and linear_speed * 3.6 < self.landing_max_speed:

                        pos.y += (alt - pos.y) * 0.1 * 60 * dts
                        if self.v_move.y < 0: self.v_move.y *= pow(0.8, 60 * dts)
                        # b = min(1, self.brake_level + (1 - health_wreck_factor))
                        b = self.brake_level
                        self.v_move *= ((b * pow(0.98, 60 * dts)) + (1 - b))
                        # r=self.parent_node.GetTransform().GetRot()
                        f = ((b * pow(0.95, 60 * dts)) + (1 - b))
                        rot.x *= f
                        rot.z *= f
                        # self.parent_node.GetTransform().SetRot(rot)
                        self.flag_landing = True
                        flag_crash = False

                if flag_crash:
                    pos.y = alt
                    self.crash()

        return hg.TransformationMat4(pos, rot)

    def crash(self):
        self.hit(1, self.parent_node.GetTransform().GetPos())
        self.flag_crashed = True
        self.set_thrust_level(0)
        ia_ctrl = self.get_device("IAControlDevice")
        if ia_ctrl is not None:
            ia_ctrl.deactivate()
        else:
            ap_ctrl = self.get_device("AutopilotControlDevice")
            if ap_ctrl is not None:
                ap_ctrl.deactivate()

    def update_angular_levels(self, dts):
        self.angular_levels.x = self.update_inertial_value(self.angular_levels.x, self.angular_levels_dest.x,
                                                           self.angular_levels_inertias.x, dts)
        self.angular_levels.y = self.update_inertial_value(self.angular_levels.y, self.angular_levels_dest.y,
                                                           self.angular_levels_inertias.y, dts)
        self.angular_levels.z = self.update_inertial_value(self.angular_levels.z, self.angular_levels_dest.z,
                                                           self.angular_levels_inertias.z, dts)

    # ==================================================================

    def get_physics_parameters(self):
        # ============================ Compute Thrust impulse
        tf = self.thrust_force
        if self.post_combustion and self.thrust_level == 1:
            tf += self.post_combustion_force
        # ================================ Compute Z drag impulse
        dc = hg.Vec3(self.drag_coeff)
        dc.z = self.compute_z_drag()

        return {"v_move": self.v_move,
                "thrust_level": self.thrust_level,
                "thrust_force": tf,
                "lift_force": self.wings_lift + self.flaps_level * self.flaps_lift,
                "drag_coefficients": dc,
                "health_wreck_factor": pow(self.health_level, 0.2),
                "angular_levels": self.angular_levels,
                "angular_frictions": self.angular_frictions,
                "speed_ceiling": self.speed_ceiling,
                "flag_easy_steering": self.flag_easy_steering
                }

    def update_kinetics(self, dts):

        # Custom physics (but keep inner collisions system)
        if self.flag_custom_physics_mode:
            Destroyable_Machine.update_kinetics(self, dts)

        # Inner physics
        else:

            if self.activated:
                self.update_devices(dts) # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

                # # ========================= Flight physics Repositionning after landing :

                if self.flag_going_to_takeoff_position:
                    self.update_takoff_positionning(dts)

                # ========================= Flight physics
                else:

                    # ==================== Aircraft Inertias for animated parts
                    self.update_thrust_level(dts)  # Applies disfunctions
                    self.update_brake_level(dts)  # Brake level inertia
                    self.update_flaps_level(dts)  # Flaps level inertia
                    self.update_angular_levels(dts)  # flaps inertia

                    self.update_mobile_parts(dts)  # Animate mobile parts

                    # # ========================= Update physics

                    physics_parameters = self.get_physics_parameters()

                    mat, physics_parameters = Physics.update_physics(self.parent_node.GetTransform().GetWorld(), self, physics_parameters, dts)

                    # ======================== Update aircraft vars:

                    self.pitch_attitude = physics_parameters["pitch_attitude"]
                    self.heading = physics_parameters["heading"]
                    self.roll_attitude = physics_parameters["roll_attitude"]
                    self.v_move = physics_parameters["v_move"]

                    # ========================== Update collisions

                    mat = self.update_collisions(mat, dts)

                    # Landed state:
                    ia_ctrl = self.get_device("IAControlDevice")
                    if not self.flag_crashed and not ia_ctrl.is_activated():
                        hs, vs = self.get_world_speed()
                        if abs(vs) > 1:
                            self.flag_landed = False
                        if hs < 1 and abs(vs) < 1:
                            self.set_landed()

                    # ======== Update matrix==========================================================

                    mat, pos, rot, aX, aY, aZ = self.decompose_matrix(mat)

                    self.parent_node.GetTransform().SetPos(pos)
                    self.parent_node.GetTransform().SetRot(rot)

                    # ======== Update Acceleration ==========================================================

                    self.rec_linear_speed()
                    self.update_linear_acceleration()


                # ====================== Update Feed backs:

                self.update_feedbacks(dts)

    def gui(self):
        if hg.ImGuiBegin("Aircraft"):

            hg.ImGuiSetWindowPos("Aircraft", hg.Vec2(1300, 20), hg.ImGuiCond_Once)
            hg.ImGuiSetWindowSize("Aircraft", hg.Vec2(600, 450), hg.ImGuiCond_Once)
            hg.ImGuiText("Name:" + self.name)
            hg.ImGuiText("Altitude: " + str(int(self.get_altitude())))
            hg.ImGuiText("Cap:" + str(int(self.heading)))
            hg.ImGuiText("Health:" + str(int(self.health_level * 100)) + "%")
            hg.ImGuiText("Linear speed:" + str(int(self.get_linear_speed() * 3.6)))
            hs, vs = self.get_world_speed()
            hg.ImGuiText("Horizontal speed:" + str(int(hs * 3.6)))
            hg.ImGuiText("Vertical speed:" + str(int(vs * 3.6)))

            d, self.flag_display_linear_speed = hg.ImGuiCheckbox("Display linear speed", self.flag_display_linear_speed)
            d, self.flag_display_vertical_speed = hg.ImGuiCheckbox("Display vertical speed", self.flag_display_vertical_speed)
            d, self.flag_display_horizontal_speed = hg.ImGuiCheckbox("Display horizontal speed", self.flag_display_horizontal_speed)

            if hg.ImGuiButton("RESET"):
                self.reset()

            ia_ctrl = self.get_device("IAControlDevice")
            if ia_ctrl is not None:
                d, f = hg.ImGuiCheckbox("IA activated", ia_ctrl.is_activated())
                if d:
                    if f:
                        ia_ctrl.activate()
                    else:
                        ia_ctrl.deactivate()

                if ia_ctrl.is_activated():
                    hg.ImGuiText("IA command: " + ia_ctrl.IA_commands_labels[ia_ctrl.IA_command])


            hg.ImGuiSeparator()
            ap_ctrl = self.get_device("AutopilotControlDevice")
            if ap_ctrl is not None:
                if ap_ctrl.is_user_control_active():
                    d, f = hg.ImGuiCheckbox("Autopilot activated", ap_ctrl.is_activated())
                    if d:
                        if f:
                            ap_ctrl.activate()
                        else:
                            ap_ctrl.deactivate()

                    d, f = hg.ImGuiSliderFloat("Autopilot heading", ap_ctrl.autopilot_heading, 0, 360)
                    if d:
                        ap_ctrl.set_autopilot_heading(f)

                    d, f = hg.ImGuiSliderFloat("Autopilot altitude (m)", ap_ctrl.autopilot_altitude, ap_ctrl.altitude_range[0], ap_ctrl.altitude_range[1])
                    if d:
                        ap_ctrl.set_autopilot_altitude(f)

                    d, f = hg.ImGuiSliderFloat("Autopilot speed (km/h)", ap_ctrl.autopilot_speed * 3.6, ap_ctrl.speed_range[0], ap_ctrl.speed_range[1])
                    if d:
                        ap_ctrl.set_autopilot_speed(f / 3.6)
                else:
                    hg.ImGuiText("Autopilot heading: %.2f" % (ap_ctrl.autopilot_heading))
                    hg.ImGuiText("Autopilot altitude (m): %.2f" % (ap_ctrl.autopilot_altitude))
                    hg.ImGuiText("Autopilot speed (km/h): %.2f" % (ap_ctrl.autopilot_speed * 3.6))

            td = self.get_device("TargettingDevice")
            if td is not None:
                targets_list = hg.StringList()
                targets_list.push_back("- None -")

                for target in td.targets:
                    nm = target.name
                    if target.wreck:
                        nm += " - WRECK!"
                    if not target.activated:
                        nm += " - INACTIVE!"
                    targets_list.push_back(nm)

                f, d = hg.ImGuiListBox("Targets", td.target_id, targets_list, 20)
                if f:
                    td.set_target_id(d)

        hg.ImGuiEnd()


# ========================================================================================================
#                   Sounds handlers
# ========================================================================================================


class MissileSFX:

    def __init__(self, missile: Missile):
        self.missile = missile

        self.explosion_source = None
        self.explosion_state = tools.create_spatialized_sound_state(hg.SR_Once)
        self.explosion_ref = hg.LoadWAVSoundAsset("sfx/missile_explosion.wav")

        self.turbine_ref = hg.LoadWAVSoundAsset("sfx/missile_engine.wav")
        self.turbine_source = None
        self.turbine_state = tools.create_spatialized_sound_state(hg.SR_Loop)

        self.start = False
        self.exploded = False

    def reset(self):
        self.exploded = False

    def start_engine(self, main):
        self.turbine_state.volume = 0
        # self.turbine_state.pitch = 1
        self.turbine_source = hg.PlaySpatialized(self.turbine_ref, self.turbine_state)
        self.start = True

    def stop_engine(self, main):
        self.turbine_state.volume = 0
        # self.turbine_state.pitch = 1
        hg.StopSource(self.turbine_source)
        self.turbine_source = None

    def update_sfx(self, main, dts):
        if self.missile.activated:
            self.missile.calculate_view_matrix(main.scene.GetCurrentCamera())
            self.missile.update_view_v_move(dts)

            level = MathsSupp.get_sound_distance_level(hg.GetT(self.missile.mat_view)) * main.master_sfx_volume

            if not self.start:
                self.start_engine(main)

            if self.missile.wreck and not self.exploded:
                self.explosion_state.volume = level
                self.stop_engine(main)
                self.explosion_source = hg.PlaySpatialized(self.explosion_ref, self.explosion_state)
                self.exploded = True

            if not self.exploded:
                self.turbine_state.volume = 0.5 * level
                # self.turbine_state.pitch = self.turbine_pitch_levels.x + self.aircraft.thrust_level * (self.turbine_pitch_levels.y - self.turbine_pitch_levels.x)

                hg.SetSourceTransform(self.turbine_source, self.missile.mat_view, self.missile.view_v_move)
                hg.SetSourceVolume(self.turbine_source, self.turbine_state.volume)

            else:
                hg.SetSourceTransform(self.explosion_source, self.missile.mat_view, self.missile.view_v_move)
                hg.SetSourceVolume(self.explosion_source, min(1, level * 2))


class AircraftSFX:

    def __init__(self, aircraft: Aircraft):
        self.aircraft = aircraft

        self.turbine_pitch_levels = hg.Vec2(1, 2)

        self.turbine_ref = hg.LoadWAVSoundAsset("sfx/turbine.wav")
        self.air_ref = hg.LoadWAVSoundAsset("sfx/air.wav")
        self.pc_ref = hg.LoadWAVSoundAsset("sfx/post_combustion.wav")
        self.wind_ref = hg.LoadWAVSoundAsset("sfx/wind.wav")
        self.explosion_ref = hg.LoadWAVSoundAsset("sfx/explosion.wav")
        self.machine_gun_ref = hg.LoadWAVSoundAsset("sfx/machine_gun.wav")
        self.burning_ref = hg.LoadWAVSoundAsset("sfx/burning.wav")

        self.turbine_state = tools.create_spatialized_sound_state(hg.SR_Loop)
        self.air_state = tools.create_spatialized_sound_state(hg.SR_Loop)
        self.pc_state = tools.create_spatialized_sound_state(hg.SR_Loop)
        self.wind_state = tools.create_spatialized_sound_state(hg.SR_Loop)
        self.explosion_state = tools.create_spatialized_sound_state(hg.SR_Once)
        self.machine_gun_state = tools.create_spatialized_sound_state(hg.SR_Once)
        self.burning_state = tools.create_spatialized_sound_state(hg.SR_Loop)

        self.start = False

        self.pc_cptr = 0
        self.pc_start_delay = 0.25
        self.pc_stop_delay = 0.5

        self.turbine_source = None
        self.wind_source = None
        self.air_source = None
        self.pc_source = None
        self.explosion_source = None
        self.machine_gun_source = None
        self.burning_source = None

        self.pc_started = False
        self.pc_stopped = False

        self.exploded = False

    def reset(self):
        self.exploded = False

    def set_air_pitch(self, value):
        self.air_state.pitch = value

    def set_pc_pitch(self, value):
        self.pc_state.pitch = value

    def set_turbine_pitch_levels(self, values: hg.Vec2):
        self.turbine_pitch_levels = values

    def start_engine(self, main):
        self.turbine_state.volume = 0
        # self.turbine_state.pitch = 1
        self.air_state.volume = 0
        self.pc_state.volume = 0
        self.air_source = hg.PlaySpatialized(self.air_ref, self.air_state)
        self.turbine_source = hg.PlaySpatialized(self.turbine_ref, self.turbine_state)
        self.pc_source = hg.PlaySpatialized(self.pc_ref, self.pc_state)
        self.start = True
        self.pc_started = False
        self.pc_stopped = True

    def stop_engine(self, main):
        self.turbine_state.volume = 0
        # self.turbine_state.pitch = 1
        self.air_state.volume = 0
        self.pc_state.volume = 0
        if self.turbine_source is not None:
            hg.StopSource(self.turbine_source)
        if self.air_source is not None:
            hg.StopSource(self.air_source)
        if self.pc_source is not None:
            hg.StopSource(self.pc_source)

        self.start = False
        self.pc_started = False
        self.pc_stopped = True

        # self.wind_state.volume = 0

    def update_sfx(self, main, dts):

        self.aircraft.calculate_view_matrix(main.scene.GetCurrentCamera())
        self.aircraft.update_view_v_move(dts)

        level = MathsSupp.get_sound_distance_level(hg.GetT(self.aircraft.mat_view)) * main.master_sfx_volume

        if self.aircraft.thrust_level > 0 and not self.start:
            self.start_engine(main)

        if self.aircraft.smoke is not None:
            if self.aircraft.health_level < 1 and not self.aircraft.smoke.end:
                self.burning_state.volume = level * (1 - self.aircraft.health_level) * self.aircraft.smoke.life_f
                self.burning_state.mtx = self.aircraft.mat_view
                self.burning_state.vel = self.aircraft.view_v_move
                if self.burning_source is None:
                    self.burning_source = hg.PlaySpatialized(self.burning_ref, self.burning_state)
                hg.SetSourceTransform(self.burning_source, self.burning_state.mtx, self.burning_state.vel)
                hg.SetSourceVolume(self.burning_source, self.burning_state.volume)

            elif self.burning_source is not None:
                hg.StopSource(self.burning_source)
                self.burning_source = None

        if self.aircraft.wreck and not self.exploded:
            self.explosion_state.volume = level
            self.stop_engine(main)
            self.explosion_source = hg.PlaySpatialized(self.explosion_ref, self.explosion_state)
            self.exploded = True

        if self.start:
            if self.aircraft.thrust_level <= 0:
                self.stop_engine(main)

            else:
                self.turbine_state.volume = 0.5 * level
                # self.turbine_state.pitch = self.turbine_pitch_levels.x + self.aircraft.thrust_level * (self.turbine_pitch_levels.y - self.turbine_pitch_levels.x)
                self.air_state.volume = (0.1 + self.aircraft.thrust_level * 0.9) * level

                if self.aircraft.post_combustion:
                    self.pc_state.volume = level
                    if not self.pc_started:
                        self.pc_stopped = False
                        self.pc_state.volume *= self.pc_cptr / self.pc_start_delay
                        self.pc_cptr += dts
                        if self.pc_cptr >= self.pc_start_delay:
                            self.pc_started = True
                            self.pc_cptr = 0

                else:
                    if not self.pc_stopped:
                        self.pc_started = False
                        self.pc_state.volume = (1 - self.pc_cptr / self.pc_stop_delay) * level
                        self.pc_cptr += dts
                        if self.pc_cptr >= self.pc_stop_delay:
                            self.pc_stopped = True
                            self.pc_cptr = 0

                hg.SetSourceTransform(self.turbine_source, self.aircraft.mat_view, self.aircraft.view_v_move)
                hg.SetSourceVolume(self.turbine_source, self.turbine_state.volume)
                hg.SetSourceTransform(self.air_source, self.aircraft.mat_view, self.aircraft.view_v_move)
                hg.SetSourceVolume(self.air_source, self.air_state.volume)
                hg.SetSourceTransform(self.pc_source, self.aircraft.mat_view, self.aircraft.view_v_move)
                hg.SetSourceVolume(self.pc_source, self.pc_state.volume)

        if self.explosion_source is not None:
            hg.SetSourceTransform(self.explosion_source, self.aircraft.mat_view, self.aircraft.view_v_move)
            hg.SetSourceVolume(self.explosion_source, min(1, level * 2))

        f = min(1, self.aircraft.get_linear_speed() * 3.6 / 1000)
        self.wind_state.volume = f * level
        self.wind_state.mtx = self.aircraft.mat_view
        self.wind_state.vel = self.aircraft.view_v_move
        if self.wind_source is None:
            self.wind_source = hg.PlaySpatialized(self.wind_ref, self.wind_state)
        hg.SetSourceTransform(self.wind_source, self.wind_state.mtx, self.wind_state.vel)
        hg.SetSourceVolume(self.wind_source, self.wind_state.volume)

        # Machine gun
        n = self.aircraft.get_machinegun_count()
        if n > 0:
            num_new = 0
            for i in range(n):
                gmd = self.aircraft.get_device("MachineGunDevice_%02d" % i)
                if gmd is not None:
                    num_new += gmd.get_new_bullets_count()
            if num_new > 0:
                self.machine_gun_state.volume = level * 0.5
                self.machine_gun_state.mtx = self.aircraft.mat_view
                self.machine_gun_state.vel = self.aircraft.view_v_move
                self.machine_gun_source = hg.PlaySpatialized(self.machine_gun_ref, self.machine_gun_state)


# =====================================================================================================
#                                   Aircraft-carrier
# =====================================================================================================


class Carrier(Destroyable_Machine):
    instance_scene_name = "machines/aircraft_carrier_blend/aircraft_carrier_blend.scn"

    def __init__(self, name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, nationality):
        Destroyable_Machine.__init__(self, name, "Basic_Carrier", scene, scene_physics, pipeline_ressource, Carrier.instance_scene_name, Destroyable_Machine.TYPE_SHIP, nationality)
        self.setup_collisions()
        self.activated = True
        sv = self.parent_node.GetInstanceSceneView()
        self.radar = sv.GetNode(scene, "aircraft_carrier_radar")
        self.fps_start_point = sv.GetNode(scene, "fps_start_point")
        self.aircraft_start_points = []
        self.landing_points = []
        self.find_nodes("carrier_aircraft_start_point.", self.aircraft_start_points, 1)
        self.find_nodes("landing_point.", self.landing_points, 1)
        self.landing_targets = []
        for landing_point in self.landing_points:
            self.landing_targets.append(LandingTarget(landing_point))

    def find_nodes(self, name, tab, first=1):
        i = first
        sv = self.parent_node.GetInstanceSceneView()
        n = sv.GetNodes(self.scene).size()
        if n == 0:
            raise OSError("ERROR - Empty Instance '" + self.name + "'- Unloaded scene ?")
        while True:
            nm = name + '{:03d}'.format(i)
            nd = sv.GetNode(self.scene, nm)
            node_name = nd.GetName()
            if node_name != nm:
                break
            else:
                tab.append(nd)
                i += 1

    def destroy(self):
        if not self.flag_destroyed:
            self.destroy_nodes()
            self.flag_destroyed = True

    def hit(self, value, position):
        Collisions_Object.hit(self, value, position)

    def update_kinetics(self, dts):
        rot = self.radar.GetTransform().GetRot()
        rot.y += radians(45 * dts)
        self.radar.GetTransform().SetRot(rot)

    def get_aircraft_start_point(self, point_id):
        mat = self.aircraft_start_points[point_id].GetTransform().GetWorld()
        return hg.GetT(mat), hg.GetR(mat)

# =====================================================================================================
#                                   LandVehicle
# =====================================================================================================

class LandVehicle(Destroyable_Machine):

    def __init__(self, name, model_name, scene, scene_physics, pipeline_ressource, instance_scene_name, nationality, start_position=None, start_rotation=None):
        Destroyable_Machine.__init__(self, name, model_name, scene, scene_physics, pipeline_ressource, instance_scene_name, Destroyable_Machine.TYPE_LANDVEHICLE, nationality, start_position, start_rotation)

        self.thrust_level = 0
        self.brake_level = 0

        self.setup_bounds_positions()

    def destroy(self):
        self.destroy_nodes()
        self.flag_destroyed = True

    def get_thrust_level(self):
        return self.thrust_level

    def get_brake_level(self):
        return self.brake_level

    def hit(self, value, position):
        Collisions_Object.hit(self, value, position)

    def update_kinetics(self, dts):
        Destroyable_Machine.update_kinetics(self, dts)