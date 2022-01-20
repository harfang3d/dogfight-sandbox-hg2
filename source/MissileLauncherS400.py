# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg

from Machines import *

class MissileLauncherS400(LandVehicle):
	model_name = "Missile_Launcher"
	instance_scene_name = "machines/missile_launcher/missile_launcher_exp.scn"

	def __init__(self, name, scene, scene_physics, pipeline_ressource: hg.PipelineResources, nationality, start_position, start_rotation):
		LandVehicle.__init__(self, name, MissileLauncherS400.model_name, scene, scene_physics, pipeline_ressource, MissileLauncherS400.instance_scene_name, nationality, start_position, start_rotation)
		self.type = Destroyable_Machine.TYPE_MISSILE_LAUNCHER

		self.brake_level = 1

		self.add_device(MissileLauncherUserControlDevice("UserControlDevice", self, "scripts/missile_launcher_user_inputs_mapping.json"))

		td = TargettingDevice("TargettingDevice", self, True)
		self.add_device(td)
		td.set_target_lock_range(2000, 20000)
		td.flag_front_lock_cone = False

		self.missiles_config = ["S400", "S400", "S400", "S400"]
		self.missiles_slots = self.get_missiles_slots()
		self.add_device(MissilesDevice("MissilesDevice", self, self.missiles_slots))

		self.plateform = None

		# Views parameters
		self.camera_track_distance = 100
		self.camera_follow_distance = 100
		self.camera_tactical_distance = 100
		self.camera_tactical_min_altitude = 1


	def destroy(self):

		md = self.get_device("MissilesDevice")
		if md is not None:
			md.destroy()

		self.destroy_nodes()
		self.flag_destroyed = True

	def set_platform(self, plateform: hg.Node):
		self.plateform = plateform
		self.start_position = self.plateform.GetTransform().GetPos()
		self.start_rotation = self.plateform.GetTransform().GetRot()
		self.parent_node.GetTransform().SetPos(self.start_position)
		self.parent_node.GetTransform().SetRot(self.start_rotation)

	# =========================== Missiles

	def get_missiles_slots(self):
		return self.get_slots("missile_slot")

	def get_num_missiles_slots(self):
		return len(self.missiles_slots)

	def rearm(self):
		self.set_health_level(1)
		md = self.get_device("MissilesDevice")
		if md is not None:
			md.rearm()

	#=========================== Physics


	def update_kinetics(self, dts):
		if self.activated:
			if self.custom_matrix is not None:
				matrix = self.custom_matrix
			else:
				matrix = self.get_parent_node().GetTransform().GetWorld()
			if self.custom_v_move is not None:
				v_move = self.custom_v_move
			else:
				v_move = self.v_move

			if not self.flag_crashed:
				self.v_move = v_move

			pos = hg.GetT(matrix)

			if not self.flag_custom_physics_mode:
				pos += self.v_move * dts

			# Collisions
			if self.plateform is not None:
				p_pos = self.plateform.GetTransform().GetPos()
				alt = p_pos.y
			else:
				alt = Physics.get_terrain_altitude(pos)

			if pos.y < alt:
				pos.y += (alt - pos.y) * 0.1 * 60 * dts
				if self.v_move.y < 0: self.v_move.y *= pow(0.8, 60 * dts)
				# b = min(1, self.brake_level + (1 - health_wreck_factor))
				b = self.brake_level
				self.v_move *= ((b * pow(0.98, 60 * dts)) + (1 - b))

			else:
				self.v_move += Physics.F_gravity * dts

			self.parent_node.GetTransform().SetPos(pos)

			self.update_devices(dts)  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

			self.update_mobile_parts(dts)
			self.update_feedbacks(dts)
