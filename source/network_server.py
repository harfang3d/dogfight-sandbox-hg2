# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
import threading
import socket
import json
import socket_lib
from Machines import *
from overlays import *
import math
import Physics

main = None
dogfight_network_port = 50888
flag_server_running = False
flag_server_connected = False
server_log = ""
listen_socket_thread = None
flag_print_log = True

commands_functions = []


def get_network():
	return socket_lib.HOST, dogfight_network_port


def init_server(main_):
	global server_log, commands_functions, main
	main = main_

	commands_functions = {

		# Globals
		"DISABLE_LOG": disable_log,
		"ENABLE_LOG": enable_log,
		"GET_RUNNING": get_running,
		"SET_RENDERLESS_MODE": set_renderless_mode,
		"SET_DISPLAY_RADAR_IN_RENDERLESS_MODE": set_display_radar_in_renderless_mode,
		"SET_TIMESTEP": set_timestep,
		"GET_TIMESTEP": get_timestep,
		"SET_CLIENT_UPDATE_MODE": set_client_update_mode,
		"UPDATE_SCENE": update_scene,
		"DISPLAY_VECTOR": display_vector,
		"DISPLAY_2DTEXT": display_2DText,

		# Machines
		"GET_MACHINE_MISSILES_LIST": get_machine_missiles_list,
		"GET_TARGETS_LIST": get_targets_list,
		"GET_HEALTH": get_health,
		"SET_HEALTH": set_health,
		"ACTIVATE_AUTOPILOT": activate_autopilot,
		"DEACTIVATE_AUTOPILOT": deactivate_autopilot,
		"ACTIVATE_IA": activate_IA,
		"DEACTIVATE_IA": deactivate_IA,
		"GET_MACHINE_GUN_STATE": get_machine_gun_state,
		"ACTIVATE_MACHINE_GUN": activate_machine_gun,
		"DEACTIVATE_MACHINE_GUN": deactivate_machine_gun,
		"GET_MISSILESDEVICE_SLOTS_STATE": get_missiles_device_slots_state,
		"FIRE_MISSILE": fire_missile,
		"REARM_MACHINE": rearm_machine,
		"GET_TARGET_IDX": get_target_idx,
		"SET_TARGET_ID": set_target_id,
		"RESET_MACHINE_MATRIX": reset_machine_matrix,
		"RESET_MACHINE": reset_machine,
		"SET_MACHINE_CUSTOM_PHYSICS_MODE": set_machine_custom_physics_mode,
		"GET_MACHINE_CUSTOM_PHYSICS_MODE": get_machine_custom_physics_mode,
		"UPDATE_MACHINE_KINETICS": update_machine_kinetics,
		"GET_MOBILE_PARTS_LIST": get_mobile_parts_list,
		"IS_AUTOPILOT_ACTIVATED": is_autopilot_activated,
		"ACTIVATE_AUTOPILOT": activate_autopilot,
		"DEACTIVATE_AUTOPILOT": deactivate_autopilot,
		"IS_IA_ACTIVATED": is_ia_activated,
		"ACTIVATE_IA": activate_IA,
		"DEACTIVATE_IA": deactivate_IA,
		"IS_USER_CONTROL_ACTIVATED": is_user_control_activated,
		"ACTIVATE_USER_CONTROL": activate_user_control,
		"DEACTIVATE_USER_CONTROL": deactivate_user_control,
		"COMPUTE_NEXT_TIMESTEP_PHYSICS": compute_next_timestep_physics,

		# Aircrafts
		"GET_PLANESLIST": get_planes_list,
		"GET_PLANE_STATE": get_plane_state,
		"SET_PLANE_THRUST": set_plane_thrust,
		"GET_PLANE_THRUST": get_plane_thrust,
		"ACTIVATE_PC": activate_pc,
		"DEACTIVATE_PC": deactivate_pc,
		"SET_PLANE_BRAKE": set_plane_brake,
		"SET_PLANE_FLAPS": set_plane_flaps,
		"SET_PLANE_PITCH": set_plane_pitch,
		"SET_PLANE_ROLL": set_plane_roll,
		"SET_PLANE_YAW": set_plane_yaw,
		"STABILIZE_PLANE": stabilize_plane,
		"DEPLOY_GEAR": deploy_gear,
		"RETRACT_GEAR": retract_gear,
		"SET_PLANE_AUTOPILOT_SPEED": set_plane_autopilot_speed,
		"SET_PLANE_AUTOPILOT_HEADING": set_plane_autopilot_heading,
		"SET_PLANE_AUTOPILOT_ALTITUDE": set_plane_autopilot_altitude,
		"ACTIVATE_PLANE_EASY_STEERING": activate_plane_easy_steering,
		"DEACTIVATE_PLANE_EASY_STEERING": deactivate_plane_easy_steering,
		"SET_PLANE_LINEAR_SPEED": set_plane_linear_speed,
		"RESET_GEAR": reset_gear,
		"RECORD_PLANE_START_STATE": record_plane_start_state,

		# Missiles
		"GET_MISSILESLIST": get_missiles_list,
		"GET_MISSILE_STATE": get_missile_state,
		"SET_MISSILE_LIFE_DELAY": set_missile_life_delay,
		"GET_MISSILE_TARGETS_LIST": get_missile_targets_list,
		"SET_MISSILE_TARGET": set_missile_target,
		"SET_MISSILE_THRUST_FORCE": set_missile_thrust_force,
		"SET_MISSILE_ANGULAR_FRICTIONS": set_missile_angular_frictions,
		"SET_MISSILE_DRAG_COEFFICIENTS": set_missile_drag_coefficients,

		# Missile launchers
		"GET_MISSILE_LAUNCHERS_LIST": get_missile_launchers_list,
		"GET_MISSILE_LAUNCHER_STATE": get_missile_launcher_state
	}
	server_log = ""
	msg = "Hostname: %s, IP: %s, port: %d" % (socket_lib.hostname, socket_lib.HOST, dogfight_network_port)
	server_log = msg
	print(msg)


