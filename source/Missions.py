# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from Animations import *
import tools
from random import uniform
from math import radians
import json
import network_server as netws
from overlays import *
from MachineDevice import *

class Mission:

	def __init__(self, title, num_ennemies, num_allies, num_carriers_ennemies, num_carriers_allies, setup_players, end_test, end_phase_update):
		self.title = title
		self.ennemies = num_ennemies
		self.allies = num_allies
		self.allies_carriers = num_carriers_allies
		self.ennemies_carriers = num_carriers_ennemies
		self.setup_players_f = setup_players
		self.end_test_f = end_test
		self.update_end_phase_f = end_phase_update
		self.failed = False
		self.aborted = False

	def reset(self):
		self.failed = False
		self.aborted = False

	def setup_players(self, main):
		self.setup_players_f(main)

	def end_test(self, main):
		return self.end_test_f(main)

	def update_end_phase(self, main, dts):
		self.update_end_phase_f(main, dts)

class Missions:
	beep_ref = None
	beep_state = None
	beep_source = None

	validation_ref = None
	validation_state = None
	validation_source = None

	# animations mission:
	am_start = False
	am_anim_x_prec = None
	am_anim_a_prec = None
	am_anim_x_new = None
	am_anim_a_new = None
	am_mission_id_prec = 0
	am_t = 0

	missions = []
	mission_id = 1

	@classmethod
	def display_mission_title(cls, main, fade_lvl, dts, yof7):
		mcr = 1
		mcg = 0.6
		mcb = 0.1

		if not cls.am_start:
			mx = 0.5
			mc = hg.Color(mcr, mcg, mcb, 1) * fade_lvl
			mid = cls.mission_id

			if cls.mission_id < len(cls.missions) - 1 and main.keyboard.Pressed(hg.K_Right):
				cls.am_start = True
				mcpt = 1
				xpd = 0
				xns = 1

			elif cls.mission_id > 0 and main.keyboard.Pressed(hg.K_Left):
				cls.am_start = True
				mcpt = -1
				xpd = 1
				xns = 0

			if cls.am_start:
				cls.beep_source = hg.PlayStereo(cls.beep_ref, cls.beep_state)
				hg.SetSourceVolume(cls.beep_source, 0.05)
				cls.am_mission_id_prec = cls.mission_id
				cls.mission_id += mcpt
				cls.am_t = 0
				cls.am_anim_x_prec = Animation(0, 0.5, 0.5, xpd)
				cls.am_anim_a_prec = Animation(0, 0.5, 1, 0)
				cls.am_anim_x_new = Animation(0, 0.2, xns, 0.5)
				cls.am_anim_a_new = Animation(0, 0.2, 0, 1)
				mid = cls.am_mission_id_prec

		else:
			cls.am_t += dts
			cls.am_anim_x_prec.update(cls.am_t)
			cls.am_anim_x_new.update(cls.am_t)
			cls.am_anim_a_prec.update(cls.am_t)
			cls.am_anim_a_new.update(cls.am_t)

			mx = cls.am_anim_x_new.v
			mc = hg.Color(mcr, mcg, mcb, cls.am_anim_a_new.v) * fade_lvl

			mxprec = cls.am_anim_x_prec.v
			mcprec = hg.Color(mcr, mcg, mcb, cls.am_anim_a_prec.v) * fade_lvl

			Overlays.add_text2D( Missions.missions[cls.am_mission_id_prec].title, hg.Vec2(mxprec, 671 / 900 + yof7), 0.02, mcprec, main.hud_font, hg.DTHA_Center)
			mid = cls.mission_id

			if cls.am_anim_a_new.flag_end and cls.am_anim_x_new.flag_end and cls.am_anim_x_prec.flag_end and cls.am_anim_a_prec:
				cls.am_start = False

		Overlays.add_text2D(cls.missions[mid].title, hg.Vec2(mx, 671 / 900 + yof7), 0.02, mc, main.hud_font, hg.DTHA_Center)
		Overlays.add_text2D( "<- choose your mission ->", hg.Vec2(0.5, 701 / 900 + yof7), 0.012, hg.Color(1, 0.9, 0.3, fade_lvl * 0.8), main.hud_font, hg.DTHA_Center)

		if main.keyboard.Pressed(hg.K_Space):
			cls.validation_source = hg.PlayStereo(cls.validation_ref, cls.validation_state)
			hg.SetSourceVolume(cls.validation_source, 1)

	@classmethod
	def get_current_mission(cls):
		return cls.missions[cls.mission_id]

	@classmethod
	def aircrafts_starts_on_carrier(cls, aircrafts, carrier, start, y_orientation, distance, liftoff_delay=0, liftoff_offset=1):
		p, r = carrier.get_aircraft_start_point(0)
		carrier_alt = p.y
		carrier_mat = hg.TransformationMat4(carrier.get_parent_node().GetTransform().GetPos(), carrier.get_parent_node().GetTransform().GetRot())
		for i, aircraft in enumerate(aircrafts):
			ia_ctrl = aircraft.get_device("IAControlDevice")
			if ia_ctrl is not None:
				ia_ctrl.IA_liftoff_delay = liftoff_delay
			aircraft.flag_landed = True
			liftoff_delay += liftoff_offset
			start += distance
			gear = aircraft.get_device("Gear")
			if gear is not None:
				bottom_height = gear.gear_height
				gear.record_start_state(True)
				gear.reset()
			else:
				bottom_height = aircraft.bottom_height
			start.y = carrier_alt + bottom_height
			mat = carrier_mat * hg.TransformationMat4(start, hg.Vec3(0, y_orientation, 0))
			aircraft.reset_matrix(hg.GetT(mat), hg.GetR(mat))
			aircraft.record_start_state()

	@classmethod
	def setup_aircrafts_on_carrier(cls, players, aircraft_carriers, start_time):
		na = len(players)
		nc = len(aircraft_carriers)
		na_row = na // (2 * nc)

		for i in range(nc):
			n0 = na_row * (2 * i)
			n1 = na_row * (2 * i + 1)
			n2 = na_row * (2 * i + 2)
			if na - n2 <= (na_row+1):
				n2 = na
			cls.aircrafts_starts_on_carrier(players[n0:n1], aircraft_carriers[i], hg.Vec3(10, 19.5, 80), 0, hg.Vec3(0, 0, -18), start_time + na_row * 2 * i, 2)
			cls.aircrafts_starts_on_carrier(players[n1:n2], aircraft_carriers[i], hg.Vec3(-10, 19.5, 62), 0, hg.Vec3(0, 0, -18), start_time + 1 + na_row * 2 * i, 2)

	@classmethod
	def aircrafts_starts_in_sky(cls, aircrafts, center: hg.Vec3, range: hg.Vec3, y_orientations_range: hg.Vec2, speed_range: hg.Vec2):
		for i, ac in enumerate(aircrafts):
			# ac.reset_matrix(hg.Vec3(uniform(center.x-range.x/2, center.x+range.x/2), uniform(center.y-range.y/2, center.y+range.y/2), uniform(center.z-range.z/2, center.z+range.z/2)), hg.Vec3(0, radians(uniform(y_orientations_range.x, y_orientations_range.y)), 0))

			ac.reset_matrix(hg.Vec3(uniform(center.x - range.x / 2, center.x + range.x / 2), uniform(center.y - range.y / 2, center.y + range.y / 2), uniform(center.z - range.z / 2, center.z + range.z / 2)), hg.Vec3(0, radians(uniform(y_orientations_range.x, y_orientations_range.y)), 0))
			gear = ac.get_device("Gear")
			if gear is not None:
				gear.record_start_state(False)
				gear.reset()
			ac.set_linear_speed(uniform(speed_range.x, speed_range.y))
			ac.flag_landed = False
			ac.record_start_state()

	@classmethod
	def setup_carriers(cls, carriers, start_pos, dist, y_orientation):
		for carrier in carriers:
			carrier.reset_matrix(start_pos, hg.Vec3(0, y_orientation, 0))
			start_pos += dist


