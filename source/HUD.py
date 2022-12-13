# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.


import harfang as hg
from Machines import *
from MachineDevice import *
from MathsSupp import *
from Sprites import *
from random import *
from overlays import *
from MissileLauncherS400 import *


class HUD:

	@classmethod
	def init(cls, resolution: hg.Vec2):

		cls.color_inactive = hg.Color(0.2, 0.2, 0.2, 0.5)
		cls.color_wait_connect = hg.Color(1, 0.8, 0.8, 1)
		cls.color_connected = hg.Color(0.3, 0.3, 0.3, 1)

	# Texts:
	@staticmethod
	def hud_convert_coords(x, y, resolution):
		ratio = resolution.x / resolution.y
		return (x - resolution.x / 2) / (resolution.x / 2) * ratio, (y - resolution.y / 2) / (resolution.y / 2)


class HUD_Radar:

	spr_radar = None
	spr_radar_light = None
	spr_radar_box = None
	aircrafts_plots = None
	missiles_plots = None
	ships_plots = None
	missile_launchers_plots = None
	dir_plots = None
	spr_noise = None

	@classmethod
	def init(cls, resolution:hg.Vec2):
		cls.spr_radar = Sprite(530, 530, "sprites/radar.png")
		cls.spr_radar_light = Sprite(530, 530, "sprites/radar_light.png")
		cls.spr_radar_box = Sprite(530, 530, "sprites/radar_box.png")
		cls.aircrafts_plots = []
		cls.missiles_plots = []
		cls.ships_plots = []
		cls.missile_launchers_plots = []
		cls.dir_plot = Sprite(32, 32, "sprites/plot_dir.png")
		cls.spr_noise = Sprite(256, 256, "sprites/noise.png")
		rs = (200 / 1600 * resolution.x) / cls.spr_radar.width
		cls.spr_radar.set_size(rs)
		cls.spr_radar_light.set_size(rs)
		cls.spr_radar_box.set_size(rs)
		cls.spr_noise.set_size((200 / 1600 * resolution.x) / cls.spr_noise.width)

	@classmethod
	def setup_plots(cls, resolution, num_aircrafts, num_missiles, num_ships, num_missile_launchers):
		cls.aircrafts_plots = []
		cls.missiles_plots = []
		cls.ships_plots = []
		cls.missile_launchers_plots = []
		for i in range(num_aircrafts):
			cls.aircrafts_plots.append(Sprite(40, 40, "sprites/plot.png"))
		for i in range(num_missiles):
			cls.missiles_plots.append(Sprite(40, 40, "sprites/plot_missile.png"))
		for i in range(num_ships):
			cls.ships_plots.append(Sprite(40, 40, "sprites/plot_ship.png"))
		for i in range(num_missile_launchers):
			cls.missile_launchers_plots.append(Sprite(40, 40, "sprites/plot_missile_launcher.png"))

	@classmethod
	def update(cls, Main, machine:Destroyable_Machine, targets):
		t = hg.time_to_sec_f(hg.GetClock())
		rx, ry = 150 / 1600 * Main.resolution.x, 150 / 900 * Main.resolution.y
		rm = 6 / 1600
		rs = cls.spr_radar.size

		radar_scale = 4000
		plot_size = 12 / 1600 * Main.resolution.x

		cls.spr_radar.set_position(rx, ry)
		cls.spr_radar.set_color(hg.Color(1, 1, 1, 1))
		Main.sprites_display_list.append(cls.spr_radar)

		mat, pos, rot, aX, aY, aZ = machine.decompose_matrix()
		aZ.y = 0
		aZ = hg.Normalize(aZ)
		if aY.y < 0:
			aY = hg.Vec3(0, -1, 0)
		else:
			aY = hg.Vec3(0, 1, 0)
		aX = hg.Cross(aY, aZ)
		matrot = hg.Mat3()
		hg.SetAxises(matrot, aX, aY, aZ)
		mat_trans = hg.InverseFast(hg.TransformationMat4(hg.GetT(mat), matrot))

		i_missile = 0
		i_ship = 0
		i_aircraft = 0
		i_missile_launcher = 0
		td = machine.get_device("TargettingDevice")

		for target in targets:
			if not target.wreck and target.activated:
				t_mat, t_pos, t_rot, aX, aY, aZ = target.decompose_matrix()
				aZ.y = 0
				aZ = hg.Normalize(aZ)
				aY = hg.Vec3(0, 1, 0)
				aX = hg.Cross(aY, aZ)
				matrot = hg.Mat3()
				hg.SetAxises(matrot, aX, aY, aZ)
				t_mat_trans = mat_trans * hg.TransformationMat4(t_pos, matrot)
				pos = hg.GetT(t_mat_trans)
				v2D = hg.Vec2(pos.x, pos.z) / radar_scale * rs / 2
				if abs(v2D.x) < rs / 2 - rm and abs(v2D.y) < rs / 2 - rm:

					if target.type == Destroyable_Machine.TYPE_MISSILE:
						plot = cls.missiles_plots[i_missile]
						i_missile += 1
					elif target.type == Destroyable_Machine.TYPE_AIRCRAFT:
						plot = cls.aircrafts_plots[i_aircraft]
						i_aircraft += 1
					elif target.type == Destroyable_Machine.TYPE_SHIP:
						plot = cls.ships_plots[i_ship]
						i_ship += 1
					elif target.type == Destroyable_Machine.TYPE_MISSILE_LAUNCHER:
						plot = cls.missile_launchers_plots[i_missile_launcher]
						i_missile_launcher += 1
					t_mat_rot = hg.GetRotationMatrix(t_mat_trans)
					a = 0.5 + 0.5 * abs(sin(t * uniform(1, 500)))
				else:
					if target.type == Destroyable_Machine.TYPE_MISSILE: continue
					dir = hg.Normalize(v2D)
					v2D = dir * (rs / 2 - rm)
					plot = cls.dir_plot
					aZ = hg.Vec3(dir.x, 0, dir.y)
					aX = hg.Cross(hg.Vec3.Up, aZ)
					t_mat_rot = hg.Mat3(aX, hg.Vec3.Up, aZ)
					a = 0.5 + 0.5 * abs(sin(t * uniform(1, 500)))

				v2D *= Main.resolution.y / 2
				cx, cy = rx + v2D.x, ry + v2D.y

				if td is not None and target == td.get_target():
					c = hg.Color(0.85, 1., 0.25, a)
				elif target.nationality == machine.nationality:
					c = hg.Color(0.25, 1., 0.25, a)
				else:
					c = hg.Color(1., 0.5, 0.5, a)

				rot = hg.ToEuler(t_mat_rot)
				plot.set_position(cx, cy)
				plot.rotation.z = -rot.y
				plot.set_size(plot_size / plot.width)
				plot.set_color(c)
				Main.sprites_display_list.append(plot)

		cls.spr_noise.set_position(rx, ry)
		cls.spr_noise.set_color(hg.Color(1, 1, 1, max(pow(1 - machine.health_level, 2), 0.05)))
		cls.spr_noise.set_uv_scale(hg.Vec2((0.75 + 0.25 * sin(t * 538)) - (0.25 + 0.25 * sin(t * 103)), (0.75 + 0.25 * cos(t * 120)) - ((0.65 + 0.35 * sin(t * 83)))))
		Main.sprites_display_list.append(cls.spr_noise)

		cls.spr_radar_light.set_position(rx, ry)
		cls.spr_radar_light.set_color(hg.Color(1, 1, 1, 0.3))
		Main.sprites_display_list.append(cls.spr_radar_light)

		cls.spr_radar_box.set_position(rx, ry)
		cls.spr_radar_box.set_color(hg.Color(1, 1, 1, 1))
		Main.sprites_display_list.append(cls.spr_radar_box)