def start_server():
	global flag_server_running, listen_socket_thread
	main.flag_client_connected = False
	flag_server_running = True
	listen_socket_tread = threading.Thread(target=server_update)
	listen_socket_tread.start()


def stop_server():
	global flag_server_running, flag_server_connected, server_log
	flag_server_running = False
	flag_server_connected = False
	main.flag_client_connected = False
	msg = "Exit from server"
	server_log += msg
	print(msg)


def server_update():
	global flag_server_running, server_log, flag_server_connected

	while flag_server_running:
		try:
			socket_lib.listener_socket(dogfight_network_port)
			print(socket_lib.logger)
			server_log += socket_lib.logger
			flag_server_connected = True
			main.flag_client_connected = True
			while flag_server_connected:
				answ = socket_lib.get_answer()
				answ.decode()
				command = json.loads(answ)
				if command == "":
					server_log += "Disconnected"
					flag_server_connected = False
					main.flag_client_connected = False
				else:
					msg = "command:" + command["command"]
					if flag_print_log:
						print(msg)
						server_log += msg
					commands_functions[command["command"]](command["args"])

		except:
			print("network_server.py - server_update ERROR")
			flag_server_connected = False
			main.flag_client_connected = False
			main.flag_client_update_mode = False
			main.set_renderless_mode(False)
			msg = "Socket closed"
			server_log += msg
			print(msg)


# Globals

def disable_log(args):
	global flag_print_log
	flag_print_log = False


def enable_log(args):
	global flag_print_log
	flag_print_log = True


def update_scene(args):
	if main.flag_client_update_mode:
		if main.flag_renderless:
			main.update() # No display, but fast simulation
		else:
			main.flag_client_ask_update_scene = True # display simulation at 60 fps
	elif flag_print_log:
		print("Update_scene ERROR - Client update mode is FALSE")


def display_vector(args):
	if main.flag_client_update_mode:
		position = hg.Vec3(args["position"][0], args["position"][1], args["position"][2])
		direction = hg.Vec3(args["direction"][0], args["direction"][1], args["direction"][2])
		label_offset2D = hg.Vec2(args["label_offset2D"][0], args["label_offset2D"][1])
		color = hg.Color(args["color"][0],args["color"][1], args["color"][2], args["color"][3])
		Overlays.display_named_vector(position, direction, args["label"], label_offset2D, color, args["label_size"])
	elif flag_print_log:
		print("Display vector ERROR - Client Update Mode must be TRUE")


def display_2DText(args):
	if main.flag_client_update_mode:
		position = hg.Vec2(args["position"][0], args["position"][1])
		color = hg.Color(args["color"][0],args["color"][1], args["color"][2], args["color"][3])
		Overlays.add_text2D(args["text"], position, args["size"], color)
	elif flag_print_log:
		print("Display 2d Text ERROR - Client Update Mode must be TRUE")


