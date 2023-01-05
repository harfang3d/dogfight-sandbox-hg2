import json
import socket_lib


def connect(_host, _port):
	socket_lib.connect_socket(_host, _port)


def disconnect():
	socket_lib.close_socket()


# Globals

def disable_log():
	socket_lib.send_message(str.encode(json.dumps({"command": "DISABLE_LOG", "args": {}})))


def enable_log():
	socket_lib.send_message(str.encode(json.dumps({"command": "ENABLE_LOG", "args": {}})))


def get_running():
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_RUNNING", "args": {}})))
	return json.loads((socket_lib.get_answer()).decode())


def set_timestep(t):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_TIMESTEP", "args": {"timestep": t}})))


def get_timestep():
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_TIMESTEP", "args": {}})))
	return json.loads((socket_lib.get_answer()).decode())


def set_renderless_mode(flag: bool):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_RENDERLESS_MODE", "args": {"flag": flag}})))


def set_client_update_mode(flag: bool):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_CLIENT_UPDATE_MODE", "args": {"flag": flag}})))


def set_display_radar_in_renderless_mode(flag: bool):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_DISPLAY_RADAR_IN_RENDERLESS_MODE", "args": {"flag": flag}})))


def update_scene():
	socket_lib.send_message(str.encode(json.dumps({"command": "UPDATE_SCENE", "args": {}})))


def display_vector(position, direction, label, label_offset2D, color, label_size):
	socket_lib.send_message(str.encode(json.dumps({"command": "DISPLAY_VECTOR", "args": {"position": position, "direction": direction, "label": label, "label_offset2D": label_offset2D, "color": color, "label_size": label_size}})))


def display_2DText(position, text, size, color):
	socket_lib.send_message(str.encode(json.dumps({"command": "DISPLAY_2DTEXT", "args": {"position": position, "text": text, "size": size, "color": color}})))


# Machines

def get_mobile_parts_list(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_MOBILE_PARTS_LIST", "args": {"machine_id": machine_id}})))
	return json.loads((socket_lib.get_answer()).decode())


def set_machine_custom_physics_mode(machine_id, flag: bool):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_MACHINE_CUSTOM_PHYSICS_MODE", "args": {"machine_id": machine_id, "flag": flag}})))


def get_machine_custom_physics_mode(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_MACHINE_CUSTOM_PHYSICS_MODE", "args": {"machine_id": machine_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


def update_machine_kinetics(machine_id, matrix_3_4: list, speed_vector: list):
	socket_lib.send_message(str.encode(json.dumps({"command": "UPDATE_MACHINE_KINETICS", "args": {"machine_id": machine_id, "matrix": matrix_3_4, "v_move": speed_vector}})))


def get_targets_list(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_TARGETS_LIST", "args": {"machine_id": machine_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


def get_target_idx(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_TARGET_IDX", "args": {"machine_id": machine_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


def set_target_id(machine_id, target_id):
	# target_id: index in targets list. 0 = no target
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_TARGET_ID", "args": {"machine_id": machine_id, "target_id": target_id}})))


def get_health(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_HEALTH", "args": {"machine_id": machine_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


def set_health(machine_id, level):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_HEALTH", "args": {"machine_id": machine_id, "health_level": level}})))


def get_machine_missiles_list(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_MACHINE_MISSILES_LIST", "args": {"machine_id": machine_id}})))
	return json.loads((socket_lib.get_answer()).decode())


def get_missiles_device_slots_state(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_MISSILESDEVICE_SLOTS_STATE", "args": {"machine_id": machine_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


def fire_missile(machine_id, slot_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "FIRE_MISSILE", "args": {"machine_id": machine_id, "slot_id": slot_id}})))


def rearm_machine(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "REARM_MACHINE", "args": {"machine_id": machine_id}})))


def reset_machine(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "RESET_MACHINE", "args": {"machine_id": machine_id}})))


def reset_machine_matrix(machine_id, x, y, z, rx, ry, rz):
	socket_lib.send_message(str.encode(json.dumps({"command": "RESET_MACHINE_MATRIX", "args": {"machine_id": machine_id, "position": [x, y, z], "rotation": [rx, ry, rz]}})))


def activate_autopilot(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "ACTIVATE_AUTOPILOT", "args": {"machine_id": machine_id}})))


def deactivate_autopilot(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "DEACTIVATE_AUTOPILOT", "args": {"machine_id": machine_id}})))


def activate_IA(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "ACTIVATE_IA", "args": {"machine_id": machine_id}})))


def deactivate_IA(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "DEACTIVATE_IA", "args": {"machine_id": machine_id}})))


def get_machine_gun_state(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_MACHINE_GUN_STATE", "args": {"machine_id": machine_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


def activate_machine_gun(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "ACTIVATE_MACHINE_GUN", "args": {"machine_id": machine_id}})))


def deactivate_machine_gun(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "DEACTIVATE_MACHINE_GUN", "args": {"machine_id": machine_id}})))


def is_autopilot_activated(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "IS_AUTOPILOT_ACTIVATED", "args": {"machine_id": machine_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


def activate_autopilot(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "ACTIVATE_AUTOPILOT", "args": {"machine_id": machine_id}})))


