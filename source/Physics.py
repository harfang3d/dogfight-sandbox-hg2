# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from math import radians, degrees, pi, sqrt, exp, floor, acos, asin
from MathsSupp import *
import tools as tools
from overlays import *

air_density0 = 1.225 #  sea level standard atmospheric pressure, 101325 Pa
F_gravity = hg.Vec3(0, -9.8, 0)

scene = None
scene_physics = None
water_level = 0


terrain_heightmap = None
terrain_position = hg.Vec3(-24896, -296.87, 9443)
terrain_scale = hg.Vec3(41480, 1000, 19587)
map_bounds = hg.Vec2(0, 255)


def init_physics(scn, scn_physics, terrain_heightmap_file, p_terrain_pos, p_terrain_scale, p_map_bounds):
	global scene, scene_physics, terrain_heightmap, terrain_position, terrain_scale, map_bounds
	scene = scn
	scene_physics = scn_physics
	terrain_heightmap = hg.Picture()
	terrain_position = p_terrain_pos
	terrain_scale = p_terrain_scale
	map_bounds = p_map_bounds
	hg.LoadPicture(terrain_heightmap, terrain_heightmap_file)


def get_terrain_altitude(pos: hg.Vec3):
	global terrain_position, terrain_scale, terrain_heightmap, map_bounds
	pos2 = hg.Vec2((pos.x - terrain_position.x) / terrain_scale.x, 1 - (pos.z - terrain_position.z) / terrain_scale.z)
	return get_map_altitude(pos2), get_terrain_normale(pos2)


def get_map_altitude(pos2d):
	global terrain_position, terrain_scale, terrain_heightmap, map_bounds
	a = (tools.get_pixel_bilinear(terrain_heightmap, pos2d).r * 255 - map_bounds.x) / (map_bounds.y - map_bounds.x)
	a = max(water_level, a * terrain_scale.y + terrain_position.y)
	return a


def get_terrain_normale(pos2d):
	w = terrain_heightmap.GetWidth()
	h = terrain_heightmap.GetHeight()
	f = 1 / max(w, h)
	xd = hg.Vec2(f, 0)
	zd = hg.Vec2(0, f)
	return hg.Normalize(hg.Vec3(get_map_altitude(pos2d - xd) - get_map_altitude(pos2d + xd), 2 * f, get_map_altitude(pos2d - zd) - get_map_altitude(pos2d + zd)))


def _compute_atmosphere_temp(altitude):
	"""
	Internal function to compute atmospheric temperature according to altitude. Different layers have
	different temperature gradients, therefore the calculation is branched.
	Model is taken from ICAO DOC 7488: Manual of ICAO Standard Atmosphere.

	:param altitude: altitude in meters.
	:return: temperature in Kelvin.
	"""

	#Gradients are Kelvin/km.
	if altitude < 11e3:
		temperature_gradient = -6.5 #Kelvin per km.
		reference_temp = 288.15 #Temperature at sea level.
		altitude_diff = altitude - 0
	else:
		temperature_gradient = 0
		reference_temp = 216.65 #Temperature at 11km altitude.
		altitude_diff = altitude - 11e3

	return reference_temp + temperature_gradient*(altitude_diff / 1000)



def compute_atmosphere_density(altitude):
	# Barometric formula
	# temperature_K : based on ICAO Standard Atmosphere
	temperature_K = _compute_atmosphere_temp(altitude)
	R = 8.3144621  # ideal (universal) gas constant, 8.31446 J/(mol·K)
	M = 0.0289652  # molar mass of dry air, 0.0289652 kg/mol
	g = 9.80665  # earth-surface gravitational acceleration, 9.80665 m/s2
	d = air_density0 * exp(-altitude / (R * temperature_K / (M * g)))
	return d


def update_collisions(matrix: hg.Mat4, collisions_object, collisions_raycasts):
	rays_hits = []

	for collision_ray in collisions_raycasts:
		ray_hits = {"name": collision_ray["name"], "hits": []}
		c_pos = collision_ray["position"] * matrix
		c_dir = (collision_ray["position"] + collision_ray["direction"]) * matrix
		rc_len = hg.Len(collision_ray["direction"])

		hit = scene_physics.RaycastFirstHit(scene, c_pos, c_dir)

		if 0 < hit.t < rc_len:
			if not collisions_object.test_collision(hit.node):
				ray_hits["hits"].append(hit)
		rays_hits.append(ray_hits)

	terrain_alt, terrain_nrm = get_terrain_altitude(hg.GetT(matrix))

	return rays_hits, terrain_alt, terrain_nrm