class HUD_MachineGun:
	spr_machine_gun_sight = None

	@classmethod
	def init(cls, resolution:hg.Vec2):
		cls.spr_machine_gun_sight = Sprite(64, 64, "sprites/machine_gun_sight.png")
		cls.spr_machine_gun_sight.set_color(hg.Color(0.5, 1, 0.5, 1))

	@classmethod
	def update(cls, main, machine):
		mat, pos, rot, aX, aY, aZ = machine.decompose_matrix()
		aZ = hg.GetZ(mat)
		aZ = hg.Normalize(aZ)
		gp = hg.Vec3(0, 0, 0)
		for gs in machine.machine_gun_slots:
			gp = gp + hg.GetT(gs.GetTransform().GetWorld())
		gp = gp / len(machine.machine_gun_slots)
		p = gp + aZ * 500
		p2D = main.get_2d_hud(p)
		if p2D is not None:
			cls.spr_machine_gun_sight.set_position(p2D.x, p2D.y)
			main.sprites_display_list.append(cls.spr_machine_gun_sight)


class HUD_MissileTarget:
	spr_target_sight = None
	spr_missile_sight = None

	@classmethod
	def init(cls, resolution: hg.Vec2):
		cls.spr_target_sight = Sprite(64, 64, "sprites/target_sight.png")
		cls.spr_missile_sight = Sprite(64, 64, "sprites/missile_sight.png")

		cls.spr_target_sight.set_size((32 / 1600 * resolution.x) / cls.spr_target_sight.width)
		cls.spr_missile_sight.set_size((32 / 1600 * resolution.x) / cls.spr_missile_sight.width)

	@classmethod
	def display_selected_target(cls, main, selected_machine):
		mat, pos, rot, aX, aY, aZ = selected_machine.decompose_matrix()
		p2D = main.get_2d_hud(pos)
		if p2D is not None:
			msg = selected_machine.name
			x = (p2D.x / main.resolution.x - 12 / 1600)
			c = hg.Color(1, 1, 0.0, 1.0)
			cls.spr_target_sight.set_position(p2D.x, p2D.y)
			cls.spr_target_sight.set_color(c)
			main.sprites_display_list.append(cls.spr_target_sight)
			Overlays.add_text2D(msg, hg.Vec2(x, (p2D.y / main.resolution.y - 24 / 900)), 0.012, c, main.hud_font)

	@classmethod
	def update(cls, main, machine):
		tps = hg.time_to_sec_f(hg.GetClock())
		td = machine.get_device("TargettingDevice")
		if td is not None:
			target = td.get_target()
			f = 1  # Main.HSL_postProcess.GetL()
			if target is not None:
				target_pos = target.get_parent_node().GetTransform().GetPos()
				target_distance = hg.Len(target_pos - machine.get_parent_node().GetTransform().GetPos())
				p2D = main.get_2d_hud(target_pos)
				if p2D is not None:
					a_pulse = 0.5 if (sin(tps * 20) > 0) else 0.75
					if td.target_locked:
						c = hg.Color(1., 0.5, 0.5, a_pulse)
						msg = "LOCKED - " + str(int(target_distance))
						x = (p2D.x / main.resolution.x - 32 / 1600)
						a = a_pulse
					else:
						msg = str(int(target_distance))
						x = (p2D.x / main.resolution.x - 12 / 1600)
						c = hg.Color(0.5, 1, 0.5, 0.75)

					c.a *= f
					cls.spr_target_sight.set_position(p2D.x, p2D.y)
					cls.spr_target_sight.set_color(c)
					main.sprites_display_list.append(cls.spr_target_sight)

					if td.target_out_of_range:
						Overlays.add_text2D("OUT OF RANGE", hg.Vec2(p2D.x / main.resolution.x - 40 / 1600, p2D.y / main.resolution.y - 24 / 900), 0.012, hg.Color(0.2, 1, 0.2, a_pulse * f), main.hud_font)
					else:
						Overlays.add_text2D(msg, hg.Vec2(x, (p2D.y / main.resolution.y - 24 / 900)), 0.012, c, main.hud_font)

					if td.target_locking_state > 0:
						t = sin(td.target_locking_state * pi - pi / 2) * 0.5 + 0.5
						p2D = hg.Vec2(0.5, 0.5) * (1 - t) + p2D * t
						cls.spr_missile_sight.set_position(p2D.x, p2D.y)
						cls.spr_missile_sight.set_color(c)
						main.sprites_display_list.append(cls.spr_missile_sight)

				c = hg.Color(0, 1, 0, f)

				Overlays.add_text2D("Target dist: %d" % (target_distance), hg.Vec2(0.05, 0.91), 0.016, c, main.hud_font)
				Overlays.add_text2D("Target heading: %d" % (target.get_heading()),hg.Vec2(0.05, 0.89), 0.016, c, main.hud_font)
				Overlays.add_text2D("Target alt: %d" % (target.get_altitude()), hg.Vec2(0.05, 0.87), 0.016, c, main.hud_font)