def deactivate_autopilot(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "DEACTIVATE_AUTOPILOT", "args": {"machine_id": machine_id}})))


def is_ia_activated(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "IS_IA_ACTIVATED", "args": {"machine_id": machine_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


def activate_ia(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "ACTIVATE_IA", "args": {"machine_id": machine_id}})))


def deactivate_ia(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "DEACTIVATE_IA", "args": {"machine_id": machine_id}})))


def is_user_control_activated(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "IS_USER_CONTROL_ACTIVATED", "args": {"machine_id": machine_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


def activate_user_control(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "ACTIVATE_USER_CONTROL", "args": {"machine_id": machine_id}})))


def deactivate_user_control(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "DEACTIVATE_USER_CONTROL", "args": {"machine_id": machine_id}})))


# Aircrafts

def get_planes_list():
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_PLANESLIST", "args": {}})))
	return json.loads((socket_lib.get_answer()).decode())


def get_plane_state(plane_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_PLANE_STATE", "args": {"plane_id": plane_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


def get_plane_thrust(plane_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_PLANE_THRUST", "args": {"plane_id": plane_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


def set_plane_thrust(plane_id, level):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_PLANE_THRUST", "args": {"plane_id": plane_id, "thrust_level": level}})))


def reset_gear(plane_id, gear_deployed: bool):
	socket_lib.send_message(str.encode(json.dumps({"command": "RESET_GEAR", "args": {"plane_id": plane_id, "gear_deployed": gear_deployed}})))


def set_plane_linear_speed(plane_id, speed):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_PLANE_LINEAR_SPEED", "args": {"plane_id": plane_id, "linear_speed": speed}})))


def record_plane_start_state(plane_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "RECORD_PLANE_START_STATE", "args": {"plane_id": plane_id}})))


def set_plane_brake(plane_id, level):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_PLANE_BRAKE", "args": {"plane_id": plane_id, "brake_level": level}})))


def set_plane_flaps(plane_id, level):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_PLANE_FLAPS", "args": {"plane_id": plane_id, "flaps_level": level}})))


def activate_post_combustion(plane_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "ACTIVATE_PC", "args": {"plane_id": plane_id}})))


def deactivate_post_combustion(plane_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "DEACTIVATE_PC", "args": {"plane_id": plane_id}})))


def set_plane_pitch(plane_id, level):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_PLANE_PITCH", "args": {"plane_id": plane_id, "pitch_level": level}})))


def set_plane_roll(plane_id, level):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_PLANE_ROLL", "args": {"plane_id": plane_id, "roll_level": level}})))


def set_plane_yaw(plane_id, level):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_PLANE_YAW", "args": {"plane_id": plane_id, "yaw_level": level}})))


def stabilize_plane(plane_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "STABILIZE_PLANE", "args": {"plane_id": plane_id}})))


def deploy_gear(plane_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "DEPLOY_GEAR", "args": {"plane_id": plane_id}})))


def retract_gear(plane_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "RETRACT_GEAR", "args": {"plane_id": plane_id}})))


def activate_plane_easy_steering(plane_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "ACTIVATE_EASY_STEERING", "args": {"plane_id": plane_id}})))


def deactivate_plane_easy_steering(plane_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "DEACTIVATE_EASY_STEERING", "args": {"plane_id": plane_id}})))


def set_plane_autopilot_heading(plane_id, level):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_PLANE_AUTOPILOT_HEADING", "args": {"plane_id": plane_id, "ap_heading": level}})))


def set_plane_autopilot_speed(plane_id, level):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_PLANE_AUTOPILOT_SPEED", "args": {"plane_id": plane_id, "ap_speed": level}})))


def set_plane_autopilot_altitude(plane_id, level):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_PLANE_AUTOPILOT_ALTITUDE", "args": {"plane_id": plane_id, "ap_altitude": level}})))


# Missile launchers

def get_missile_launchers_list():
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_MISSILE_LAUNCHERS_LIST", "args": {}})))
	return json.loads((socket_lib.get_answer()).decode())


def get_missile_launcher_state(machine_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_MISSILE_LAUNCHER_STATE", "args": {"machine_id": machine_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state

# Missiles

def get_missiles_list():
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_MISSILESLIST", "args": {}})))
	return json.loads((socket_lib.get_answer()).decode())


def get_missile_state(missile_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_MISSILE_STATE", "args": {"missile_id": missile_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


def set_missile_target(missile_id, target_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_MISSILE_TARGET", "args": {"missile_id": missile_id, "target_id": target_id}})))


def set_missile_life_delay(missile_id, life_delay):
	socket_lib.send_message(str.encode(json.dumps({"command": "SET_MISSILE_LIFE_DELAY", "args": {"missile_id": missile_id, "life_delay": life_delay}})))


def get_missile_targets_list(missile_id):
	socket_lib.send_message(str.encode(json.dumps({"command": "GET_MISSILE_TARGETS_LIST", "args": {"missile_id": missile_id}})))
	state = json.loads((socket_lib.get_answer()).decode())
	return state