def set_timestep(args):
	main.timestep = args["timestep"]


def get_timestep(args):
	ts = {"timestep": main.timestep}
	socket_lib.send_message(str.encode(json.dumps(ts)))


def get_running(args):
	state = {"running": main.flag_running}
	socket_lib.send_message(str.encode(json.dumps(state)))


def set_renderless_mode(args):
	main.set_renderless_mode(args["flag"])


def set_display_radar_in_renderless_mode(args):
	main.flag_display_radar_in_renderless = args["flag"]


def set_client_update_mode(args):
	main.flag_client_update_mode = args["flag"]


# Machines


def set_machine_custom_physics_mode(args):
	if flag_print_log:
		print(args["machine_id"])
	machine = main.destroyables_items[args["machine_id"]]
	machine.set_custom_physics_mode(args["flag"])


def get_machine_custom_physics_mode(args):
	machine = main.destroyables_items[args["machine_id"]]
	state = {
		"timestamp": main.framecount,
		"timestep": main.timestep,
		"custom_physics_mode": machine.flag_custom_physics_mode
	}
	if flag_print_log:
		print(args["machine_id"])
		print(str(state))
	socket_lib.send_message(str.encode(json.dumps(state)))


def update_machine_kinetics(args):
	if flag_print_log:
		print(args["machine_id"])
	machine = main.destroyables_items[args["machine_id"]]
	print("c0")
	mat = hg.TranslationMat4(hg.Vec3(0, 0, 0))
	for n in args["matrix"]:
		if math.isnan(n):
			args["matrix"] = [1, 0, 0,
							0, 1, 0,
							0, 0, 1,
							0, 200, 0]
			break
	for n in args["v_move"]:
		if math.isnan(n):
			args["v_move"] = [0, 0, 0]
			break
	hg.SetRow(mat, 0, hg.Vec4(args["matrix"][0], args["matrix"][3], args["matrix"][6], args["matrix"][9]))
	hg.SetRow(mat, 1, hg.Vec4(args["matrix"][1], args["matrix"][4], args["matrix"][7], args["matrix"][10]))
	hg.SetRow(mat, 2, hg.Vec4(args["matrix"][2], args["matrix"][5], args["matrix"][8], args["matrix"][11]))
	machine.set_custom_kinetics(mat, hg.Vec3(args["v_move"][0], args["v_move"][1], args["v_move"][2]))


def reset_machine(args):
	machine = main.destroyables_items[args["machine_id"]]
	machine.reset()


def reset_machine_matrix(args):
	machine = main.destroyables_items[args["machine_id"]]
	pos = hg.Vec3(args["position"][0], args["position"][1], args["position"][2])
	rot = hg.Vec3(args["rotation"][0], args["rotation"][1], args["rotation"][2])
	machine.reset_matrix(pos, rot)
	if machine.type == Destroyable_Machine.TYPE_AIRCRAFT:
		machine.flag_landed = False


def get_machine_missiles_list(args):
	machine = main.destroyables_items[args["machine_id"]]
	missiles = []
	md = machine.get_device("MissilesDevice")
	if md is not None:
		for missile in md.missiles:
			if missile is None:
				missiles.append("")
			else:
				missiles.append(missile.name)
	else:
		print("ERROR - Machine '" + args["machine_id"] + "' has no MissilesDevice !")
	socket_lib.send_message(str.encode(json.dumps(missiles)))


def get_targets_list(args):
	machine = main.destroyables_items[args["machine_id"]]
	td = machine.get_device("TargettingDevice")
	if td is not None:
		tlist = [{"target_id": "-None-"}]  # Target id 0 = no target
		targets = td.get_targets()
		for target in targets:
			tlist.append({"target_id": target.name, "wreck": target.wreck, "active": target.activated})
		if flag_print_log:
			print(args["machine_id"])
			print(str(tlist))
	else:
		tlist = []
		print("ERROR - Machine '" + args["machine_id"] + "' has no TargettingDevice !")
	socket_lib.send_message(str.encode(json.dumps(tlist)))


def get_mobile_parts_list(args):
	machine = main.destroyables_items[args["machine_id"]]
	parts = machine.get_mobile_parts()
	parts_id = []
	for part_id in parts:
		parts_id.append(part_id)
	socket_lib.send_message(str.encode(json.dumps(parts_id)))


