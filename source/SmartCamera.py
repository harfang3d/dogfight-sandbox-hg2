# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from math import radians, sqrt, pi, acos, asin
import MathsSupp as ms
import Physics
from Machines import Destroyable_Machine


class SmartCamera:
	TYPE_FOLLOW = 1
	TYPE_TRACKING = 2
	TYPE_SATELLITE = 3
	TYPE_FPS = 4
	TYPE_CINEMATIC = 5
	TYPE_FIX = 6
	TYPE_TACTICAL = 7

	def __init__(self, cam_type=TYPE_FOLLOW, keyboard=None, mouse=None):

		self.flag_hovering_gui = False

		self.flag_fix_mouse_controls_rotation = True  # True = FIX camera rotation controlled with mouse
		self.flag_reseting_rotation = False

		self.flag_inertia = True

		self.type = cam_type

		self.keyboard = keyboard
		self.mouse = mouse

		self.fix_pos = None
		self.fix_rot = None
		self.fix_rot_inertia = 0.1

		self.fps_pos = None
		self.fps_rot = None
		self.fps_rot_inertia = 0.1
		self.fps_pos_inertia = 0.1

		self.track_position = None  # Vec3
		self.track_orientation = None  # Mat3 - Rotation inertia matrix

		self.pos_inertia = 0.2
		self.rot_inertia = 0.07

		self.follow_inertia = 0.01
		self.follow_distance = 40
		self.lateral_rot = 20

		self.target_node = None
		self.target_point = None
		self.target_matrix = None

		self.satellite_view_size = 100
		self.satellite_view_size_inertia = 0.7
		self.satellite_view_ratio = 16 / 9

		self.camera_move = hg.Vec3(0, 0, 0)  # Translation in frame

		self.noise_x = ms.Temporal_Perlin_Noise(0.1446)
		self.noise_y = ms.Temporal_Perlin_Noise(0.1017)
		self.noise_z = ms.Temporal_Perlin_Noise(0.250314)
		self.noise_level = 0.1

		self.back_view = {"position": hg.Vec3(0, 4, -20),
						  "orientation": hg.Mat3(hg.Vec3(1, 0, 0), hg.Vec3(0, 1, 0), hg.Vec3(0, 0, 1)),
						  "pos_inertia": 0.2, "rot_inertia": 0.07}

		self.front_view = {"position": hg.Vec3(0, 4, 40),
						   "orientation": hg.Mat3(hg.Vec3(-1, 0, 0), hg.Vec3(0, 1, 0), hg.Vec3(0, 0, -1)),
						   "pos_inertia": 0.9, "rot_inertia": 0.05}

		self.right_view = {"position": hg.Vec3(-40, 4, 0),
						   "orientation": hg.Mat3(hg.Vec3(0, 0, -1), hg.Vec3(0, 1, 0), hg.Vec3(1, 0, 0)),
						   "pos_inertia": 0.9, "rot_inertia": 0.05}

		self.left_view = {"position": hg.Vec3(40, 4, 0),
						  "orientation": hg.Mat3(hg.Vec3(0, 0, 1), hg.Vec3(0, 1, 0), hg.Vec3(-1, 0, 0)),
						  "pos_inertia": 0.9, "rot_inertia": 0.05}

		self.top_view = {"position": hg.Vec3(0, 50, 0),
						 "orientation": hg.Mat3(hg.Vec3(1, 0, 0), hg.Vec3(0, 0, 1), hg.Vec3(0, -1, 0)),
						 "pos_inertia": 0.9, "rot_inertia": 0.05}

		self.views = {
			"back": self.back_view,
			"front": self.front_view,
			"right": self.right_view,
			"left": self.left_view,
			"top": self.top_view
		}

		self.current_view = ""
		self.set_track_view("back")

		self.cinematic_timer = 0
		self.keyframes = []

		# Tactical:

		self.subject_node = None
		self.tactical_subject_distance = 40
		self.minimal_tactical_altitude = 10
		self.projectil_node = None
		self.tactical_pos_inertia = 0.75

	# ----------- Call setup at view beginning:

	def setup(self, cam_type, camera: hg.Node, target_node: hg.Node = None, target_point: hg.Vec3 = None, target_matrix: hg.Mat3 = None):
		self.type = cam_type
		camera.GetTransform().ClearParent()
		if self.type == SmartCamera.TYPE_SATELLITE:
			self.setup_satellite_camera(camera)
		self.target_node = target_node
		if target_node is not None:
			w = target_node.GetTransform().GetWorld()
			if target_point is None:
				self.target_point = hg.GetT(w)
			else:
				self.target_point = target_point
			if target_matrix is None:
				self.target_matrix = hg.RotationMat3(hg.GetR(w))
			else:
				self.target_matrix = target_matrix

		if self.type == SmartCamera.TYPE_FOLLOW:
			self.update_follow_direction(camera)
			self.update_follow_translation(camera, 0, True)
		elif self.type == SmartCamera.TYPE_TRACKING:
			self.update_track_direction(camera, 0, 0)
			self.update_track_translation(camera)
		elif self.type == SmartCamera.TYPE_SATELLITE:
			self.update_satellite_camera(camera, 0, True)
		elif self.type == SmartCamera.TYPE_FPS:
			self.fps_pos = camera.GetTransform().GetPos()
			self.fps_rot = camera.GetTransform().GetRot()
			self.update_fps_camera(camera, 0)

		elif self.type == SmartCamera.TYPE_CINEMATIC:
			self.cinematic_timer = 0
			self.update_cinematic_camera(camera, 0)

		elif self.type == SmartCamera.TYPE_FIX:
			trans = camera.GetTransform()
			trans.SetPos(hg.Vec3(0, 0, 0))
			trans.SetRot(hg.Vec3(0, 0, 0))
			camera.GetTransform().SetParent(self.target_node)
			self.fix_rot = hg.Vec3(0, 0, 0) # FIX camera rotation reset to 0
			self.fix_pos = camera.GetTransform().GetPos()
			self.update_fix_camera(camera, 0)

	def setup_tactical(self,camera: hg.Node, subject_node: hg.Node, target_node:hg.Node, projectil_node:Destroyable_Machine = None ):
		self.type = SmartCamera.TYPE_TACTICAL
		camera.GetTransform().ClearParent()
		self.subject_node = subject_node
		self.target_node = target_node
		self.projectil_node = projectil_node
		self.target_point = self.compute_tactical_view_center(camera.GetTransform().GetPos())
		self.update_tactical_camera(camera, 0, True)

	def update(self, camera: hg.Camera, dts, noise_level=0):
		if self.type == SmartCamera.TYPE_FOLLOW:
			self.update_camera_follow(camera, dts)
		elif self.type == SmartCamera.TYPE_TRACKING:
			self.update_camera_tracking(camera, dts, noise_level)
		elif self.type == SmartCamera.TYPE_SATELLITE:
			self.update_satellite_camera(camera, dts)
		elif self.type == SmartCamera.TYPE_FPS:
			self.update_fps_camera(camera, dts)
		elif self.type == SmartCamera.TYPE_CINEMATIC:
			self.update_cinematic_camera(camera, dts)
		elif self.type == SmartCamera.TYPE_FIX:
			self.update_fix_camera(camera, dts, noise_level)
		elif self.type == SmartCamera.TYPE_TACTICAL:
			self.update_tactical_camera(camera, dts)

	def update_target_point(self, dts):
		if self.flag_inertia:
			v = self.target_node.GetTransform().GetPos() - self.target_point
			self.target_point += v * self.pos_inertia * dts * 60
			mat_n = hg.TransformationMat4(self.target_node.GetTransform().GetPos(), self.target_node.GetTransform().GetRot())
			rz = hg.Cross(hg.GetZ(self.target_matrix), hg.GetZ(mat_n))
			ry = hg.Cross(hg.GetY(self.target_matrix), hg.GetY(mat_n))
			mr = rz + ry
			le = hg.Len(mr)
			if le > 0.001:
				self.target_matrix = ms.MathsSupp.rotate_matrix(self.target_matrix, hg.Normalize(mr), le * self.rot_inertia * dts * 60)
		else:
			self.target_point = self.target_node.GetTransform().GetPos()
			self.target_matrix = hg.RotationMat3(hg.GetR(self.target_node.GetTransform().GetWorld()))

	# ============== Camera fix =====================
	def enable_mouse_controls_fix_rotation(self):
		self.flag_fix_mouse_controls_rotation = True

	def disable_mouse_controls_fix_rotation(self):
		self.flag_fix_mouse_controls_rotation = False


	def update_fix_camera(self, camera, dts, noise_level=0):
		f = radians(noise_level)
		rot = hg.Vec3(self.noise_x.temporal_Perlin_noise(dts) * f, self.noise_y.temporal_Perlin_noise(dts) * f, self.noise_z.temporal_Perlin_noise(dts) * f)

		if self.flag_fix_mouse_controls_rotation:

			if self.flag_reseting_rotation:
				self.fix_rot = self.fix_rot * 0.9
				camera.GetTransform().SetRot(self.fix_rot)
				if hg.Len(self.fix_rot) < 1e-4:
					self.fix_rot.x = self.fix_rot.y = self.fix_rot.z = 0
					self.flag_reseting_rotation = False
				rot = rot + self.fix_rot
			else:
				if self.mouse.Pressed(hg.MB_1):
					self.flag_reseting_rotation = True
				if not self.flag_hovering_gui:
					cam_t = camera.GetTransform()
					cam_fov = camera.GetCamera().GetFov()
					rot_fov = hg.Vec3(self.fix_rot)
					hg.FpsController(self.keyboard, self.mouse, self.fix_pos, self.fix_rot, 0, hg.time_from_sec_f(dts))
					self.fix_rot = rot_fov + (self.fix_rot - rot_fov) * cam_fov / (40/180*pi)

					#cam_pos0 = cam_t.GetPos()
					#cam_t.SetPos(cam_pos0 + (self.fps_pos - cam_pos0) * self.fps_pos_inertia)
					cam_rot0 = cam_t.GetRot()
					rot = rot + cam_rot0 + (self.fix_rot - cam_rot0) * self.fix_rot_inertia

		camera.GetTransform().SetRot(rot)

	# ============== Camera follow ==================

	def set_camera_follow_distance(self, distance):
		self.follow_distance = distance

	def update_camera_follow(self, camera: hg.Node, dts):
		self.update_target_point(dts)
		rot_mat = self.update_follow_direction(camera)
		pos = self.update_follow_translation(camera, dts)
		mat = hg.Mat4(rot_mat)
		hg.SetT(mat, pos)
		return mat

	def update_follow_direction(self, camera: hg.Node):
		v = self.target_point - camera.GetTransform().GetPos()
		rot_mat = hg.Mat3LookAt(v)
		rot = hg.ToEuler(rot_mat)
		camera.GetTransform().SetRot(rot)
		return rot_mat

	def update_follow_translation(self, camera: hg.Node, dts, init=False):
		trans = camera.GetTransform()
		camera_pos = trans.GetPos()
		aX = hg.GetX(trans.GetWorld())
		target_pos = self.target_node.GetTransform().GetPos()

		# Wall
		v = target_pos - camera_pos
		target_dir = hg.Normalize(v)
		target_dist = hg.Len(v)

		v_trans = target_dir * (target_dist - self.follow_distance) + aX * self.lateral_rot  # Déplacement latéral

		if init:
			new_position = camera_pos + v_trans
		else:
			new_position = camera_pos + v_trans * self.follow_inertia * 60 * dts
		trans.SetPos(new_position)
		self.camera_move = new_position - camera_pos
		return new_position

	# ============= Camera tracking =============================

	def set_camera_tracking_target_distance(self, distance):
		self.views["back"]["position"].z = -distance / 2
		self.views["back"]["position"].y = distance / 10

		self.views["front"]["position"].z = distance
		self.views["front"]["position"].y = distance / 10

		self.views["left"]["position"].x = distance
		self.views["left"]["position"].y = distance / 10

		self.views["right"]["position"].x = -distance
		self.views["right"]["position"].y = distance / 10

		self.views["top"]["position"].y = distance

	def update_camera_tracking(self, camera: hg.Node, dts, noise_level=0):
		self.update_target_point(dts)
		rot_mat = self.update_track_direction(camera, dts, noise_level)
		pos = self.update_track_translation(camera)
		mat = hg.Mat4(rot_mat)
		hg.SetT(mat, pos)

		return mat

	def update_track_direction(self, camera: hg.Node, dts, noise_level):
		# v = target_point - camera.GetTransform().GetPos()
		f = radians(noise_level)
		rot = hg.ToEuler(self.target_matrix)
		rot += hg.Vec3(self.noise_x.temporal_Perlin_noise(dts) * f, self.noise_y.temporal_Perlin_noise(dts) * f, self.noise_z.temporal_Perlin_noise(dts) * f)
		rot_mat = hg.RotationMat3(rot)
		rot_mat = rot_mat * self.track_orientation
		rot = hg.ToEuler(rot_mat)
		camera.GetTransform().SetRot(rot)
		return rot_mat  # hg.Mat3LookAt(v, target_matrix.GetY()))

	def update_track_translation(self, camera: hg.Node, init=False):
		trans = camera.GetTransform()
		camera_pos = trans.GetPos()
		new_position = self.target_point + hg.GetX(self.target_matrix) * self.track_position.x + hg.GetY(self.target_matrix) * self.track_position.y + hg.GetZ(self.target_matrix) * self.track_position.z
		trans.SetPos(new_position)
		self.camera_move = new_position - camera_pos
		return new_position

	# Views id: "back", "front", "left", "right", "top":
	def set_track_view(self, view_id):
		parameters = self.views[view_id]
		self.current_view = view_id
		self.track_position = parameters["position"]
		self.track_orientation = parameters["orientation"]
		self.pos_inertia = parameters["pos_inertia"]
		self.rot_inertia = parameters["rot_inertia"]

	# ======================== Satellite view ========================================

	def setup_satellite_camera(self, camera: hg.Node):
		camera.GetCamera().SetIsOrthographic(True)
		camera.GetCamera().SetSize(self.satellite_view_size)
		camera.GetTransform().SetRot(hg.Vec3(radians(90), 0, 0))

	def update_satellite_camera(self, camera, dts, init=False):
		if not init: self.update_target_point(dts)
		pos = hg.Vec3(self.target_point.x, self.target_point.y + camera.GetCamera().GetSize() * self.satellite_view_ratio, self.target_point.z)
		camera.GetTransform().SetPos(pos)
		# camera.GetTransform().SetPos(hg.Vec3(self.target_point.x, 1000, self.target_point.z))
		cam = camera.GetCamera()
		size = cam.GetSize()
		cam.SetSize(size + (self.satellite_view_size - size) * self.satellite_view_size_inertia)
		cam.SetZNear(1)
		cam.SetZFar(pos.y)

	def increment_satellite_view_size(self):
		self.satellite_view_size *= 1.01

	def decrement_satellite_view_size(self):
		self.satellite_view_size *= 0.99  # max(10, satellite_view_size / 1.01)

	# ======================== fps camera ========================================

	def update_hovering_ImGui(self):
		self.flag_hovering_gui = False
		if hg.ImGuiWantCaptureMouse() and hg.ReadMouse().Button(hg.MB_0):
			self.flag_hovering_gui = True
		if self.flag_hovering_gui and not hg.ReadMouse().Button(hg.MB_0):
			self.flag_hovering_gui = False

	def update_fps_camera(self, camera, dts):
		if not self.flag_hovering_gui:
			cam_t = camera.GetTransform()
			cam_fov = camera.GetCamera().GetFov()
			speed = 1
			if self.keyboard.Down(hg.K_LShift):
				speed = 100
			elif self.keyboard.Down(hg.K_LCtrl):
				speed = 1000
			elif self.keyboard.Down(hg.K_RCtrl):
				speed = 50000
			fps_rot_fov = hg.Vec3(self.fps_rot)
			hg.FpsController(self.keyboard, self.mouse, self.fps_pos, self.fps_rot, speed, hg.time_from_sec_f(dts))
			self.fps_rot = fps_rot_fov + (self.fps_rot - fps_rot_fov) * cam_fov / (40 / 180 * pi)

			cam_pos0 = cam_t.GetPos()
			cam_t.SetPos(cam_pos0 + (self.fps_pos - cam_pos0) * self.fps_pos_inertia)
			cam_rot0 = cam_t.GetRot()
			cam_t.SetRot(cam_rot0 + (self.fps_rot - cam_rot0) * self.fps_rot_inertia)

			if self.keyboard.Pressed(hg.K_Return):
				print("pos,rot,fov = hg.Vec3(%.3f,%.3f,%.3f),hg.Vec3(%.3f,%.3f,%.3f),%.3f" % (self.fps_pos.x, self.fps_pos.y, self.fps_pos.z, self.fps_rot.x, self.fps_rot.y, self.fps_rot.z, cam_fov))

	# ======================== Cinematic camera ========================================

	def set_keyframes(self, keyframes):
		self.keyframes = keyframes

	def update_cinematic_camera(self, camera, dts):
		if len(self.keyframes) > 0:
			cam_t = camera.GetTransform()
			# Get current tween:
			t_total = 0
			current_tween = None
			for tween in self.keyframes:
				if t_total <= self.cinematic_timer < t_total + tween["duration"]:
					current_tween = tween
					break
				else:
					t_total += tween["duration"]
			# Get t in tween
			if current_tween is None:
				# Cinematic loop
				self.cinematic_timer = 0
				t_total = 0
				current_tween = self.keyframes[0]
			t = (self.cinematic_timer - t_total) / current_tween["duration"]
			pos = current_tween["pos_start"] * (1 - t) + current_tween["pos_end"] * t
			rot = current_tween["rot_start"] * (1 - t) + current_tween["rot_end"] * t
			fov = current_tween["fov_start"] * (1 - t) + current_tween["fov_end"] * t
			cam_t.SetPos(pos)
			cam_t.SetRot(rot)
			camera.GetCamera().SetFov(fov)
			self.cinematic_timer += dts

	# ======================== Tactical camera ========================================

	def set_tactical_camera_distance(self, distance):
		self.tactical_subject_distance = distance

	def set_tactical_min_altitude(self, alt):
		self.minimal_tactical_altitude = alt

	def compute_tactical_view_center(self, camera_pos):
		v = hg.Normalize(self.subject_node.GetTransform().GetPos() - camera_pos)
		if self.target_node is not None:
			v_t = hg.Normalize(self.target_node.GetTransform().GetPos() - camera_pos)
			v += v_t
			v *= 0.5
			v = hg.Normalize(v)
		if self.projectil_node is not None:
			v_p = hg.Normalize(self.projectil_node.get_parent_node().GetTransform().GetPos() - camera_pos)
			v += v_p
			v *= 0.5
			v = hg.Normalize(v)
		return v + camera_pos

	def set_target_node(self, target_node: hg.Node):
		self.target_node = target_node

	def set_projectil_node(self, projectil_node: Destroyable_Machine):
		self.projectil_node = projectil_node

	def compute_camera_tactical_displacement(self, camera, cam_pos, target_node):
		subject_pos = self.subject_node.GetTransform().GetPos()
		dir_subject = hg.Normalize(subject_pos - cam_pos)
		cam_fov = camera.GetCamera().GetFov()
		target_pos = target_node.GetTransform().GetPos()
		dir_target = hg.Normalize(target_pos - cam_pos)
		angle = abs(acos(hg.Dot(dir_subject, dir_target)))
		if angle > cam_fov:
			# print("angle " + str(angle / pi * 180) + " FOV " + str(cam_fov / pi * 180))
			angle_diff = angle - cam_fov
			nrm = hg.Normalize(hg.Cross(dir_target, dir_subject))
			new_dir_subject = ms.MathsSupp.rotate_vector(dir_subject, nrm, -angle_diff)
			cam_subject_dist = hg.Len(subject_pos - cam_pos)
			p = cam_pos + new_dir_subject * cam_subject_dist
			v = subject_pos - p
			return v
		return None

	def update_tactical_camera(self, camera, dts, init=False):

		# update camera position:
		cam_pos = camera.GetTransform().GetPos()
		subject_pos = self.subject_node.GetTransform().GetPos()
		dir_subject = hg.Normalize(subject_pos - cam_pos)
		v = (subject_pos - dir_subject * self.tactical_subject_distance) - cam_pos
		if init:
			cam_pos += v
		else:
			cam_pos += v  # * self.tactical_pos_inertia

		if self.target_node is not None:
			v = self.compute_camera_tactical_displacement(camera, cam_pos, self.target_node)
			if v is not None:
				cam_pos += v

		"""
		if self.projectil_node is not None:
			if self.projectil_node.activated:
				v = self.compute_camera_tactical_displacement(camera, cam_pos, self.projectil_node.get_parent_node())
				if v is not None:
					cam_pos += v
			else:
				self.set_projectil_node(None)
		"""

		t_alt, t_nrm = Physics.get_terrain_Y(cam_pos)
		if cam_pos.y < t_alt + self.minimal_tactical_altitude:
			cam_pos.y = t_alt + self.minimal_tactical_altitude

		camera.GetTransform().SetPos(cam_pos)

		tvc = self.compute_tactical_view_center(cam_pos)
		# Update tactical view point
		v = tvc - self.target_point
		self.target_point += v

		dir = hg.Normalize(self.target_point - cam_pos)
		cam_rot = hg.ToEuler(hg.Mat3LookAt(dir, hg.Vec3.Up))
		camera.GetTransform().SetRot(cam_rot)