# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from Machines import *
from math import radians


class F16_Parameters:

    model_name = "F16"
    instance_scene_name = "machines/f16/F16_rigged.scn"

    def __init__(self):
        # Aircraft constants:
        self.camera_track_distance = 35
        self.thrust_force = 15
        self.post_combution_force = self.thrust_force

        self.drag_coeff = hg.Vec3(0.033, 0.06666, 0.0002)

        self.wings_lift = 0.0005
        self.brake_drag = 0.006
        self.flaps_lift = 0.0025
        self.flaps_drag = 0.002
        self.speed_ceiling = 1750  # maneuverability is not guaranteed beyond this speed !

        self.angular_levels_inertias = hg.Vec3(3, 3, 3)
        self.angular_frictions = hg.Vec3(0.000175, 0.000125, 0.000275)  # pitch, yaw, roll

        self.mobile_parts_definitions = [
            ["aileron_left", -45, 45, 0, "dummy_flap_left", "X"],
            ["aileron_right", -45, 45, 0, "dummy_flap_right", "X"],
            ["elevator_left", -15, 15, 0, "dummy_elevator_left", "X"],
            ["elevator_right", -15, 15, 0, "dummy_elevator_right", "X"],
            ["rudder", -45, 45, 0, "dummy_rudder", "Z"]
        ]

        self.max_safe_altitude = 15700
        self.max_altitude = 25700
        self.gear_height = 2.504 * 0.8
        self.bottom_height = 1.3 * 0.8

        # Weapons configuration:
        self.missiles_config = ["AIM_SL", "AIM_SL", "Karaoke", "Karaoke", "Karaoke", "Karaoke", "CFT", "CFT", "Karaoke", "Karaoke", "Karaoke", "Karaoke"]


class F16(Aircraft, F16_Parameters):

    @classmethod
    def init(cls, scene):
        print("F16 class init")

    def __init__(self, name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, nationality, start_pos, start_rot):
        self.gear_anim_play = None
        Aircraft.__init__(self, name, F16_Parameters.model_name, scene, scene_physics, pipeline_ressource, F16.instance_scene_name, nationality, start_pos, start_rot)
        F16_Parameters.__init__(self)
        self.define_mobile_parts(self.mobile_parts_definitions)
        self.add_device(Gear("Gear", self, scene, self.get_animation("gear_open"), self.get_animation("gear_close")))
        self.setup_bounds_positions()

    def update_mobile_parts(self, dts):

        self.parts["aileron_left"]["level"] = -self.angular_levels.z
        self.parts["aileron_right"]["level"] = self.angular_levels.z
        self.parts["elevator_left"]["level"] = self.angular_levels.x
        self.parts["elevator_right"]["level"] = self.angular_levels.x
        self.parts["rudder"]["level"] = self.angular_levels.y
        Aircraft.update_mobile_parts(self, dts)