def get_machine_gun_state(args):
	machine = main.destroyables_items[args["machine_id"]]
	state = {
		"timestamp": main.framecount,
		"timestep": main.timestep,
		"MachineGunDevices": {}
	}
	n = machine.get_machinegun_count()
	if n > 0:
		for i in range(n):
			gm_name = "MachineGunDevice_%02d" % i
			gmd = machine.get_device(gm_name)
			if gmd is not None:
				gm_state = {
					"machine_gun_activated": gmd.is_gun_activated(),
					"bullets_count": gmd.get_num_bullets()
				}
				state["MachineGunDevices"][gm_name] = gm_state
		if flag_print_log:
			print(args["machine_id"])
			print(str(state))
		socket_lib.send_message(str.encode(json.dumps(state)))
	else:
		print("ERROR - Machine '" + args["machine_id"] + "' has no MachineGunDevice !")


def get_missiles_device_slots_state(args):
	machine = main.destroyables_items[args["machine_id"]]
	md = machine.get_device("MissilesDevice")
	if md is not None:
		state = {
			"timestamp": main.framecount,
			"timestep": main.timestep,
			"missiles_slots": md.get_missiles_state()
		}
		if flag_print_log:
			print(args["machine_id"])
			print(str(state))
		socket_lib.send_message(str.encode(json.dumps(state)))
	else:
		print("ERROR - Machine '" + args["machine_id"] + "' has no MissilesDevice !")


def fire_missile(args):
	if flag_print_log:
		print(args["machine_id"] + " " + str(args["slot_id"]))
	machine = main.destroyables_items[args["machine_id"]]
	md = machine.get_device("MissilesDevice")
	if md is not None:
		md.fire_missile(int(args["slot_id"]))
	else:
		print("ERROR - Machine '" + args["machine_id"] + "' has no MissilesDevice !")


def rearm_machine(args):
	if flag_print_log:
		print(args["machine_id"])
	machine = main.destroyables_items[args["machine_id"]]
	machine.rearm()


def activate_machine_gun(args):
	if flag_print_log:
		print(args["machine_id"])
	machine = main.destroyables_items[args["machine_id"]]
	n = machine.get_machinegun_count()
	for i in range(n):
		mgd = machine.get_device("MachineGunDevice_%02d" % i)
		if mgd is not None and not mgd.is_gun_activated():
			mgd.fire_machine_gun()


def deactivate_machine_gun(args):
	if flag_print_log:
		print(args["machine_id"])
	machine = main.destroyables_items[args["machine_id"]]
	n = machine.get_machinegun_count()
	for i in range(n):
		mgd = machine.get_device("MachineGunDevice_%02d" % i)
		if mgd is not None and mgd.is_gun_activated():
			mgd.stop_machine_gun()


def get_health(args):
	machine = main.destroyables_items[args["machine_id"]]
	state = {
		"timestamp": main.framecount,
		"timestep": main.timestep,
		"health_level": machine.get_health_level()
	}
	if flag_print_log:
		print(args["machine_id"])
		print(str(state))
	socket_lib.send_message(str.encode(json.dumps(state)))


def set_health(args):
	if flag_print_log:
		print(args["machine_id"] + " " + str(args["health_level"]))
	machine = main.destroyables_items[args["machine_id"]]
	machine.set_health_level(args["health_level"])


def get_target_idx(args):
	machine = main.destroyables_items[args["machine_id"]]
	td = machine.get_device("TargettingDevice")
	if td is not None:
		state = {
			"timestamp": main.framecount,
			"timestep": main.timestep,
			"target_idx": td.get_target_id()
		}
		if flag_print_log:
			print(args["machine_id"])
			print(str(state))
	else:
		state = {
			"timestamp": main.framecount,
			"timestep": main.timestep,
			"target_idx": 0
		}
		print("ERROR - Machine '" + args["machine_id"] + "' has no TargettingDevice !")

	socket_lib.send_message(str.encode(json.dumps(state)))


def set_target_id(args):
	if flag_print_log:
		print(args["machine_id"] + " " + str(args["target_id"]))
	machine = main.destroyables_items[args["machine_id"]]
	td = machine.get_device("TargettingDevice")
	if td is not None:
		td.set_target_by_name(args["target_id"])
	else:
		print("ERROR - Machine '" + args["machine_id"] + "' has no TargettingDevice !")


