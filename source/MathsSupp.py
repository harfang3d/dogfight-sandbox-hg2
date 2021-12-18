# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from math import sin, cos, pi, inf
from random import uniform


class MathsSupp:
	@classmethod
	def smoothstep(cls, edge0, edge1, x):
		t = max(0, min((x - edge0) / (edge1 - edge0), 1.0))
		return t * t * (3.0 - 2.0 * t)

	@classmethod
	def rotate_vector(cls, point: hg.Vec3, axe: hg.Vec3, angle):
		axe = hg.Normalize(axe)
		dot_prod = point.x * axe.x + point.y * axe.y + point.z * axe.z
		cos_angle = cos(angle)
		sin_angle = sin(angle)

		return hg.Vec3(
			cos_angle * point.x + sin_angle * (axe.y * point.z - axe.z * point.y) + (1 - cos_angle) * dot_prod * axe.x, \
			cos_angle * point.y + sin_angle * (axe.z * point.x - axe.x * point.z) + (1 - cos_angle) * dot_prod * axe.y, \
			cos_angle * point.z + sin_angle * (axe.x * point.y - axe.y * point.x) + (1 - cos_angle) * dot_prod * axe.z)

	@classmethod
	def rotate_matrix(cls, mat, axe: hg.Vec3, angle):
		axeX = hg.GetX(mat)
		axeY = hg.GetY(mat)
		# axeZ=hg.GetZ(mat)
		axeXr = cls.rotate_vector(axeX, axe, angle)
		axeYr = cls.rotate_vector(axeY, axe, angle)
		axeZr = hg.Cross(axeXr, axeYr)  # cls.rotate_vector(axeZ,axe,angle)
		return hg.Mat3(axeXr, axeYr, axeZr)

	@classmethod
	def rotate_vector_2D(cls, p: hg.Vec2, angle):
		cos_angle = cos(angle)
		sin_angle = sin(angle)

		return hg.Vec2(p.x * cos_angle - p.y * sin_angle, p.x * sin_angle + p.y * cos_angle)

	@classmethod
	def get_sound_distance_level(cls, sounder_view_position: hg.Vec3):
		distance = hg.Len(sounder_view_position)
		return 1 / (distance / 10 + 1)

	@classmethod
	def get_mix_color_value(cls, f, colors):
		if f < 1:
			fc = f * (len(colors) - 1)
			i = int(fc)
			fc -= i
			return colors[i] * (1 - fc) + colors[i + 1] * fc
		else:
			return colors[-1]


# ===================================================================================
#          Génère une valeur temporelle aléatoire, lissée selon un bruit de Perlin
#          La valeur renvoyée est comprise entre -1 et 1
#          t: temps en s
#          t_prec: temps précédent en s
#          intervalle: l'intervalle de temps entre les valeurs aléatoires à interpôler (en s)
# ===================================================================================

class Temporal_Perlin_Noise:
	def __init__(self, interval=0.1):
		self.pt_prec = 0
		self.b0 = 0
		self.b1 = 0
		self.date = 0
		self.interval = interval

	def temporal_Perlin_noise(self, dts):
		self.date += dts
		t = self.date / self.interval
		pr = int(t)
		t -= self.pt_prec

		if pr > self.pt_prec:
			self.pt_prec = pr
			self.b0 = self.b1
			self.b1 = uniform(-1, 1)
			t = 0

		return self.b0 + (self.b1 - self.b0) * (sin(t * pi - pi / 2) * 0.5 + 0.5)


# ============================================================================================
#			Intersection box / ray
# ============================================================================================

def precompute_ray(dir: hg.Vec3):
	try:
		x = 1 / dir.x
	except:
		x = inf

	try:
		y = 1 / dir.y
	except:
		y = inf

	try:
		z = 1 / dir.z
	except:
		z = inf

	invdir = hg.Vec3(x, y, z)
	sign = [invdir.x < 0, invdir.y < 0, invdir.z < 0]
	return invdir, sign


def compute_relative_ray(pos, dir, mat):
	mati = hg.InverseFast(mat)
	rotmat = hg.GetRotationMatrix(mati)
	return mati * pos, rotmat * dir


def intersect_box_ray(bounds, pos, dir, invdir, sign, dist):
	# bounds=[mm.mn,mm.mx]
	tmin = (bounds[sign[0]].x - pos.x) * invdir.x
	tmax = (bounds[1 - sign[0]].x - pos.x) * invdir.x
	tymin = (bounds[sign[1]].y - pos.y) * invdir.y
	tymax = (bounds[1 - sign[1]].y - pos.y) * invdir.y

	if (tmin > tymax) or (tymin > tmax):
		return False
	if tymin > tmin:
		tmin = tymin
	if tymax < tmax:
		tmax = tymax

	tzmin = (bounds[sign[2]].z - pos.z) * invdir.z
	tzmax = (bounds[1 - sign[2]].z - pos.z) * invdir.z

	if (tmin > tzmax) or (tzmin > tmax):
		return False

	if tzmin > tmin:
		tmin = tzmin
	if tzmax < tmax:
		tmax = tzmax

	impact = pos + dir * tmin

	if hg.Len(impact - pos) > dist: return False

	return True