# ============================= Training

	@classmethod
	def mission_setup_training(cls, main):

		mission = cls.get_current_mission()
		main.create_aircraft_carriers(mission.allies_carriers, mission.ennemies_carriers)
		main.create_players(mission.allies, mission.ennemies)

		cls.setup_carriers(main.aircraft_carrier_allies, hg.Vec3(0, 0, 0), hg.Vec3(500, 0, 100), 0)

		n = len(main.players_allies)
		# if n == 1:

		cls.aircrafts_starts_on_carrier(main.players_allies, main.aircraft_carrier_allies[0], hg.Vec3(10, 19.5, 40), 0, hg.Vec3(0, 0, -20))

		# cls.aircrafts_starts_in_sky(main.players_allies, hg.Vec3(1000, 2000, 0), hg.Vec3(1000, 1000, 20000), hg.Vec2(-180, 180), hg.Vec2(600 / 3.6, 800 / 3.6))

		# elif n > 1:
		#	cls.aircrafts_starts_on_carrier(main.players_allies[0:n // 2], main.aircraft_carrier_allies[0], hg.Vec3(10, 19.5, 40), 0, hg.Vec3(0, 0, -20))
		#	cls.aircrafts_starts_on_carrier(main.players_allies[n // 2:n], main.aircraft_carrier_allies[0], hg.Vec3(-10, 19.5, 60), 0, hg.Vec3(0, 0, -20))

		fps_start_matrix = main.aircraft_carrier_allies[0].fps_start_point.GetTransform().GetWorld()
		main.camera_fps.GetTransform().SetWorld(fps_start_matrix)

		lt = []
		for carrier in main.aircraft_carrier_allies:
			lt += carrier.landing_targets
		for ac in main.players_allies:
			ac.set_landing_targets(lt)
			ia = ac.get_device("IAControlDevice")
			if ia is not None:
				ia.activate()

		# ------- Missile Launcher:
		main.create_missile_launchers(0, 1)

		plateform = main.scene.GetNode("platform.S400")
		ml = main.missile_launchers_ennemies[0]
		ml.set_platform(plateform)

		# --------- Views setup
		main.setup_views_carousel(True)
		main.set_view_carousel("Aircraft_ally_" + str(main.num_players_allies))
		main.set_track_view("back")

		main.user_aircraft = main.get_player_from_caroursel_id(main.views_carousel[main.views_carousel_ptr])
		main.user_aircraft.set_focus()

		ia = main.user_aircraft.get_device("IAControlDevice")
		if ia is not None:
			ia.set_IA_landing_target(main.aircraft_carrier_allies[0].landing_targets[1])
			ia.deactivate()
		uctrl = main.user_aircraft.get_device("UserControlDevice")
		if uctrl is not None:
			uctrl.activate()

		main.init_playground()

	# if main.num_players_allies < 4:
	# main.user_aircraft.set_thrust_level(1)
	# main.user_aircraft.activate_post_combustion()

	@classmethod
	def mission_training_end_test(cls, main):
		mission = cls.get_current_mission()
		allies_wreck = 0
		for ally in main.players_allies:
			if ally.wreck: allies_wreck += 1

		if main.num_players_allies == allies_wreck:
			mission.failed = True
			print("MISSION FAILED !")
			return True

		return False

	@classmethod
	def mission_training_end_phase_update(cls, main, dts):
		mission = cls.get_current_mission()
		if mission.failed:
			msg_title = "Mission Failed !"
			msg_debriefing = " You need more lessons commander..."
		elif mission.aborted:
			msg_title = "Training aborted !"
			msg_debriefing = "Ready for fight ?"
		else:
			msg_title = "Training successful !"
			msg_debriefing = "Congratulation commander !"
		Overlays.add_text2D(msg_title, hg.Vec2(0.5, 771 / 900 - 0.15), 0.04, hg.Color(1, 0.9, 0.3, 1), main.title_font, hg.DTHA_Center)
		Overlays.add_text2D(msg_debriefing, hg.Vec2(0.5, 701 / 900 - 0.15), 0.02, hg.Color(1, 0.9, 0.8, 1), main.hud_font, hg.DTHA_Center)