def activate_autopilot(args):
	if flag_print_log:
		print(args["machine_id"])
	machine = main.destroyables_items[args["machine_id"]]
	apctrl = machine.get_device("AutopilotControlDevice")
	if apctrl is not None:
		apctrl.activate()


def deactivate_autopilot(args):
	if flag_print_log:
		print(args["machine_id"])
	machine = main.destroyables_items[args["machine_id"]]
	apctrl = machine.get_device("AutopilotControlDevice")
	if apctrl is not None:
		apctrl.deactivate()


def activate_IA(args):
	if flag_print_log:
		print(args["machine_id"])
	machine = main.destroyables_items[args["machine_id"]]
	iactrl = machine.get_device("IAControlDevice")
	if iactrl is not None:
		iactrl.activate()


def deactivate_IA(args):
	if flag_print_log:
		print(args["machine_id"])
	machine = main.destroyables_items[args["machine_id"]]
	iactrl = machine.get_device("IAControlDevice")
	if iactrl is not None:
		iactrl.deactivate()


def is_autopilot_activated(args):
	machine = main.destroyables_items[args["machine_id"]]
	apctrl = machine.get_device("AutopilotControlDevice")
	if apctrl is not None:
		state = {
			"timestamp": main.framecount,
			"timestep": main.timestep,
			"autopilot": apctrl.is_activated()
		}
		if flag_print_log:
			print(args["machine_id"])
			print(str(state))
	else:
		state = {
			"timestamp": main.framecount,
			"timestep": main.timestep,
			"autopilot": False
		}
	socket_lib.send_message(str.encode(json.dumps(state)))


def is_ia_activated(args):
	machine = main.destroyables_items[args["machine_id"]]
	iactrl = machine.get_device("IAControlDevice")
	if iactrl is not None:
		state = {
			"timestamp": main.framecount,
			"timestep": main.timestep,
			"ia": iactrl.is_activated()
		}
		if flag_print_log:
			print(args["machine_id"])
			print(str(state))
	else:
		state = {
			"timestamp": main.framecount,
			"timestep": main.timestep,
			"ia": False
		}
	socket_lib.send_message(str.encode(json.dumps(state)))


def is_user_control_activated(args):
	machine = main.destroyables_items[args["machine_id"]]
	uctrl = machine.get_device("UserControlDevice")
	if uctrl is not None:
		state = {
			"timestamp": main.framecount,
			"timestep": main.timestep,
			"user": uctrl.is_activated()
		}
		if flag_print_log:
			print(args["machine_id"])
			print(str(state))
	else:
		state = {
			"timestamp": main.framecount,
			"timestep": main.timestep,
			"user": False
		}
	socket_lib.send_message(str.encode(json.dumps(state)))


def activate_user_control(args):
	if flag_print_log:
		print(args["machine_id"])
	machine = main.destroyables_items[args["machine_id"]]
	uctrl = machine.get_device("UserControlDevice")
	if uctrl is not None:
		uctrl.activate()


def deactivate_user_control(args):
	if flag_print_log:
		print(args["machine_id"])
	machine = main.destroyables_items[args["machine_id"]]
	uctrl = machine.get_device("UserControlDevice")
	if uctrl is not None:
		uctrl.deactivate()


def compute_next_timestep_physics(args):
	machine = main.destroyables_items[args["machine_id"]]
	physics_parameters = machine.get_physics_parameters()
	mat, physics_parameters = Physics.update_physics(machine.parent_node.GetTransform().GetWorld(), machine, physics_parameters, args["timestep"])
	v = physics_parameters["v_move"]
	physics_parameters["v_move"] = [v.x, v.y, v.z]
	mat_r0 = hg.GetRow(mat, 0)
	mat_r1 = hg.GetRow(mat, 1)
	mat_r2 = hg.GetRow(mat, 2)
	physics_parameters["matrix"] = [mat_r0.x, mat_r1.x, mat_r2.x,
									mat_r0.y, mat_r1.y, mat_r2.y, 
									mat_r0.z, mat_r1.z, mat_r2.z, 
									mat_r0.w, mat_r1.w, mat_r2.w]
	
	if flag_print_log:
		print(args["machine_id"])
		print(str(physics_parameters))
	socket_lib.send_message(str.encode(json.dumps(physics_parameters)))

# Aircraft


