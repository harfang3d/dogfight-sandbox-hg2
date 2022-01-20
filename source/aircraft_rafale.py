# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from Machines import *

class Rafale_Parameters:

    model_name = "Rafale"
    instance_scene_name = "machines/rafale/rafale_rigged.scn"

    def __init__(self):
        # Aircraft constants:
        self.camera_track_distance = 30

        self.thrust_force = 15
        self.post_combution_force = self.thrust_force / 2
        self.drag_coeff = hg.Vec3(0.043, 0.07666, 0.0003)
        self.wings_lift = 0.0005
        self.brake_drag = 0.006
        self.flaps_lift = 0.0025
        self.flaps_drag = 0.002
        self.angular_frictions = hg.Vec3(0.000165, 0.000115, 0.000255)  # pitch, yaw, roll
        self.speed_ceiling = 2200  # maneuverability is not guaranteed beyond this speed !
        self.angular_levels_inertias = hg.Vec3(3, 3, 3)
        self.max_safe_altitude = 15240
        self.max_altitude = 25240 * 4

        self.gear_height = 2.28
        self.bottom_height = 0.78

        # Weapons configuration:
        self.missiles_config = ["Mica", "Meteor", "Meteor", "Meteor", "Meteor", "Mica"]

        # Mobile parts:

        self.mobile_parts_definitions = [
            ["aileron_left", -20, 20, 0, "dummy_rafale_wing_flap_l", "X"],
            ["aileron_right", -20, 20, 0, "dummy_rafale_wing_flap_r", "X"],
            ["elevator_left", -45, 45, 0, "dummy_rafale_elevator_l", "X"],
            ["elevator_right", -45, 45, 0, "dummy_rafale_elevator_r", "X"],
            ["rudder", -30, 30, 0, "rafale_rudder", "Y"]
        ]


class Rafale(Aircraft, Rafale_Parameters):

    @classmethod
    def init(cls, scene):
        print("Rafale class init")

    def __init__(self, name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, nationality, start_pos, start_rot):

        self.gear_anim_play = None

        Aircraft.__init__(self, name, Rafale_Parameters.model_name, scene, scene_physics, pipeline_ressource, Rafale.instance_scene_name, nationality, start_pos, start_rot)
        Rafale_Parameters.__init__(self)
        self.define_mobile_parts(self.mobile_parts_definitions)
        self.add_device(Gear("Gear", self, scene, self.get_animation("gear_open"), self.get_animation("gear_fr_close")))
        self.setup_bounds_positions()

    def update_mobile_parts(self, dts):

        self.parts["aileron_left"]["level"] = -self.angular_levels.z
        self.parts["aileron_right"]["level"] = self.angular_levels.z
        self.parts["elevator_left"]["level"] = -self.angular_levels.x
        self.parts["elevator_right"]["level"] = -self.angular_levels.x
        self.parts["rudder"]["level"] = -self.angular_levels.y
        Aircraft.update_mobile_parts(self, dts)
