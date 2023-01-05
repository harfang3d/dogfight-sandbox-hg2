# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from math import radians, degrees
import json
import subprocess
import re
from tqdm import tqdm
import re
import os

def get_local_file_path(f):
	return os.path.join(os.path.dirname(os.path.realpath(__file__)), f)

def conform_string(s):
	# Remove all non-word characters (everything except numbers and letters)
	s = re.sub(r"[^\w\s]", '', s)
	# Replace all runs of whitespace with a single dash
	s = re.sub(r"\s+", '_', s)
	return s

def list_to_color(c: list):
	return hg.Color(c[0], c[1], c[2], c[3])


def color_to_list(c: hg.Color):
	return [c.r, c.g, c.b, c.a]


def list_to_vec2(v: list):
	return hg.Vec2(v[0], v[1])


def vec2_to_list(v: hg.Vec2):
	return [v.x, v.y]


def list_to_vec3(v: list):
	return hg.Vec3(v[0], v[1], v[2])


def list_to_vec3_radians(v: list):
	v = list_to_vec3(v)
	v.x = radians(v.x)
	v.y = radians(v.y)
	v.z = radians(v.z)
	return v

def list_to_mat4(v: list):
	return hg.TransformationMat4(hg.Vec3(v[0], v[1], v[2]), hg.Vec3(v[3], v[4], v[5]), hg.Vec3(v[6], v[7], v[8]))


def mat4_to_list(v: hg.Mat4):
	p, r, s = hg.Decompose(v)
	return [p.x, p.y, p.z, r.x, r.y, r.z, s.x, s.y, s.z]

def vec3_to_list(v: hg.Vec3):
	return [v.x, v.y, v.z]


def vec3_to_list_degrees(v: hg.Vec3):
	l = vec3_to_list(v)
	l[0] = degrees(l[0])
	l[1] = degrees(l[1])
	l[2] = degrees(l[2])
	return l

def serialize_vec3(v):
	return "{0:.6f};{1:.6f};{2:.6f}".format(
		v.x, v.y, v.z)

# bool("any_string") returns True
# bool("") (empty string) returns False
def serialize_boolean(v:bool):
    return "1" if v else ""

def deserialize_vec3(s):
	f = s.split(";")
	return hg.Vec3(float(f[0]), float(f[1]), float(f[2]))


def serialize_mat4(m):
	r0 = hg.GetRow(m, 0)
	r1 = hg.GetRow(m, 1)
	r2 = hg.GetRow(m, 2)
	return "{0:.6f};{1:.6f};{2:.6f};{3:.6f};{4:.6f};{5:.6f};{6:.6f};{7:.6f};{8:.6f};{9:.6f};{10:.6f};{11:.6f}".format(
		r0.x, r0.y, r0.z, r0.w,
		r1.x, r1.y, r1.z, r1.w,
		r2.x, r2.y, r2.z, r2.w)
		

def deserialize_mat4(s):
	f = s.split(";")
	m = hg.Mat4()
	hg.SetRow(m, 0, hg.Vec4(float(f[0]), float(f[1]), float(f[2]), float(f[3])))
	hg.SetRow(m, 1, hg.Vec4(float(f[4]), float(f[5]), float(f[6]), float(f[7])))
	hg.SetRow(m, 2, hg.Vec4(float(f[8]), float(f[9]), float(f[10]), float(f[11])))
	return m


def str_to_booleans(script):
    for k, v in script.items():
        if v.__class__ == str:
            if v == "true": script[k] = True
            elif v == "false": script[k] = False
        elif v.__class__ == dict:
            str_to_booleans(v)


def booleans_to_str(script):
    for k, v in script.items():
        if v.__class__ == bool:
            script[k] = "true" if v else "false"
        elif v.__class__ == dict:
            booleans_to_str(v)


def load_json_matrix(file_name):
	file = hg.OpenText(file_name)
	json_script = hg.ReadString(file)
	hg.Close(file)
	if json_script != "":
		script_parameters = json.loads(json_script)
		pos = list_to_vec3(script_parameters["position"])
		rot = list_to_vec3_radians(script_parameters["rotation"])
		return pos, rot
	return None, None


def save_json_matrix(pos: hg.Vec3, rot: hg.Vec3, output_filename):
	script_parameters = {"position": vec3_to_list(pos), "rotation": vec3_to_list_degrees(rot)}
	json_script = json.dumps(script_parameters, indent=4)
	file = hg.OpenWrite(output_filename)
	hg.WriteString(file, json_script)
	hg.Close(file)


# execute commande line and show stdout:
def run_command(exe):
	def execute_com(command):
		p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		return iter(p.stdout.readline, b'')

	t = tqdm(total=100)
	percent_prec = 0
	for line in execute_com(exe):
		txt = str(line)
		if "Progress" in txt:
			percent = int(re.findall('\d*%', txt)[0].split("%")[0])
			t.update(percent - percent_prec)
			percent_prec = percent
