
# Dogfight Sandbox client example
# This script show how to use the network mode to controls missiles.
# Before starts this script, Dogfight Sandbox must be running in "Network mode"
# dogfight_client.py is the library needed to communicate with DogFight sandbox

import dogfight_client as df
import time
from math import sin, cos

# Enter the IP and port displayed in top-left corner of DogFight screen
df.connect("192.168.42.86", 50888)

time.sleep(2)

# Get the whole planes list in DogFight scene
# returns a list that contains planes id
planes = df.get_planes_list()

#df.disable_log()

# Get the id of the plane you want to control
plane_id = planes[0]

# Reset the plane at its start state
df.reset_machine(plane_id)

# Get the plane missiles list
missiles = df.get_machine_missiles_list(plane_id)



# Get the missile id at slot 0
missile_slot = 0
missile_id = missiles[missile_slot]

#Change missile settings
df.set_missile_thrust_force(missile_id, 50)
df.set_missile_angular_frictions(missile_id, 0.11,0.22,0.33)
df.set_missile_drag_coefficients(missile_id, 1.1,2.2,3.2)

# Set client update mode ON: the scene update must be done by client network, calling "update_scene()"
df.set_client_update_mode(True)

# Fire missile to unhook from the plane:
df.fire_missile(plane_id, missile_slot)

# Take control of missile physics:
df.set_machine_custom_physics_mode(missile_id, True)

# Set missile life delay in s (set to 0 to turn off life delay)
df.set_missile_life_delay(missile_id, 10)

# Update scene
df.update_scene()

# Get missile state
missile_state = df.get_missile_state(missile_id)
x, y, z = missile_state["position"][0], missile_state["position"][1], missile_state["position"][2]

# Put missile at altitude 25 m
y = 25

# Model matrix 3 * 4
missile_matrix = [1, 0, 0,
				0, 1, 0,
				0, 0, 1,
				x, y, z]

# Linear displacement vector in m.s-1
missile_speed_vector = [0, 0.5, 3]

frame_time_step = 1/60

# Custom missile movements
t = 0
while not missile_state["wreck"]:
	time.sleep(1/60)
	missile_state = df.get_missile_state(missile_id)
	missile_matrix[9] = x
	missile_matrix[10] = y
	missile_matrix[11] = z

	df.update_machine_kinetics(missile_id, missile_matrix, missile_speed_vector)
	df.update_scene()
	x = 5 * sin(t*5)
	y = 25 + abs(sin(t)) * 10
	z = 60 + cos(t*1.256) * 50

	# Compute speed vector, used by missile engine smoke
	missile_speed_vector = [(x-missile_matrix[9]) / frame_time_step, (y - missile_matrix[10]) / frame_time_step, (z - missile_matrix[11]) / frame_time_step]

	t += frame_time_step


# Custom physics off
df.set_machine_custom_physics_mode(missile_id, False)

# Client update mode OFF
df.set_client_update_mode(False)

# Disconnect from the Dogfight server
df.disconnect()