# ============================= Basic fight

	@classmethod
	def mission_setup_players(cls, main):
		mission = cls.get_current_mission()
		main.create_aircraft_carriers(mission.allies_carriers, mission.ennemies_carriers)
		main.create_players(mission.allies, mission.ennemies)

		cls.setup_carriers(main.aircraft_carrier_allies, hg.Vec3(0, 0, 0), hg.Vec3(500, 0, 100), 0)
		cls.setup_carriers(main.aircraft_carrier_ennemies, hg.Vec3(-17000, 0, 0), hg.Vec3(500, 0, -150), radians(90))

		main.init_playground()

		n = len(main.players_allies)
		if n == 1:
			cls.aircrafts_starts_on_carrier(main.players_allies, main.aircraft_carrier_allies[0], hg.Vec3(10, 19.5, 40), 0, hg.Vec3(0, 0, -20))
		elif n > 1:
			cls.aircrafts_starts_on_carrier(main.players_allies[0:n // 2], main.aircraft_carrier_allies[0], hg.Vec3(10, 19.5, 40), 0, hg.Vec3(0, 0, -20), 2, 2)
			cls.aircrafts_starts_on_carrier(main.players_allies[n // 2:n], main.aircraft_carrier_allies[0], hg.Vec3(-10, 19.5, 60), 0, hg.Vec3(0, 0, -20), 3, 2)

		n = len(main.players_ennemies)
		if n < 3:
			cls.aircrafts_starts_in_sky(main.players_ennemies, hg.Vec3(-5000, 1000, 0), hg.Vec3(1000, 500, 2000), hg.Vec2(-180, 180), hg.Vec2(800 / 3.6, 600 / 3.6))
		else:
			cls.aircrafts_starts_in_sky(main.players_ennemies[0:2], hg.Vec3(-5000, 1000, 0), hg.Vec3(1000, 500, 2000), hg.Vec2(-180, 180), hg.Vec2(800 / 3.6, 600 / 3.6))
			cls.aircrafts_starts_on_carrier(main.players_ennemies[2:n], main.aircraft_carrier_ennemies[0], hg.Vec3(-10, 19.5, 60), 0, hg.Vec3(0, 0, -20), 2, 1)

		for i, ac in enumerate(main.players_allies):
			ia = ac.get_device("IAControlDevice")
			if ia is not None:
				ia.activate()

		for i, ac in enumerate(main.players_ennemies):
			ia = ac.get_device("IAControlDevice")
			if ia is not None:
				ia.activate()

		main.setup_views_carousel(False)
		main.set_view_carousel("Aircraft_ally_" + str(main.num_players_allies))
		main.set_track_view("back")

		main.user_aircraft = main.get_player_from_caroursel_id(main.views_carousel[main.views_carousel_ptr])
		main.user_aircraft.set_focus()

		if main.user_aircraft is not None:
			ia = main.user_aircraft.get_device("IAControlDevice")
			if ia is not None:
				ia.deactivate()
			uctrl = main.user_aircraft.get_device("UserControlDevice")
			if uctrl is not None:
				uctrl.activate()
			if main.num_players_allies < 3:
				main.user_aircraft.reset_thrust_level(1)
				main.user_aircraft.activate_post_combustion()

	@classmethod
	def mission_one_against_x_end_test(cls, main):
		mission = cls.get_current_mission()
		ennemies_wreck = 0
		allies_wreck = 0
		for ennemy in main.players_ennemies:
			if ennemy.wreck: ennemies_wreck += 1
		for ally in main.players_allies:
			if ally.wreck: allies_wreck += 1

		if main.num_players_ennemies == ennemies_wreck:
			mission.failed = False
			return True
		if main.num_players_allies == allies_wreck:
			mission.failed = True
			return True

		return False

	@classmethod
	def mission_one_against_x_end_phase_update(cls, main, dts):
		mission = cls.get_current_mission()
		if mission.failed:
			msg_title = "Mission Failed !"
			msg_debriefing = " R.I.P. Commander..."
		elif mission.aborted:
			msg_title = "Mission aborted !"
			msg_debriefing = "We hope you do better next time !"
		else:
			msg_title = "Mission successful !"
			msg_debriefing = "Congratulation commander !"
		Overlays.add_text2D(msg_title, hg.Vec2(0.5, 771 / 900 - 0.15), 0.04, hg.Color(1, 0.9, 0.3, 1), main.title_font, hg.DTHA_Center)
		Overlays.add_text2D(msg_debriefing, hg.Vec2(0.5, 701 / 900 - 0.15), 0.02, hg.Color(1, 0.9, 0.8, 1), main.hud_font, hg.DTHA_Center)

# ============================ War fight
	@classmethod
	def mission_total_war_setup_players(cls, main):

		mission = cls.get_current_mission()
		main.create_aircraft_carriers(mission.allies_carriers, mission.ennemies_carriers)
		main.create_players(mission.allies, mission.ennemies)

		cls.setup_carriers(main.aircraft_carrier_allies, hg.Vec3(0, 0, 0), hg.Vec3(300, 0, 25), 0)
		cls.setup_carriers(main.aircraft_carrier_ennemies, hg.Vec3(-20000, 0, 0), hg.Vec3(50, 0, -350), radians(90))


		cls.setup_aircrafts_on_carrier(main.players_allies, main.aircraft_carrier_allies, 0)

		n = len(main.players_ennemies)
		cls.aircrafts_starts_in_sky(main.players_ennemies[0:n // 2], hg.Vec3(-8000, 1000, 0), hg.Vec3(2000, 500, 2000), hg.Vec2(-180, -175), hg.Vec2(800 / 3.6, 600 / 3.6))

		cls.setup_aircrafts_on_carrier(main.players_ennemies[n//2:n], main.aircraft_carrier_ennemies, 60)

		main.init_playground()

		for i, ac in enumerate(main.players_allies):
			ia = ac.get_device("IAControlDevice")
			if ia is not None:
				ia.activate()

		for i, ac in enumerate(main.players_ennemies):
			ia = ac.get_device("IAControlDevice")
			if ia is not None:
				ia.activate()

		main.setup_views_carousel()
		main.set_view_carousel("Aircraft_ally_" + str(main.num_players_allies))
		main.set_track_view("back")

		main.user_aircraft = main.get_player_from_caroursel_id(main.views_carousel[main.views_carousel_ptr])
		main.user_aircraft.set_focus()

		if main.user_aircraft is not None:
			ia = main.user_aircraft.get_device("IAControlDevice")
			if ia is not None:
				ia.deactivate()
			uctrl = main.user_aircraft.get_device("UserControlDevice")
			if uctrl is not None:
				uctrl.activate()
			if main.num_players_allies < 4:
				main.user_aircraft.reset_thrust_level(1)
				main.user_aircraft.activate_post_combustion()

	@classmethod
	def mission_war_end_test(cls, main):
		mission = cls.get_current_mission()
		if main.keyboard.Pressed(hg.K_F5):
			for pl in main.players_allies:
				pl.flag_IA_start_liftoff = True
			for pl in main.players_ennemies:
				pl.flag_IA_start_liftoff = True
		# Pour le moment, même test de fin de mission
		return cls.mission_one_against_x_end_test(main)

	@classmethod
	def mission_war_end_phase_update(cls, main, dts):
		mission = cls.get_current_mission()
		if mission.failed:
			msg_title = "Mission Failed !"
			msg_debriefing = " R.I.P. Commander..."
		elif mission.aborted:
			msg_title = "Mission aborted !"
			msg_debriefing = "We hope you do better next time !"
		else:
			msg_title = "Mission successful !"
			msg_debriefing = "Congratulation commander !"

		Overlays.add_text2D(msg_title, hg.Vec2(0.5, 771 / 900 - 0.15), 0.04, hg.Color(1, 0.9, 0.3, 1), main.title_font, hg.DTHA_Center)
		Overlays.add_text2D(msg_debriefing, hg.Vec2(0.5, 701 / 900 - 0.15), 0.02, hg.Color(1, 0.9, 0.8, 1), main.hud_font, hg.DTHA_Center)

# ============================ Client / Server mode
	@classmethod
	def network_mode_setup(cls, main):
		mission = cls.get_current_mission()
		main.flag_network_mode = True

		file_name = "scripts/network_mission_config.json"
		file = hg.OpenText(file_name)
		if not file:
			print("Can't open mission configuration json file : " + file_name)
		else:
			json_script = hg.ReadString(file)
			hg.Close(file)
			if json_script != "":
				script_parameters = json.loads(json_script)
				mission.allies = script_parameters["aircrafts_allies"]
				mission.ennemies = script_parameters["aircrafts_ennemies"]
				mission.allies_carriers = script_parameters["aircraft_carriers_allies_count"]
				mission.ennemies_carriers = script_parameters["aircraft_carriers_enemies_count"]
			else:
				print("Mission configuration json file empty : " + file_name)

		main.create_aircraft_carriers(mission.allies_carriers, mission.ennemies_carriers)
		main.create_players(mission.allies, mission.ennemies)

		cls.setup_carriers(main.aircraft_carrier_allies, hg.Vec3(0, 0, 0), hg.Vec3(500, 0, 100), 0)
		cls.setup_carriers(main.aircraft_carrier_ennemies, hg.Vec3(-17000, 0, 0), hg.Vec3(500, 0, -150), radians(90))

		main.init_playground()

		# Sets aircrafts landed on carriers:

		n = len(main.players_allies)
		if n == 1:
			cls.aircrafts_starts_on_carrier(main.players_allies, main.aircraft_carrier_allies[0], hg.Vec3(10, 19.5, 40), 0, hg.Vec3(0, 0, -20))
		elif n > 1:
			cls.aircrafts_starts_on_carrier(main.players_allies[0:n // 2], main.aircraft_carrier_allies[0], hg.Vec3(10, 19.5, 40), 0, hg.Vec3(0, 0, -20), 2, 2)
			cls.aircrafts_starts_on_carrier(main.players_allies[n // 2:n], main.aircraft_carrier_allies[0], hg.Vec3(-10, 19.5, 60), 0, hg.Vec3(0, 0, -20), 3, 2)

		n = len(main.players_ennemies)
		if n == 1:
			cls.aircrafts_starts_on_carrier(main.players_ennemies, main.aircraft_carrier_ennemies[0], hg.Vec3(10, 19.5, 40), 0, hg.Vec3(0, 0, -20))
		elif n > 1:
			cls.aircrafts_starts_on_carrier(main.players_ennemies[0:n // 2], main.aircraft_carrier_ennemies[0], hg.Vec3(10, 19.5, 40), 0, hg.Vec3(0, 0, -20), 2, 2)
			cls.aircrafts_starts_on_carrier(main.players_ennemies[n // 2:n], main.aircraft_carrier_ennemies[0], hg.Vec3(-10, 19.5, 60), 0, hg.Vec3(0, 0, -20), 3, 2)

		# Deactivate IA:
		for i, ac in enumerate(main.players_allies):
			ia = ac.get_device("IAControlDevice")
			if ia is not None:
				ia.deactivate()

		for i, ac in enumerate(main.players_ennemies):
			ia = ac.get_device("IAControlDevice")
			if ia is not None:
				ia.deactivate()

		# ------- Missile Launcher:
		main.create_missile_launchers(0, 1)

		plateform = main.scene.GetNode("platform.S400")
		ml = main.missile_launchers_ennemies[0]
		ml.set_platform(plateform)

		# --------- Views setup
		main.setup_views_carousel(True)
		main.set_view_carousel("Aircraft_ally_1")# + str(main.num_players_allies))
		main.set_track_view("back")

		main.init_playground()

		main.user_aircraft = main.get_player_from_caroursel_id(main.views_carousel[main.views_carousel_ptr])
		main.user_aircraft.set_focus()

		uctrl = main.user_aircraft.get_device("UserControlDevice")
		if uctrl is not None:
			uctrl.activate()

		netws.init_server(main)
		netws.start_server()

	@classmethod
	def network_mode_end_test(cls, main):
		"""
		mission = cls.get_current_mission()

		allies_wreck = 0
		for ally in main.players_allies:
			if ally.wreck:
				allies_wreck += 1

		if main.num_players_allies == allies_wreck:
			mission.failed = True
			return True
		"""
		return False

	@classmethod
	def network_mode_end_phase_update(cls, main, dts):
		if main.flag_network_mode:
			main.flag_network_mode = False
			netws.stop_server()
		mission = cls.get_current_mission()
		if mission.failed:
			msg_title = "Network aborted !"
			msg_debriefing = " Aircraft destroyed, TAB to restart"
		elif mission.aborted:
			msg_title = "Network aborted !"
			msg_debriefing = "TAB to restart"
		else:
			msg_title = "Successful !"
			msg_debriefing = "Congratulation commander !"
		Overlays.add_text2D(msg_title, hg.Vec2(0.5, 771 / 900 - 0.15), 0.04, hg.Color(1, 0.9, 0.3, 1), main.title_font, hg.DTHA_Center)
		Overlays.add_text2D(msg_debriefing, hg.Vec2(0.5, 701 / 900 - 0.15), 0.02, hg.Color(1, 0.9, 0.8, 1), main.hud_font, hg.DTHA_Center)

	@classmethod
	def init(cls):
		cls.beep_ref = hg.LoadWAVSoundAsset("sfx/blip.wav")
		cls.beep_state = tools.create_stereo_sound_state(hg.SR_Once)
		cls.beep_state.volume = 0.25

		cls.validation_ref = hg.LoadWAVSoundAsset("sfx/blip2.wav")
		cls.validation_state = tools.create_stereo_sound_state(hg.SR_Once)
		cls.validation_state.volume = 0.5

		cls.missions.append(Mission("Network mode", ["Eurofighter"], ["Rafale"], 1, 1, Missions.network_mode_setup, Missions.network_mode_end_test, Missions.network_mode_end_phase_update))

		cls.missions.append(Mission("Training with Rafale", [], ["Rafale"], 0, 1, Missions.mission_setup_training, Missions.mission_training_end_test, Missions.mission_training_end_phase_update))
		cls.missions.append(Mission("Training with Eurofighter", [], ["Eurofighter"], 0, 1, Missions.mission_setup_training, Missions.mission_training_end_test, Missions.mission_training_end_phase_update))
		cls.missions.append(Mission("Training with TFX", [], ["TFX"], 0, 1, Missions.mission_setup_training, Missions.mission_training_end_test, Missions.mission_training_end_phase_update))
		cls.missions.append(Mission("Training with F16", [], ["F16"], 0, 1, Missions.mission_setup_training, Missions.mission_training_end_test, Missions.mission_training_end_phase_update))
		#cls.missions.append(Mission("Training with F14", [], ["F14"], 0, 1, Missions.mission_setup_training, Missions.mission_training_end_test, Missions.mission_training_end_phase_update))
		#cls.missions.append(Mission("Training with F14 2", [], ["F14_2"], 0, 1, Missions.mission_setup_training, Missions.mission_training_end_test, Missions.mission_training_end_phase_update))

		cls.missions.append(Mission("One on one", ["Rafale"], ["Eurofighter"], 1, 1, Missions.mission_setup_players, Missions.mission_one_against_x_end_test, Missions.mission_one_against_x_end_phase_update))
		cls.missions.append(Mission("Fight against 2 ennemies", ["Rafale"] * 2, ["Eurofighter"], 1, 1, Missions.mission_setup_players, Missions.mission_one_against_x_end_test, Missions.mission_one_against_x_end_phase_update))
		cls.missions.append(Mission("Fight against 3 ennemies", ["Rafale"] * 1 + ["F16"] * 2, ["Eurofighter"], 1, 1, Missions.mission_setup_players, Missions.mission_one_against_x_end_test, Missions.mission_one_against_x_end_phase_update))
		cls.missions.append(Mission("Fight against 4 ennemies", ["Rafale"] * 2 + ["F16"] * 2, ["TFX", "Eurofighter"], 1, 1, Missions.mission_setup_players, Missions.mission_one_against_x_end_test, Missions.mission_one_against_x_end_phase_update))
		cls.missions.append(Mission("Fight against 5 ennemies", ["Rafale"] * 5, ["TFX", "Eurofighter", "F16"], 1, 1, Missions.mission_setup_players, Missions.mission_one_against_x_end_test, Missions.mission_one_against_x_end_phase_update))

		cls.missions.append(Mission("War: 5 allies against 5 ennemies", ["Rafale"] * 3 + ["Eurofighter"] * 2, ["TFX"] * 2 + ["F16"] * 2 + ["Eurofighter"] * 1, 1, 1, Missions.mission_setup_players, Missions.mission_war_end_test, Missions.mission_war_end_phase_update))
		#cls.missions.append(Mission("Total War: 12 allies against 12 ennemies", ["Rafale"] * 12, ["TFX"] * 4 + ["Eurofighter"] * 4 + ["F16"] * 4 + ["Eurofighter"] * 4, 2, 2, Missions.mission_total_war_setup_players, Missions.mission_war_end_test, Missions.mission_war_end_phase_update))
		#cls.missions.append(Mission("Crash test: 60 allies against 60 ennemies", ["Rafale"] * 30 + ["Eurofighter"] * 30, ["TFX"] * 30 + ["Eurofighter"] * 20 + ["F16"] * 10, 5, 5, Missions.mission_total_war_setup_players, Missions.mission_war_end_test, Missions.mission_war_end_phase_update))