class HUD_Aircraft:

	@classmethod
	def update(cls, Main, aircraft: Aircraft, targets):
		f = 1  # Main.HSL_postProcess.GetL()
		tps = hg.time_to_sec_f(hg.GetClock())
		a_pulse = 0.1 if (sin(tps * 25) > 0) else 0.9
		hs, vs = aircraft.get_world_speed()
		if Main.flag_network_mode:
			if Main.flag_client_connected:
				Overlays.add_text2D("Client connected", hg.Vec2(0.05, 0.98), 0.016, HUD.color_connected * f, Main.hud_font)
			else:
				h, p = Main.get_network()
				Overlays.add_text2D("Host: " + h + " Port: " + str(p), hg.Vec2(0.05, 0.98), 0.016, HUD.color_wait_connect * f, Main.hud_font)

		if aircraft.flag_custom_physics_mode:
			Overlays.add_text2D("Custom physics", hg.Vec2(0.05, 0.92), 0.016, hg.Color.White * f, Main.hud_font)

		Overlays.add_text2D("Health: %d" % (aircraft.health_level * 100), hg.Vec2(0.05, 0.96), 0.016, (hg.Color.White * aircraft.health_level + hg.Color.Red * (1 - aircraft.health_level)) * f, Main.hud_font)

		# Compute num bullets

		Overlays.add_text2D("Bullets: %d" % (aircraft.get_num_bullets()), hg.Vec2(0.05, 0.94), 0.016, hg.Color.White * f, Main.hud_font)
		Overlays.add_text2D("Heading: %d" % (aircraft.get_heading()), hg.Vec2(0.49, 0.96), 0.016, hg.Color.White * f, Main.hud_font)

		iactrl = aircraft.get_device("IAControlDevice")
		if iactrl.is_activated():
			c = hg.Color.Orange
		else:
			c = HUD.color_inactive
		Overlays.add_text2D("IA Activated", hg.Vec2(0.45, 0.94), 0.015, c * f, Main.hud_font)

		# Gear HUD
		gear = aircraft.get_device("Gear")
		if gear is not None:
			color_gear = hg.Color(0.8, 1, 0.2, 1)
			gst = "DEPLOYED"
			if gear.flag_gear_moving:
				c = color_gear * a_pulse + HUD.color_inactive * (1 - a_pulse)
			elif gear.activated:
				c = color_gear
			else:
				gst = "RETRACTED"
				c = HUD.color_inactive
			Overlays.add_text2D("GEAR " + gst, hg.Vec2(0.52, 0.94), 0.015, c * f, Main.hud_font)
		else:
			Overlays.add_text2D("No gear installed", hg.Vec2(0.52, 0.94), 0.015, HUD.color_inactive * f, Main.hud_font)

		flag_internal_physics = not aircraft.get_custom_physics_mode()

		if flag_internal_physics and aircraft.playfield_distance > Destroyable_Machine.playfield_safe_distance:
			Overlays.add_text2D("Position Out of battle field !", hg.Vec2(0.43, 0.52), 0.018, hg.Color.Red * f, Main.hud_font)
			Overlays.add_text2D("Turn back now or you'll be destroyed !", hg.Vec2(0.405, 0.48), 0.018, hg.Color.Red * a_pulse * f, Main.hud_font)


		alt = aircraft.get_altitude()
		terrain_alt = aircraft.terrain_altitude
		if alt > aircraft.max_safe_altitude and flag_internal_physics :
			c = hg.Color.Red * a_pulse + hg.Color.Yellow * (1-a_pulse)
			Overlays.add_text2D("AIR DENSITY LOW - Damaging thrust", hg.Vec2(0.8, 0.95), 0.016, hg.Color.Red * f, Main.hud_font)
		else:
			c = hg.Color.White
		Overlays.add_text2D("Altitude (m): %d" % (alt),  hg.Vec2(0.8, 0.93), 0.016, c * f, Main.hud_font)
		Overlays.add_text2D("Ground (m): %d" % (terrain_alt),  hg.Vec2(0.8, 0.91), 0.016, c * f, Main.hud_font)

		Overlays.add_text2D("Vertical speed (m/s): %d" % (vs), hg.Vec2(0.8, 0.89), 0.016, hg.Color.White * f, Main.hud_font)
		Overlays.add_text2D("horizontal speed (m/s): %d" % (hs), hg.Vec2(0.8, 0.04), 0.016, hg.Color.White * f, Main.hud_font)
		Overlays.add_text2D("Pitch attitude: %d" % (aircraft.get_pitch_attitude()), hg.Vec2(0.8, 0.14), 0.016, hg.Color.White * f, Main.hud_font)
		Overlays.add_text2D("Roll attitude: %d" % (aircraft.get_roll_attitude()), hg.Vec2(0.8, 0.12), 0.016, hg.Color.White * f, Main.hud_font)

		ls = aircraft.get_linear_speed() * 3.6

		Overlays.add_text2D("Linear speed (km/h): %d" % (ls), hg.Vec2(0.8, 0.06), 0.016, hg.Color.White * f, Main.hud_font)

		if ls < aircraft.minimum_flight_speed and not aircraft.flag_landed:
			Overlays.add_text2D("LOW SPEED", hg.Vec2(0.47, 0.13), 0.018, hg.Color(1., 0, 0, a_pulse) * f, Main.hud_font)
		if aircraft.flag_landed:
			Overlays.add_text2D("LANDED", hg.Vec2(0.48, 0.13), 0.018, hg.Color(0.2, 1, 0.2, a_pulse) * f, Main.hud_font)

		Overlays.add_text2D("Linear acceleration (m.s2): %.2f" % (aircraft.get_linear_acceleration()), hg.Vec2(0.8, 0.02), 0.016, hg.Color.White * f, Main.hud_font)
		Overlays.add_text2D("Thrust: %d %%" % (aircraft.get_thrust_level() * 100), hg.Vec2(0.47, 0.1), 0.016, hg.Color.White * f, Main.hud_font)

		if aircraft.brake_level > 0:
			Overlays.add_text2D("Brake: %d %%" % (aircraft.get_brake_level() * 100), hg.Vec2(0.43, 0.046), 0.016, hg.Color(1, 0.4, 0.4) * f, Main.hud_font)

		if aircraft.flaps_level > 0:
			Overlays.add_text2D("Flaps: %d %%" % (aircraft.get_flaps_level() * 100), hg.Vec2(0.515, 0.046), 0.016, hg.Color(1, 0.8, 0.4) * f, Main.hud_font)

		HUD_Radar.update(Main, aircraft, targets)
		HUD_MissileTarget.update(Main, aircraft)

		if not Main.satellite_view:
			HUD_MachineGun.update(Main, aircraft)


