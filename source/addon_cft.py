# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from random import uniform
from Machines import *


class CFT(Missile):
    model_name = "CFT"
    instance_scene_name = "weaponry/fuel_cft.scn"

    @classmethod
    def init(cls, scene):
        print("CFT class init")

    def __init__(self, name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, nationality):
        Missile.__init__(self, name, CFT.model_name, nationality, scene, scene_physics, pipeline_ressource, CFT.instance_scene_name)

        self.flag_armed = False
