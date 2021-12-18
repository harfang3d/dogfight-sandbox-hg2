# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from math import cos, pi


class Animations:
	animations = []

	@staticmethod
	def interpolation_lineaire(a, b, t):
		return a * (1 - t) + b * t

	@staticmethod
	def interpolation_cosinusoidale(a, b, t):
		return Animations.interpolation_lineaire(a, b, (-cos(pi * t) + 1) / 2)

	@classmethod
	def update_animations(cls, t):
		for anim in cls.animations:
			anim.update(t)


class Animation:
	def __init__(self, t_start, delay, v_start, v_end):
		self.t_start = t_start
		self.delay = delay
		self.v_start = v_start
		self.v_end = v_end
		self.v = v_start
		self.flag_end = False

	def update(self, t):
		if t > self.t_start + self.delay:
			self.v = self.v_end
			self.flag_end = True
		elif t >= self.t_start:
			self.v = Animations.interpolation_cosinusoidale(self.v_start, self.v_end, (t - self.t_start) / self.delay)
		else:
			self.v = self.v_start
