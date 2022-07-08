# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from Machines import *


class Miuss_Parameters:

    model_name = "Miuss"
    instance_scene_name = "machines/mius/miuss.scn"

    def __init__(self):
        # Aircraft constants:
        self.camera_track_distance = 30
        self.thrust_force = 20
        self.post_combution_force = self.thrust_force
        self.drag_coeff = hg.Vec3(0.033, 0.06666, 0.0002)
        self.wings_lift = 0.0005
        self.brake_drag = 0.006
        self.flaps_lift = 0.0025
        self.flaps_drag = 0.002
        self.angular_frictions = hg.Vec3(0.000175, 0.000125, 0.000275)  # pitch, yaw, roll
        self.speed_ceiling = 3000  # maneuverability is not guaranteed beyond this speed !
        self.angular_levels_inertias = hg.Vec3(3, 3, 3)
        self.max_safe_altitude = 60000
        self.max_altitude = 50000
        self.gear_height = 1.3
        self.bottom_height = 0.70

        # Weapons configuration:
        self.missiles_config = []

        # Mobile parts:
        self.mobile_parts_definitions = [
            ["elevator", -20, 20, 0, "dummy_elevator", "X"]
        ]


class Miuss(Aircraft, Miuss_Parameters):

    @classmethod
    def init(cls, scene):
        print("Miuss class init")

    def __init__(self, name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, nationality, start_pos, start_rot):

        self.gear_anim_play = None

        Aircraft.__init__(self, name, Miuss_Parameters.model_name, scene, scene_physics, pipeline_ressource, Miuss.instance_scene_name, nationality, start_pos, start_rot)
        Miuss_Parameters.__init__(self)
        self.define_mobile_parts(self.mobile_parts_definitions)
        gear = Gear("Gear", self, scene, self.get_animation("gear_open"), self.get_animation("gear_close"))
        gear.gear_moving_delay = 3
        self.add_device(gear)
        md = self.get_device("MissilesDevice")
        if md is not None:
            md.flag_hide_fitted_missiles = True
        self.setup_bounds_positions()

    def update_mobile_parts(self, dts):
        self.parts["elevator"]["level"] = -self.angular_levels.x

        Aircraft.update_mobile_parts(self, dts)

