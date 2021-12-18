# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from MathsSupp import *
from math import radians, degrees, pi, sqrt, exp
from random import uniform, random
import tools


class Particle:
	def __init__(self, node: hg.Node):
		self.node = node
		node.GetTransform().SetPos(hg.Vec3(0, -1000, 0))
		self.age = -1
		self.v_move = hg.Vec3(0, 0, 0)
		self.delay = 0
		self.scale = 1
		self.rot_speed = hg.Vec3(0, 0, 0)

	def destroy(self, scene):
		scene.DestroyNode(self.node)
		scene.GarbageCollect()

	def kill(self):
		self.age = -1
		self.node.GetTransform().SetPos(hg.Vec3(0, -1000, 0))
		self.node.GetTransform().SetScale(hg.Vec3(0.01, 0.01, 0.01))
		self.node.Disable()

	def get_enabled(self):
		if self.age > 0:
			return True
		else:
			return False


class ParticlesEngine:
	particle_id = 0
	_instances = []
	current_item = 0

	@classmethod
	def reset_engines(cls):
		cls._instances = []

	@classmethod
	def gui(cls):
		generators_list = hg.StringList()
		n = 0
		for engine in cls._instances:
			generators_list.push_back(engine.name)
			n += engine.num_particles

		if hg.ImGuiBegin("Particles settings"):
			hg.ImGuiSetWindowPos("Particles settings", hg.Vec2(680, 60), hg.ImGuiCond_Once)
			hg.ImGuiSetWindowSize("Particles settings", hg.Vec2(450, 930), hg.ImGuiCond_Once)

			hg.ImGuiText("Num generators: %d" % len(cls._instances))
			hg.ImGuiText("Num particles: %d" % n)
			f, d = hg.ImGuiListBox("Generators", cls.current_item, generators_list, 50)
			if f:
				cls.current_item = d
		hg.ImGuiEnd()

	def __init__(self, name, scene, original_node_name, num_particles, start_scale, end_scale, stream_angle, life_time=0., color_label="uColor", write_z=False):
		self.scene = scene
		self.name = name
		ParticlesEngine._instances.append(self)
		self.instance_id = len(ParticlesEngine._instances) - 1
		self.life_time = life_time  # flow life time.
		self.life_t = 0  # Life counter
		self.life_f = 1  # life factor
		self.flow_decrease_date = 0.75  # particles size & alpha decreases life time position (0,1)
		self.color_label = color_label
		self.particles_cnt = 0
		self.particles_cnt_max = 0
		self.particles_cnt_f = 0
		self.num_particles = num_particles
		self.num_alive = 0
		self.flow = 8
		self.particles_delay = 3
		self.particles = []
		self.create_particles(scene.GetNode(original_node_name), write_z)
		self.start_speed_range = hg.Vec2(800, 1200)
		self.delay_range = hg.Vec2(1, 2)
		self.start_scale = start_scale
		self.end_scale = end_scale
		self.scale_range = hg.Vec2(1, 2)
		self.stream_angle = stream_angle
		self.colors = [hg.Color(1, 1, 1, 1), hg.Color(1, 1, 1, 0)]
		self.start_offset = 0
		self.rot_range_x = hg.Vec2(0, 0)
		self.rot_range_y = hg.Vec2(0, 0)
		self.rot_range_z = hg.Vec2(0, 0)
		self.gravity = hg.Vec3(0, -9.8, 0)
		self.linear_damping = 1
		self.loop = True
		self.end = False  # True when loop=True and all particles are dead
		self.num_new = 0
		self.reset()

	def destroy(self):
		for part in self.particles:
			part.destroy(self.scene)
		self.particles = []

	# scene.GarbageCollect()

	def set_rot_range(self, xmin, xmax, ymin, ymax, zmin, zmax):
		self.rot_range_x = hg.Vec2(xmin, xmax)
		self.rot_range_y = hg.Vec2(ymin, ymax)
		self.rot_range_z = hg.Vec2(zmin, zmax)

	def create_particles(self, original_node, write_z):
		for i in range(self.num_particles):
			node = tools.duplicate_node_object(self.scene, original_node, self.name + "." + str(i))
			particle = Particle(node)
			material = particle.node.GetObject().GetMaterial(0)
			hg.SetMaterialWriteZ(material, write_z)
			self.particles.append(particle)

	def deactivate(self):
		for p in self.particles:
			p.node.Disable()

	def reset(self):
		self.num_new = 0
		self.particles_cnt = 0
		self.particles_cnt_f = 0
		self.end = False
		for i in range(self.num_particles):
			self.particles[i].age = -1
			self.particles[i].node.Disable()
			self.particles[i].v_move = hg.Vec3(0, 0, 0)

	def get_direction(self, main_dir):
		if self.stream_angle == 0: return main_dir
		axe0 = hg.Vec3(0, 0, 0)
		axeRot = hg.Vec3(0, 0, 0)
		while hg.Len(axeRot) < 1e-4:
			while hg.Len(axe0) < 1e-5:
				axe0 = hg.Vec3(uniform(-1, 1), uniform(-1, 1), uniform(-1, 1))
			axe0 = hg.Normalize(axe0)
			axeRot = hg.Cross(axe0, main_dir)
		axeRot = hg.Normalize(axeRot)
		return MathsSupp.rotate_vector(main_dir, axeRot, random() * radians(self.stream_angle))

	def update_color(self, particle: Particle):
		if len(self.colors) == 1:
			c = self.colors[0]
		else:
			c = MathsSupp.get_mix_color_value(particle.age / particle.delay, self.colors)
		material = particle.node.GetObject().GetMaterial(0)
		hg.SetMaterialValue(material, self.color_label, hg.Vec4(c.r, c.g, c.b, c.a * self.life_f))

	def reset_life_time(self, life_time=0.):
		self.life_time = life_time
		self.life_t = 0

	def update_kinetics(self, position: hg.Vec3, direction: hg.Vec3, v0: hg.Vec3, axisY: hg.Vec3, dts):

		if self.life_time > 0:
			self.life_t = min(self.life_time, self.life_t + dts)
			if self.life_t >= self.life_time - 1e-6:
				self.end = True
			t = self.life_t / self.life_time
			if t > self.flow_decrease_date:
				self.life_f = 1 - (t - self.flow_decrease_date) / (1 - self.flow_decrease_date)
		else:
			self.life_f = 1

		self.num_new = 0
		if not self.end:
			self.particles_cnt_f += dts * self.flow
			self.num_new = int(self.particles_cnt_f) - self.particles_cnt
			if self.particles_cnt_max > 0:
				if self.num_new + self.particles_cnt > self.particles_cnt_max:
					self.num_new = self.particles_cnt_max - self.particles_cnt
			if self.num_new > 0:
				for i in range(self.num_new):
					if not self.loop and self.particles_cnt + i >= self.num_particles: break
					particle = self.particles[(self.particles_cnt + i) % self.num_particles]
					particle.age = 0
					particle.delay = uniform(self.delay_range.x, self.delay_range.y)
					particle.scale = uniform(self.scale_range.x, self.scale_range.y) * self.life_f
					mat = particle.node.GetTransform()
					dir = self.get_direction(direction)
					rot_mat = hg.Mat3(hg.Cross(axisY, dir), axisY, dir)
					mat.SetPos(position + dir * self.start_offset)
					mat.SetRot(hg.ToEuler(rot_mat))
					mat.SetScale(self.start_scale)
					particle.rot_speed = hg.Vec3(uniform(self.rot_range_x.x, self.rot_range_x.y),
												 uniform(self.rot_range_y.x, self.rot_range_y.y),
												 uniform(self.rot_range_z.x, self.rot_range_z.y))
					particle.v_move = v0 + dir * uniform(self.start_speed_range.x, self.start_speed_range.y)
					particle.node.Disable()
				self.particles_cnt += self.num_new

			n = 0

			for particle in self.particles:
				if particle.age > particle.delay:
					particle.kill()
				elif particle.age == 0:
					particle.age += dts
					n += 1
				elif particle.age > 0:
					n += 1
					if not particle.node.IsEnabled(): particle.node.Enable()
					t = particle.age / particle.delay
					mat = particle.node.GetTransform()
					pos = mat.GetPos()
					rot = mat.GetRot()
					particle.v_move += self.gravity * dts
					spd = hg.Len(particle.v_move)
					particle.v_move -= hg.Normalize(particle.v_move) * spd * self.linear_damping * dts
					pos += particle.v_move * dts
					rot += particle.rot_speed * dts
					pos.y = max(0, pos.y)
					mat.SetPos(pos)
					mat.SetRot(rot)
					mat.SetScale((self.start_scale * (1 - t) + self.end_scale * t) * particle.scale)
					# material = particle.node.GetObject().GetGeometry().GetMaterial(0)
					# material.SetFloat4("self_color",1.,1.,0.,1-t)
					self.update_color(particle)
					# particle.node.GetObject().GetGeometry().GetMaterial(0).SetFloat4("teint", 1,1,1,1)
					particle.age += dts

			self.num_alive = n
			if n == 0 and not self.loop: self.end = True