def get_plane_state(args):
	machine = main.destroyables_items[args["plane_id"]]
	h_spd, v_spd = machine.get_world_speed()

	gear = machine.get_device("Gear")
	apctrl = machine.get_device("AutopilotControlDevice")
	iactrl = machine.get_device("IAControlDevice")
	td = machine.get_device("TargettingDevice")

	if gear is not None:
		gear_activated = gear.activated
	else:
		gear_activated = False

	if apctrl is not None:
		autopilot_activated = apctrl.is_activated()
		autopilot_heading = apctrl.autopilot_heading
		autopilot_speed = apctrl.autopilot_speed
		autopilot_altitude = apctrl.autopilot_altitude
	else:
		autopilot_activated = False
		autopilot_heading = 0
		autopilot_speed = 0
		autopilot_altitude = 0

	if iactrl is not None:
		ia_activated = iactrl.is_activated()
	else:
		ia_activated = False

	if td is not None:
		target_id = td.get_target_name()
		target_locked = td.target_locked
		target_out_of_range = td.target_out_of_range
		target_angle = td.target_angle
	else:
		target_id = "- ! No TargettingDevice ! -"
		target_locked = False

	position = machine.get_position()
	rotation = machine.get_Euler()
	v_move = machine.get_move_vector()
	state = {
		"timestamp": main.framecount,
		"timestep": main.timestep,
		"position": [position.x, position.y, position.z],
		"Euler_angles": [rotation.x, rotation.y, rotation.z],
		"easy_steering": machine.flag_easy_steering,
		"health_level": machine.health_level,
		"destroyed": machine.flag_destroyed,
		"wreck": machine.wreck,
		"crashed": machine.flag_crashed,
		"active": machine.activated,
		"type": Destroyable_Machine.types_labels[machine.type],
		"nationality": machine.nationality,
		"thrust_level": machine.get_thrust_level(),
		"brake_level": machine.get_brake_level(),
		"flaps_level": machine.get_flaps_level(),
		"horizontal_speed": h_spd,
		"vertical_speed": v_spd,
		"linear_speed": machine.get_linear_speed(),
		"move_vector": [v_move.x, v_move.y, v_move.z],
		"linear_acceleration": machine.get_linear_acceleration(),
		"altitude": machine.get_altitude(),
		"heading": machine.get_heading(),
		"pitch_attitude": machine.get_pitch_attitude(),
		"roll_attitude": machine.get_roll_attitude(),
		"post_combustion": machine.post_combustion,
		"user_pitch_level": machine.get_pilot_pitch_level(),
		"user_roll_level": machine.get_pilot_roll_level(),
		"user_yaw_level": machine.get_pilot_yaw_level(),
		"gear": gear_activated,
		"ia": ia_activated,
		"autopilot": autopilot_activated,
		"autopilot_heading": autopilot_heading,
		"autopilot_speed": autopilot_speed,
		"autopilot_altitude": autopilot_altitude,
		"target_id": target_id,
		"target_locked": target_locked,
		"target_out_of_range": target_out_of_range,
		"target_angle": target_angle
	}
	if flag_print_log:
		print(args["plane_id"])
		print(str(state))
	socket_lib.send_message(str.encode(json.dumps(state)))


def get_planes_list(args):
	planes = []
	print("Get planes list")
	for dm in main.destroyables_list:
		if dm.type == Destroyable_Machine.TYPE_AIRCRAFT:
			print(dm.name)
			planes.append(dm.name)
	socket_lib.send_message(str.encode(json.dumps(planes)))


def record_plane_start_state(args):
	machine = main.destroyables_items[args["plane_id"]]
	machine.record_start_state()


def set_plane_linear_speed(args):
	machine = main.destroyables_items[args["plane_id"]]
	machine.set_linear_speed(args["linear_speed"])


def reset_gear(args):
	machine = main.destroyables_items[args["plane_id"]]
	machine.flag_gear_deployed = args["gear_deployed"]
	gear = machine.get_device("Gear")
	if gear is not None:
		gear.reset()


def set_plane_thrust(args):
	if flag_print_log:
		print(args["plane_id"] + " " + str(args["thrust_level"]))
	machine = main.destroyables_items[args["plane_id"]]
	machine.set_thrust_level(args["thrust_level"])


def get_plane_thrust(args):
	machine = main.destroyables_items[args["plane_id"]]
	state = {
		"timestamp": main.framecount,
		"timestep": main.timestep,
		"thrust_level": machine.get_thrust_level()
	}
	if flag_print_log:
		print(args["plane_id"])
		print(str(state))
	socket_lib.send_message(str.encode(json.dumps(state)))


