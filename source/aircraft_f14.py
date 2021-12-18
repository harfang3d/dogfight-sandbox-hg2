# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg

from Machines import *


class F14_Parameters():
    model_name = "F14"
    instance_scene_name = "machines/aircraft/aircraft_blend.scn"
    cockpit_instance_scene_name = "machines/aircraft/aircraft_blend.scn"

    def __init__(self):
        # Aircraft constants:
        self.camera_track_distance = 40
        self.thrust_force = 10
        self.post_combution_force = self.thrust_force / 2
        self.drag_coeff = hg.Vec3(0.033, 0.06666, 0.0002)
        self.wings_lift = 0.0005
        self.brake_drag = 0.006
        self.flaps_lift = 0.0025
        self.flaps_drag = 0.002
        self.angular_frictions = hg.Vec3(0.000175, 0.000125, 0.000275)  # pitch, yaw, roll
        self.speed_ceiling = 1750  # maneuverability is not guaranteed beyond this speed !
        self.angular_levels_inertias = hg.Vec3(3, 3, 3)
        self.max_safe_altitude = 15700
        self.max_altitude = 25700

        self.gear_height = 3
        self.bottom_height = 2

        # Weapons configuration:
        self.missiles_config = ["Sidewinder", "Sidewinder", "Sidewinder", "Sidewinder"]

        # Mobile parts:

        self.wings_thresholds = hg.Vec2(500, 750)
        self.wings_level = 0
        self.wings_geometry_gain_friction = -0.0001

        self.mobile_parts_definitions = [
            ["aileron_left", -45, 45, 0, "dummy_aircraft_aileron_l", "X"],
            ["aileron_right", -45, 45, 0, "dummy_aircraft_aileron_r", "X"],
            ["elevator_left", -15, 15, 0, "dummy_aircraft_elevator_changepitch_l", "X"],
            ["elevator_right", -15, 15, 0, "dummy_aircraft_elevator_changepitch_r", "X"],
            ["rudder_left", -45 + 180, 45 + 180, 180, "aircraft_rudder_changeyaw_l", "Y"],
            ["rudder_right", -45, 45, 0, "aircraft_rudder_changeyaw_r", "Y"],
            ["wing_left", -45, 0, 0, "dummy_aircraft_configurable_wing_l", "Y"],
            ["wing_right", 0, 45, 0, "dummy_aircraft_configurable_wing_r", "Y"]
        ]

# Main Aircraft, with physics interactions

class F14(Aircraft, F14_Parameters):

    @classmethod
    def init(cls, scene):
        print("F14 class init")

    def __init__(self, name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, nationality, start_pos, start_rot):
        Aircraft.__init__(self, name, F14_Parameters.model_name, scene, scene_physics, pipeline_ressource, F14_Parameters.instance_scene_name, nationality, start_pos, start_rot)
        F14_Parameters.__init__(self)
        self.define_mobile_parts(self.mobile_parts_definitions)
        self.add_device(Gear("Gear", self)) #, scene, self.get_animation("gear_open"), self.get_animation("gear_close")))
        self.setup_bounds_positions()

    def update_mobile_parts(self, dts):
        self.parts["aileron_left"]["level"] = -self.angular_levels.z
        self.parts["aileron_right"]["level"] = -self.angular_levels.z
        self.parts["elevator_left"]["level"] = -self.angular_levels.x
        self.parts["elevator_right"]["level"] = -self.angular_levels.x
        self.parts["rudder_left"]["level"] = self.angular_levels.y
        self.parts["rudder_right"]["level"] = -self.angular_levels.y
        self.set_wings_level(self.get_linear_speed())
        Aircraft.update_mobile_parts(self, dts)

    def set_wings_level(self, frontal_speed):
        value = max(min((frontal_speed * 3.6 - self.wings_thresholds.x) / (self.wings_thresholds.y - self.wings_thresholds.x), 1), 0)
        self.wings_level = min(max(value, 0), 1)
        self.parts["wing_left"]["level"] = -value
        self.parts["wing_right"]["level"] = value

    def compute_z_drag(self):
        return Aircraft.compute_z_drag(self) + self.wings_geometry_gain_friction * self.wings_level

# Only animated aircraft, used for cockpit view

class F14_Cockpit(AnimatedModel, F14_Parameters):

    def __init__(self, name, scene, pipeline_ressource: hg.PipelineResources):
        self.main_aircraft = None
        AnimatedModel.__init__(self, name, F14_Parameters.model_name, scene, pipeline_ressource, F14_Parameters.cockpit_instance_scene_name)
        F14_Parameters.__init__(self)
        self.define_mobile_parts(self.mobile_parts_definitions)

    def destroy(self):
        AnimatedModel.destroy_nodes(self)

    def set_main_aircraft(self, aircraft:F14):
        self.main_aircraft = aircraft

    def update_mobile_parts(self, dts):
        if self.main_aircraft is not None:
            self.copy_mobile_parts_levels(self.main_aircraft.get_mobile_parts())
        AnimatedModel.update_mobile_parts(self, dts)