def update_physics(matrix, collisions_object, physics_parameters, dts):

	aX = hg.GetX(matrix)
	aY = hg.GetY(matrix)
	aZ = hg.GetZ(matrix)

	# Cap, Pitch & Roll attitude:

	if aY.y > 0:
		y_dir = 1
	else:
		y_dir = -1

	horizontal_aZ = hg.Normalize(hg.Vec3(aZ.x, 0, aZ.z))
	horizontal_aX = hg.Cross(hg.Vec3.Up, horizontal_aZ) * y_dir
	horizontal_aY = hg.Cross(aZ, horizontal_aX)  # ! It's not an orthogonal repere !

	pitch_attitude = degrees(acos(max(-1, min(1, hg.Dot(horizontal_aZ, aZ)))))
	if aZ.y < 0: pitch_attitude *= -1

	roll_attitude = degrees(acos(max(-1, min(1, hg.Dot(horizontal_aX, aX)))))
	if aX.y < 0: roll_attitude *= -1

	heading = heading = degrees(acos(max(-1, min(1, hg.Dot(horizontal_aZ, hg.Vec3.Front)))))
	if horizontal_aZ.x < 0:
		heading = 360 - heading

	# axis speed:
	spdX = aX * hg.Dot(aX, physics_parameters["v_move"])
	spdY = aY * hg.Dot(aY, physics_parameters["v_move"])
	spdZ = aZ * hg.Dot(aZ, physics_parameters["v_move"])

	frontal_speed = hg.Len(spdZ)

	# Thrust force:
	k = pow(physics_parameters["thrust_level"], 2) * physics_parameters["thrust_force"]
	# if self.post_combustion and self.thrust_level == 1:
	#    k += self.post_combustion_force
	F_thrust = aZ * k

	pos = hg.GetT(matrix)

	# Air density:
	air_density = compute_atmosphere_density(pos.y)
	# Dynamic pressure:
	q = hg.Vec3(pow(hg.Len(spdX), 2), pow(hg.Len(spdY), 2), pow(hg.Len(spdZ), 2)) * 0.5 * air_density

	# F Lift
	F_lift = aY * q.z * physics_parameters["lift_force"]

	# Drag force:
	F_drag = hg.Normalize(spdX) * q.x * physics_parameters["drag_coefficients"].x + hg.Normalize(spdY) * q.y * physics_parameters["drag_coefficients"].y + hg.Normalize(spdZ) * q.z * physics_parameters["drag_coefficients"].z

	# Total

	physics_parameters["v_move"] += ((F_thrust + F_lift - F_drag) * physics_parameters["health_wreck_factor"] + F_gravity) * dts

	# Displacement:

	pos += physics_parameters["v_move"] * dts

	# Rotations:
	F_pitch = physics_parameters["angular_levels"].x * q.z * physics_parameters["angular_frictions"].x
	F_yaw = physics_parameters["angular_levels"].y * q.z * physics_parameters["angular_frictions"].y
	F_roll = physics_parameters["angular_levels"].z * q.z * physics_parameters["angular_frictions"].z

	# Angular damping:
	gaussian = exp(-pow(frontal_speed * 3.6 * 3 / physics_parameters["speed_ceiling"], 2) / 2)

	# Angular speed:
	angular_speed = hg.Vec3(F_pitch, F_yaw, F_roll) * gaussian

	# Moment:
	pitch_m = aX * angular_speed.x
	yaw_m = aY * angular_speed.y
	roll_m = aZ * angular_speed.z

	# Easy steering:
	if physics_parameters["flag_easy_steering"]:

		easy_yaw_angle = (1 - (hg.Dot(aX, horizontal_aX)))
		if hg.Dot(aZ, hg.Cross(aX, horizontal_aX)) < 0:
			easy_turn_m_yaw = horizontal_aY * -easy_yaw_angle
		else:
			easy_turn_m_yaw = horizontal_aY * easy_yaw_angle

		easy_roll_stab = hg.Cross(aY, horizontal_aY) * y_dir
		if y_dir < 0:
			easy_roll_stab = hg.Normalize(easy_roll_stab)
		else:
			n = hg.Len(easy_roll_stab)
			if n > 0.1:
				easy_roll_stab = hg.Normalize(easy_roll_stab)
				easy_roll_stab *= (1 - n) * n + n * pow(n, 0.125)

		zl = min(1, abs(physics_parameters["angular_levels"].z + physics_parameters["angular_levels"].x + physics_parameters["angular_levels"].y))
		roll_m += (easy_roll_stab * (1 - zl) + easy_turn_m_yaw) * q.z * physics_parameters["angular_frictions"].y * gaussian

	# Moment:
	torque = yaw_m + roll_m + pitch_m
	axis_rot = hg.Normalize(torque)
	moment_speed = hg.Len(torque) * physics_parameters["health_wreck_factor"]

	# Return matrix:

	rot_mat = MathsSupp.rotate_matrix(matrix, axis_rot, moment_speed * dts)
	mat = hg.TransformationMat4(pos, rot_mat)



	return mat, {"v_move": physics_parameters["v_move"], "pitch_attitude": pitch_attitude, "heading": heading, "roll_attitude": roll_attitude}