def activate_pc(args):
	if flag_print_log:
		print(args["plane_id"])
	machine = main.destroyables_items[args["plane_id"]]
	machine.activate_post_combustion()


def deactivate_pc(args):
	if flag_print_log:
		print(args["plane_id"])
	machine = main.destroyables_items[args["plane_id"]]
	machine.deactivate_post_combustion()


def set_plane_brake(args):
	if flag_print_log:
		print(args["plane_id"] + " " + str(args["brake_level"]))
		print(str(args["brake_level"]))
	machine = main.destroyables_items[args["plane_id"]]
	machine.set_brake_level(args["brake_level"])


def set_plane_flaps(args):
	if flag_print_log:
		print(args["plane_id"] + " " + str(args["flaps_level"]))
		print(str(args["flaps_level"]))
	machine = main.destroyables_items[args["plane_id"]]
	machine.set_flaps_level(args["flaps_level"])


def set_plane_pitch(args):
	if flag_print_log:
		print(args["plane_id"] + " " + str(args["pitch_level"]))
		print(str(args["pitch_level"]))
	machine = main.destroyables_items[args["plane_id"]]
	machine.set_pitch_level(args["pitch_level"])


def set_plane_roll(args):
	if flag_print_log:
		print(args["plane_id"] + " " + str(args["roll_level"]))
		print(str(args["roll_level"]))
	machine = main.destroyables_items[args["plane_id"]]
	machine.set_roll_level(args["roll_level"])


def set_plane_yaw(args):
	if flag_print_log:
		print(args["plane_id"] + " " + str(args["yaw_level"]))
		print(str(args["yaw_level"]))
	machine = main.destroyables_items[args["plane_id"]]
	machine.set_yaw_level(args["yaw_level"])


def stabilize_plane(args):
	if flag_print_log:
		print(args["plane_id"])
	machine = main.destroyables_items[args["plane_id"]]
	machine.stabilize(True, True, True)


def deploy_gear(args):
	if flag_print_log:
		print(args["plane_id"])
	machine = main.destroyables_items[args["plane_id"]]
	gear = machine.get_device("Gear")
	if gear is not None:
		gear.activate()


def retract_gear(args):
	if flag_print_log:
		print(args["plane_id"])
	machine = main.destroyables_items[args["plane_id"]]
	gear = machine.get_device("Gear")
	if gear is not None:
		gear.deactivate()


def set_plane_autopilot_speed(args):
	if flag_print_log:
		print(args["plane_id"] + " " + str(args["ap_speed"]))
	machine = main.destroyables_items[args["plane_id"]]
	apctrl = machine.get_device("AutopilotControlDevice")
	if apctrl is not None:
		apctrl.set_autopilot_speed(args["ap_speed"])


def set_plane_autopilot_heading(args):
	if flag_print_log:
		print(args["plane_id"] + " " + str(args["ap_heading"]))
		print(str(args["ap_heading"]))
	machine = main.destroyables_items[args["plane_id"]]
	apctrl = machine.get_device("AutopilotControlDevice")
	if apctrl is not None:
		apctrl.set_autopilot_heading(args["ap_heading"])


def set_plane_autopilot_altitude(args):
	if flag_print_log:
		print(args["plane_id"] + " " + str(args["ap_altitude"]))
		print(str(args["ap_altitude"]))
	machine = main.destroyables_items[args["plane_id"]]
	apctrl = machine.get_device("AutopilotControlDevice")
	if apctrl is not None:
		apctrl.set_autopilot_altitude(args["ap_altitude"])


def activate_plane_easy_steering(args):
	if flag_print_log:
		print(args["plane_id"])
	machine = main.destroyables_items[args["plane_id"]]
	machine.activate_easy_steering()


def deactivate_plane_easy_steering(args):
	if flag_print_log:
		print(args["plane_id"])
	machine = main.destroyables_items[args["plane_id"]]
	machine.deactivate_easy_steering()


# Missile launchers

def get_missile_launchers_list(args):
	missile_launchers = []
	print("Get missile launchers list")
	for dm in main.destroyables_list:
		print(dm.name)
		if dm.type == Destroyable_Machine.TYPE_MISSILE_LAUNCHER:
			missile_launchers.append(dm.name)
	socket_lib.send_message(str.encode(json.dumps(missile_launchers)))


