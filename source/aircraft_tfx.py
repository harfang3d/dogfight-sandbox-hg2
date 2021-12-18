# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from Machines import *


class TFX_Parameters:

    model_name = "TFX"
    instance_scene_name = "machines/tfx/TFX.scn"
    cockpit_instance_scene_name = "machines/tfx/TFX.scn"

    def __init__(self):
        # Aircraft constants:
        self.camera_track_distance = 45
        self.thrust_force = 20
        self.post_combution_force = self.thrust_force
        self.drag_coeff = hg.Vec3(0.033, 0.06666, 0.0002)
        self.wings_lift = 0.0005
        self.brake_drag = 0.006
        self.flaps_lift = 0.0025
        self.flaps_drag = 0.002
        self.angular_frictions = hg.Vec3(0.000175, 0.000125, 0.000275)  # pitch, yaw, roll
        self.speed_ceiling = 2500  # maneuverability is not guaranteed beyond this speed !
        self.angular_levels_inertias = hg.Vec3(3, 3, 3)
        self.max_safe_altitude = 25000
        self.max_altitude = 30000
        self.gear_height = 1.95227
        self.bottom_height = 0.748589

        # Weapons configuration:
        self.missiles_config = ["AIM_SL", "AIM_SL", "AIM_SL", "AIM_SL"]

        # Mobile parts:
        self.mobile_parts_definitions = [
            ["aileron_left", -45, 45, 0, "dummy_aileron_left", "Z"],
            ["aileron_right", -45, 45, 0, "dummy_aileron_right", "Z"],
            ["elevator", -11, 11, 0, "dummy_elevator", "X"],
            ["rudder_left", -45, 45, None, "dummy_rudder_left", "Z"],
            ["rudder_right", -45, 45, None, "dummy_rudder_right", "Z"]
        ]


class TFX(Aircraft, TFX_Parameters):

    @classmethod
    def init(cls, scene):
        print("TFX class init")

    def __init__(self, name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, nationality, start_pos, start_rot):

        self.gear_anim_play = None

        Aircraft.__init__(self, name, TFX_Parameters.model_name, scene, scene_physics, pipeline_ressource, TFX.instance_scene_name, nationality, start_pos, start_rot)
        TFX_Parameters.__init__(self)
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
        self.parts["aileron_left"]["level"] = self.angular_levels.z
        self.parts["aileron_right"]["level"] = -self.angular_levels.z
        self.parts["rudder_left"]["level"] = -self.angular_levels.y
        self.parts["rudder_right"]["level"] = -self.angular_levels.y

        Aircraft.update_mobile_parts(self, dts)


# Only animated aircraft, used for cockpit view


class TFX_Cockpit(AnimatedModel, TFX_Parameters):

    def __init__(self, name, scene, pipeline_ressource: hg.PipelineResources):
        self.main_aircraft = None
        AnimatedModel.__init__(self, name, TFX_Parameters.model_name, scene, pipeline_ressource, TFX_Parameters.cockpit_instance_scene_name)
        TFX_Parameters.__init__(self)
        self.define_mobile_parts(self.mobile_parts_definitions)

    def destroy(self):
        AnimatedModel.destroy_nodes(self)

    def set_main_aircraft(self, aircraft: TFX):
        self.main_aircraft = aircraft

    def update_mobile_parts(self, dts):
        if self.main_aircraft is not None:
            self.copy_mobile_parts_levels(self.main_aircraft.get_mobile_parts())
        AnimatedModel.update_mobile_parts(self, dts)
