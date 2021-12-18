# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from random import uniform
from Machines import *


class Mica(Missile):
    model_name = "Mica"
    instance_scene_name = "weaponry/missile_mica.scn"

    @classmethod
    def init(cls, scene):
        print("Mica missile class init")


    def __init__(self, name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, nationality):
        Missile.__init__(self, name, Mica.model_name, nationality, scene, scene_physics, pipeline_ressource, Mica.instance_scene_name)

        self.f_thrust = 150
        self.smoke_parts_distance = 1.44374
        self.angular_frictions = hg.Vec3(0.00014, 0.00014, 0.00014)  # pitch, yaw, roll
        self.drag_coeff = hg.Vec3(0.37, 0.37, 0.0003)
        self.life_delay = 15
        self.smoke_delay = 1

    def get_hit_damages(self):
        return uniform(0.20, 0.30)
