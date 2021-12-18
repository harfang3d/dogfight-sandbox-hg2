# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from random import uniform
from Machines import *


class S400(Missile):
    model_name = "S400"
    instance_scene_name = "machines/S400/S400.scn"

    @classmethod
    def init(cls, scene):
        print("S400 missile class init")

    def __init__(self, name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, nationality):
        Missile.__init__(self, name, S400.model_name, nationality, scene, scene_physics, pipeline_ressource, S400.instance_scene_name)

        self.f_thrust = 60
        self.smoke_parts_distance = 1.44374
        self.angular_frictions = hg.Vec3(0.000025, 0.000025, 0.000025)  # pitch, yaw, roll
        self.drag_coeff = hg.Vec3(0.37, 0.37, 0.0003)
        self.life_delay = 100
        self.smoke_delay = 1.5

    def get_hit_damages(self):
        return uniform(0.2, 0.3)