class HUD_MissileLauncher:

	@classmethod
	def update(cls, Main, aircraft:MissileLauncherS400, targets):
		f = 1  # Main.HSL_postProcess.GetL()
		tps = hg.time_to_sec_f(hg.GetClock())
		a_pulse = 0.1 if (sin(tps * 25) > 0) else 0.9
		if Main.flag_network_mode:
			if Main.flag_client_connected:
				Overlays.add_text2D("Client connected", hg.Vec2(0.05, 0.98), 0.016, HUD.color_connected * f, Main.hud_font)
			else:
				h, p = Main.get_network()
				Overlays.add_text2D("Host: " + h + " Port: " + str(p), hg.Vec2(0.05, 0.98), 0.016, HUD.color_wait_connect * f, Main.hud_font)

		if aircraft.flag_custom_physics_mode:
			Overlays.add_text2D("Custom physics", hg.Vec2(0.05, 0.92), 0.016, hg.Color.White * f, Main.hud_font)

		Overlays.add_text2D("Health: %d" % (aircraft.health_level * 100), hg.Vec2(0.05, 0.96), 0.016, (hg.Color.White * aircraft.health_level + hg.Color.Red * (1 - aircraft.health_level)) * f, Main.hud_font)

		Overlays.add_text2D("Heading: %d" % (aircraft.get_heading()), hg.Vec2(0.49, 0.96), 0.016, hg.Color.White * f, Main.hud_font)

		iactrl = aircraft.get_device("IAControlDevice")
		if iactrl is not None:
			if iactrl.is_activated():
				c = hg.Color.Orange
			else:
				c = HUD.color_inactive
			Overlays.add_text2D("IA Activated", hg.Vec2(0.45, 0.94), 0.015, c * f, Main.hud_font)

		flag_internal_physics = not aircraft.get_custom_physics_mode()

		if flag_internal_physics and aircraft.playfield_distance > Destroyable_Machine.playfield_safe_distance:
			Overlays.add_text2D("Position Out of battle field !", hg.Vec2(0.43, 0.52), 0.018, hg.Color.Red * f, Main.hud_font)
			Overlays.add_text2D("Turn back now or you'll be destroyed !", hg.Vec2(0.405, 0.48), 0.018, hg.Color.Red * a_pulse * f, Main.hud_font)

		alt = aircraft.get_altitude()
		terrain_alt = aircraft.terrain_altitude
		c = hg.Color.White
		Overlays.add_text2D("Altitude (m): %d" % (alt),  hg.Vec2(0.8, 0.93), 0.016, c * f, Main.hud_font)
		Overlays.add_text2D("Ground (m): %d" % (terrain_alt),  hg.Vec2(0.8, 0.91), 0.016, c * f, Main.hud_font)

		Overlays.add_text2D("Pitch attitude: %d" % (aircraft.get_pitch_attitude()), hg.Vec2(0.8, 0.14), 0.016, hg.Color.White * f, Main.hud_font)
		Overlays.add_text2D("Roll attitude: %d" % (aircraft.get_roll_attitude()), hg.Vec2(0.8, 0.12), 0.016, hg.Color.White * f, Main.hud_font)

		ls = aircraft.get_linear_speed() * 3.6

		Overlays.add_text2D("Linear speed (km/h): %d" % (ls), hg.Vec2(0.8, 0.06), 0.016, hg.Color.White * f, Main.hud_font)

		Overlays.add_text2D("Linear acceleration (m.s2): %.2f" % (aircraft.get_linear_acceleration()), hg.Vec2(0.8, 0.02), 0.016, hg.Color.White * f, Main.hud_font)
		Overlays.add_text2D("Thrust: %d %%" % (aircraft.get_thrust_level() * 100), hg.Vec2(0.47, 0.1), 0.016, hg.Color.White * f, Main.hud_font)

		if aircraft.brake_level > 0:
			Overlays.add_text2D("Brake: %d %%" % (aircraft.get_brake_level() * 100), hg.Vec2(0.43, 0.046), 0.016, hg.Color(1, 0.4, 0.4) * f, Main.hud_font)

		HUD_Radar.update(Main, aircraft, targets)
		HUD_MissileTarget.update(Main, aircraft)