def get_missile_launcher_state(args):
	machine = main.destroyables_items[args["machine_id"]]
	position = machine.get_position()
	rotation = machine.get_Euler()
	td = machine.get_device("TargettingDevice")
	if td is not None:
		target_id = td.get_target_name()
		target_locked = td.target_locked
	else:
		target_id = "- ! No TargettingDevice ! -"
		target_locked = False
	state = {
		"timestamp": main.framecount,
		"timestep": main.timestep,
		"position": [position.x, position.y, position.z],
		"Euler_angles": [rotation.x, rotation.y, rotation.z],
		"health_level": machine.health_level,
		"destroyed": machine.flag_destroyed,
		"wreck": machine.wreck,
		"active": machine.activated,
		"type": Destroyable_Machine.types_labels[machine.type],
		"nationality": machine.nationality,
		"altitude": machine.get_altitude(),
		"heading": machine.get_heading(),
		"target_id": target_id,
		"target_locked": target_locked
	}
	print("State OK")
	if flag_print_log:
		print(args["machine_id"])
		print(str(state))
	socket_lib.send_message(str.encode(json.dumps(state)))


# Missiles

def get_missiles_list(args):
	print("Get missiles list")
	missiles = []
	for dm in main.destroyables_list:
		if dm.type == Destroyable_Machine.TYPE_MISSILE:
			print(dm.name)
			missiles.append(dm.name)
	socket_lib.send_message(str.encode(json.dumps(missiles)))


def get_missile_state(args):
	machine = main.destroyables_items[args["missile_id"]]
	position = machine.get_position()
	rotation = machine.get_Euler()
	v_move = machine.get_move_vector()
	h_spd, v_spd = machine.get_world_speed()
	state = {
		"timestamp": main.framecount,
		"timestep": main.timestep,
		"type": Destroyable_Machine.types_labels[machine.type],
		"position": [position.x, position.y, position.z],
		"Euler_angles": [rotation.x, rotation.y, rotation.z],
		"move_vector": [v_move.x, v_move.y, v_move.z],
		"destroyed": machine.flag_destroyed,
		"wreck": machine.wreck,
		"crashed": machine.flag_crashed,
		"active": machine.activated,
		"nationality": machine.nationality,
		"altitude": machine.get_altitude(),
		"heading": machine.get_heading(),
		"pitch_attitude": machine.get_pitch_attitude(),
		"roll_attitude": machine.get_roll_attitude(),
		"horizontal_speed": h_spd,
		"vertical_speed": v_spd,
		"linear_speed": machine.get_linear_speed(),
		"target_id": machine.get_target_id(),
		"life_delay": machine.life_delay,
		"life_time": machine.life_cptr,
		"thrust_force": machine.f_thrust,
		"angular_frictions": [machine.angular_frictions.x, machine.angular_frictions.y, machine.angular_frictions.z],
		"drag_coefficients": [machine.drag_coeff.x, machine.drag_coeff.y, machine.drag_coeff.z]
		}
	if flag_print_log:
		print(args["missile_id"])
		print(str(state))
	socket_lib.send_message(str.encode(json.dumps(state)))


def set_missile_life_delay(args):
	missile = main.destroyables_items[args["missile_id"]]
	missile.set_life_delay(args["life_delay"])


def set_missile_target(args):
	missile = main.destroyables_items[args["missile_id"]]
	missile.set_target_by_name(args["target_id"])


def get_missile_targets_list(args):
	missile = main.destroyables_items[args["missile_id"]]
	targets = missile.get_valid_targets_list()
	targets_ids = ["-None-"]
	for t in targets:
		targets_ids.append(t.name)
	socket_lib.send_message(str.encode(json.dumps(targets_ids)))

def set_missile_thrust_force(args):
	missile = main.destroyables_items[args["missile_id"]]
	missile.set_thrust_force(args["thrust_force"])

def set_missile_angular_frictions(args):
	missile = main.destroyables_items[args["missile_id"]]
	missile.set_angular_friction(args["angular_frictions"][0], args["angular_frictions"][1], args["angular_frictions"][2] )

def set_missile_drag_coefficients(args):
	missile = main.destroyables_items[args["missile_id"]]
	missile.set_drag_coefficients(args["drag_coeff"][0], args["drag_coeff"][1], args["drag_coeff"][2] )
