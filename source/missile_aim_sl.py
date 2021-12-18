# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from random import uniform
from Machines import *


class AIM_SL(Missile):
    model_name = "AIM_SL"
    instance_scene_name = "weaponry/missile_aim_sl.scn"

    @classmethod
    def init(cls, scene):
        print("AIM-SL missile class init")

    def __init__(self, name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, nationality):
        Missile.__init__(self, name, AIM_SL.model_name, nationality, scene, scene_physics, pipeline_ressource, AIM_SL.instance_scene_name)

        self.f_thrust = 120
        self.smoke_parts_distance = 1.44374
        self.angular_frictions = hg.Vec3(0.00008, 0.00008, 0.00008)  # pitch, yaw, roll
        self.drag_coeff = hg.Vec3(0.37, 0.37, 0.0003)
        self.life_delay = 20
        self.smoke_delay = 1

    def get_hit_damages(self):
        return uniform(0.25, 0.35)

