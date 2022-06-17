
# Dogfight Sandbox client example
# This script show how to use the network mode to controls aircraft kinetics.
# Before starts this script, Dogfight Sandbox must be running in "Network mode"
# dogfight_client.py is the library needed to communicate with DogFight sandbox

import dogfight_client as df
import time
from math import sin, cos

# Enter the IP and port displayed in top-left corner of DogFight screen
df.connect("192.168.1.22", 50888)

time.sleep(2)

# Get the whole planes list in DogFight scene
# returns a list that contains planes id
planes = df.get_planes_list()

#df.disable_log()

# Get the id of the plane you want to control
plane_id = planes[0]

# Reset the plane at its start state
df.reset_machine(plane_id)

# Set client update mode ON: the scene update must be done by client network, calling "update_scene()"
df.set_client_update_mode(True)

# Take control of aircraft physics:
df.set_machine_custom_physics_mode(plane_id, True)

# Update scene
df.update_scene()

# Get plane state
plane_state = df.get_plane_state(plane_id)
x, y, z = plane_state["position"][0], plane_state["position"][1], plane_state["position"][2]

# Put aircraft at altitude 25 m
y = 45

# Model matrix 3 * 4
plane_matrix = [1, 0, 0,
				0, 1, 0,
				0, 0, 1,
				x, y, z]

# Linear displacement vector in m.s-1
plane_speed_vector = [0, 0.5, 3]

frame_time_step = 1/60

# Custom missile movements
t = 0
while (not plane_state["wreck"]) and t < 500 * frame_time_step:
	time.sleep(1/60)
	plane_state = df.get_plane_state(plane_id)
	plane_matrix[9] = x
	plane_matrix[10] = y
	plane_matrix[11] = z
	df.update_machine_kinetics(plane_id, plane_matrix, plane_speed_vector)
	df.update_scene()
	x = 5 * sin(t*5)
	y = 45 + (sin(t)) * 5
	z = 60 + cos(t*1.256) * 50

	# Compute speed vector
	plane_speed_vector = [(x-plane_matrix[9]) / frame_time_step, (y - plane_matrix[10]) / frame_time_step, (z - plane_matrix[11]) / frame_time_step]

	t += frame_time_step

# Custom physics off
df.set_machine_custom_physics_mode(plane_id, False)

# Client update mode OFF
df.set_client_update_mode(False)

# Disconnect from the Dogfight server
df.disconnect()


