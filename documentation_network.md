# Dogfight Sandbox - Network documentation

## Network API

The "Network" mode allows you to control the planes from a third party machine or program.

### Globals functions

* **disable_log**()
* **enable_log**()
* dict = **get_running**()
* **set_renderless_mode**(bool flag)
* **set_display_radar_in_renderless_mode**(bool flag)
* **set_timestep**(float timestep)
* dict = **get_timestep**()
* **set_client_update_mode**(bool flag)
* **update_scene**()
* **display_vector**(list position[3], list direction[3], string label, list label_offset2D[2], list color[4], float label_size)
* **display_2DText**(list position[3], string text, float size, list color[4])

### Common Machines functions

* list = **get_machine_missiles_liste**(string machine_id)
* list = **get_targets_list**(string machine_id)
* dict = **get_health**(string machine_id)
* **set_health**(string machine_id, float health_level)
* **activate_autopilot**(string machine_id)
* **deactivate_autopilot**(string machine_id)
* **activate_IA**(string machine_id)
* **deactivate_IA**(string machine_id)
* dict = **get_machine_gun_state**(string machine_id)
* **activate_machine_gun**(string machine_id)
* **deactivate_machine_gun**(string machine_id)
* dict = **get_missiles_device_slots_state**(string machine_id)
* **fire_missile**(string machine_id, int slot_id)
* **rearm_machine**(string machine_id)
* dict = **get_target_idx**(string machine_id)
* **set_target_id**(string machine_id, string target_id)
* **reset_machine_matrix**(string machine_id, float x, float y, float z, float rx, float ry, float rz)
* **set_machine_custom_physics_mode**(string machine_id, bool flag)
* dict = **get_machine_custom_physics_mode**(string machine_id)
* **update_machine_kinetics**(string machine_id, list matrix_3_4[12], list speed_vector[3])
* list = **get_mobile_parts_list**(string machine_id)
* list = **is_autopilot_activated**(string machine_id)
* **activate_autopilot**(string machine_id)
* **deactivate_autopilot**(string machine_id)
* list = **is_ia_activated**(string machine_id)
* **activate_IA**(string machine_id)
* **deactivate_IA**(string machine_id)
* list = **is_user_control_activated**(string machine_id)
* **activate_user_control**(string machine_id)
* **deactivate_user_control**(string machine_id)

### Aircrafts functions

* list = **get_planes_list**()
* dict = **get_plane_state(string plane_id)
* **set_plane_thrust**(string plane_id)
* dict = **get_plane_thrust**(string plane_id)
* **activate_pc**(string plane_id)
* **deactivate_pc**(string plane_id)
* **set_plane_brake**(string plane_id, float level)
* **set_plane_flaps**(string plane_id, float level)
* **set_plane_pitch**(string plane_id, float level)
* **set_plane_roll**(string plane_id, float level)
* **set_plane_yaw**(string plane_id, float level)
* **stabilize_plane**(string plane_id)
* **deploy_gear**(string plane_id)
* **retract_gear**(string plane_id)
* **set_plane_autopilot_speed**(string plane_id, float level)
* **set_plane_autopilot_heading**(string plane_id, float level)
* **set_plane_autopilot_altitude**(string plane_id, float level)
* **activate_plane_easy_steering**(string plane_id)
* **deactivate_plane_easy_steering**(string plane_id)
* **set_plane_linear_speed**(string plane_id, float speed)
* **reset_gear**(string plane_id)
* **record_plane_start_state**(string plane_id)

### Missiles functions

* list = **get_missiles_list**()
* dict = **get_missile_state**()
* **set_missile_life_delay**(string missile_id, float_life_delay)
* list = **get_missile_targets_list**(string missile_id)
* **set_missile_target**(string missile_id, string target_id)

### Missile launchers functions

* list = **get_missile_launchers_list**()
* dict = **get_missile_launcher_state**(string machine_id)