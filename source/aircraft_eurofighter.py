# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from Machines import *

class Eurofighter_Parameters:

    model_name = "Eurofighter"
    instance_scene_name = "machines/eurofighter/eurofighter_anim.scn"
    cockpit_instance_scene_name = "machines/eurofighter/eurofighter_anim.scn"

    def __init__(self):
        # Aircraft constants:
        self.camera_track_distance = 30
        self.thrust_force = 13
        self.post_combution_force = self.thrust_force / 1.5
        self.drag_coeff = hg.Vec3(0.043, 0.07666, 0.0003)
        self.wings_lift = 0.0005
        self.brake_drag = 0.006
        self.flaps_lift = 0.0025
        self.flaps_drag = 0.002
        self.angular_frictions = hg.Vec3(0.000190, 0.000170, 0.000300)  # pitch, yaw, roll
        self.speed_ceiling = 2500  # maneuverability is not guaranteed beyond this speed !
        self.angular_levels_inertias = hg.Vec3(3, 3, 3)

        self.max_safe_altitude = 16800
        self.max_altitude = 26800

        self.gear_height = 2.02
        self.bottom_height = 1.125

        # Weapons configuration:
        self.missiles_config = ["Meteor", "Mica", "Mica", "Mica", "Mica", "Meteor"]

        # Mobile parts:

        self.mobile_parts_definitions = [
            ["aileron_left", -20, 20, 0, "dummy_wing_flap_l", "X"],
            ["aileron_right", -20, 20, 0, "dummy_wing_flap_r", "X"],
            ["elevator", -45, 45, 0, "dummy_elevator", "X"],
            ["rudder", -30, 30, 0, "rudder", "Y"],
            ["brake_flap", 0, 33.1, 0, "dummy_brake_flap", "X"],
            ["brake_handle", -47.4522, 0, 0, "dummy_brake_handle", "X"]
            ]

        self.brake_flap_a = 1
        self.brake_flap_v = 0
        self.brake_flap_vmax = 1
        self.current_brake_flap_level = 0


class Eurofighter(Aircraft, Eurofighter_Parameters):


    @classmethod
    def init(cls, scene):
        print("Eurofighter class init")

    def __init__(self, name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, nationality, start_pos, start_rot):

        self.gear_anim_play = None

        Aircraft.__init__(self, name, Eurofighter_Parameters.model_name, scene, scene_physics, pipeline_ressource, Eurofighter_Parameters.instance_scene_name, nationality, start_pos, start_rot)
        Eurofighter_Parameters.__init__(self)
        self.define_mobile_parts(self.mobile_parts_definitions)
        self.add_device(Gear("Gear", self, scene, self.get_animation("gear_open"), self.get_animation("gear_close")))
        self.setup_bounds_positions()

    def update_mobile_parts(self, dts):

        self.parts["aileron_left"]["level"] = self.angular_levels.z
        self.parts["aileron_right"]["level"] = -self.angular_levels.z
        self.parts["elevator"]["level"] = self.angular_levels.x
        self.parts["rudder"]["level"] = -self.angular_levels.y

        if self.current_brake_flap_level < self.brake_level:
            self.brake_flap_v = max(-self.brake_flap_vmax, min(self.brake_flap_vmax, self.brake_flap_v + self.brake_flap_a * dts))
        else:
            self.brake_flap_v = min(self.brake_flap_vmax, max(-self.brake_flap_vmax, self.brake_flap_v - self.brake_flap_a * dts))
        m = self.current_brake_flap_level
        self.current_brake_flap_level = self.current_brake_flap_level + self.brake_flap_v * dts
        if (m < self.brake_level < self.current_brake_flap_level) or (m > self.brake_level > self.current_brake_flap_level):
            self.current_brake_flap_level = self.brake_level
            self.brake_flap_v = 0
        if self.current_brake_flap_level < 0:
            self.current_brake_flap_level = 0
            self.brake_flap_v = 0
        if self.current_brake_flap_level > 1:
            self.current_brake_flap_level = 1
            self.brake_flap_v = 0

        self.parts["brake_flap"]["level"] = pow(self.current_brake_flap_level, 0.4)
        self.parts["brake_handle"]["level"] = -self.current_brake_flap_level

        Aircraft.update_mobile_parts(self, dts)


# Only animated aircraft, used for cockpit view

class Eurofighter_Cockpit(AnimatedModel, Eurofighter_Parameters):

    def __init__(self, name, scene, pipeline_ressource: hg.PipelineResources):
        self.main_aircraft = None
        AnimatedModel.__init__(self, name, Eurofighter_Parameters.model_name, scene, pipeline_ressource, Eurofighter_Parameters.cockpit_instance_scene_name)
        Eurofighter_Parameters.__init__(self)
        self.define_mobile_parts(self.mobile_parts_definitions)

    def destroy(self):
        AnimatedModel.destroy_nodes(self)

    def set_main_aircraft(self, aircraft: Eurofighter):
        self.main_aircraft = aircraft

    def update_mobile_parts(self, dts):
        if self.main_aircraft is not None:
            self.copy_mobile_parts_levels(self.main_aircraft.get_mobile_parts())
        AnimatedModel.update_mobile_parts(self, dts)
