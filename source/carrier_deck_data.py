"""Shared aircraft carrier deck metadata extraction for scripts and runtime APIs."""

from __future__ import annotations

import copy
import json
import math
import struct
from functools import lru_cache
from pathlib import Path
from typing import Any


LANDING_HORIZONTAL_AMPLITUDE_M = 6000.0
LANDING_VERTICAL_AMPLITUDE_M = 500.0
LANDING_SMOOTH_LEVEL = 5

CORRIDOR_LATERAL_HALF_WIDTH_M = 12.0
CORRIDOR_AFT_MARGIN_M = 5.0
CORRIDOR_FORWARD_LIMIT_REQUESTED_M = 140.0
CORRIDOR_FORWARD_CLEARANCE_M = 15.0

GEO_HEADER_SIZE_BYTES = 13
GEO_CUBE_VERTEX_FLOAT_COUNT = 24
UINT32_MAX = 0xFFFFFFFF

MODULE_PATH = Path(__file__).resolve()
REPO_ROOT = MODULE_PATH.parents[1]
ASSETS_ROOT = REPO_ROOT / "source" / "assets"
SCENE_PATH = ASSETS_ROOT / "machines" / "aircraft_carrier_blend" / "aircraft_carrier_blend.scn"
DEFAULT_JSON_OUTPUT_PATH = REPO_ROOT / "source" / "scripts" / "aircraft_carrier_deck_parameters.json"


def round_float(value: float) -> float:
    return round(float(value), 6)


def round_data(value: Any) -> Any:
    if isinstance(value, float):
        return round_float(value)
    if isinstance(value, list):
        return [round_data(item) for item in value]
    if isinstance(value, dict):
        return {key: round_data(item) for key, item in value.items()}
    return value


def render_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def read_scene(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_cube_vertices(geo_path: Path) -> list[list[float]]:
    raw = geo_path.read_bytes()
    start = GEO_HEADER_SIZE_BYTES
    end = start + GEO_CUBE_VERTEX_FLOAT_COUNT * 4
    if len(raw) < end:
        raise ValueError(f"Unexpected short .geo file: {geo_path}")
    values = struct.unpack("<24f", raw[start:end])
    return [[values[i], values[i + 1], values[i + 2]] for i in range(0, len(values), 3)]


def get_node(scene: dict[str, Any], name: str) -> dict[str, Any]:
    for node in scene["nodes"]:
        if node["name"] == name:
            return node
    raise KeyError(f"Missing node: {name}")


def get_transform(scene: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    return scene["transforms"][node["components"][0]]


def get_object(scene: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    object_index = node["components"][2]
    if object_index == UINT32_MAX:
        raise KeyError(f"Node has no object: {node['name']}")
    return scene["objects"][object_index]


def resolve_asset_path(asset_relative_path: str) -> Path:
    return ASSETS_ROOT / Path(asset_relative_path)


def rotate_xyz_degrees(point: list[float], rotation_deg: list[float]) -> list[float]:
    x, y, z = point
    rx, ry, rz = [math.radians(v) for v in rotation_deg]

    cosx, sinx = math.cos(rx), math.sin(rx)
    cosy, siny = math.cos(ry), math.sin(ry)
    cosz, sinz = math.cos(rz), math.sin(rz)

    y, z = y * cosx - z * sinx, y * sinx + z * cosx
    x, z = x * cosy + z * siny, -x * siny + z * cosy
    x, y = x * cosz - y * sinz, x * sinz + y * cosz
    return [x, y, z]


def translate(point: list[float], offset: list[float]) -> list[float]:
    return [point[0] + offset[0], point[1] + offset[1], point[2] + offset[2]]


def vector_length(vector: list[float]) -> float:
    return math.sqrt(sum(component * component for component in vector))


def normalize_xyz(vector: list[float]) -> list[float]:
    length = vector_length(vector)
    if length == 0:
        raise ValueError("Cannot normalize zero-length vector")
    return [component / length for component in vector]


def normalize_xz(vector_xz: list[float]) -> list[float]:
    length = math.hypot(vector_xz[0], vector_xz[1])
    if length == 0:
        raise ValueError("Cannot normalize zero-length XZ vector")
    return [vector_xz[0] / length, vector_xz[1] / length]


def yaw_to_negative_z_axis(yaw_deg: float) -> list[float]:
    yaw_rad = math.radians(yaw_deg)
    return [-math.sin(yaw_rad), -math.cos(yaw_rad)]


def yaw_from_xz_axis(vector_xz: list[float]) -> float:
    return math.degrees(math.atan2(-vector_xz[0], -vector_xz[1]))


def landing_extremum(smooth_level: int) -> float:
    value = math.pi / 2
    for _ in range(smooth_level):
        value = math.sin(value)
    return value * 2


def landing_height_offset(distance: float, horizontal_amplitude: float, vertical_amplitude: float, smooth_level: int) -> float:
    x = distance / horizontal_amplitude
    if x >= 1:
        return vertical_amplitude
    if x <= 0:
        return 0.0
    value = x * math.pi - math.pi / 2
    for _ in range(smooth_level):
        value = math.sin(value)
    return (value / landing_extremum(smooth_level) + 0.5) * vertical_amplitude


def build_collision_bounds(scene: dict[str, Any]) -> tuple[list[float], list[float]]:
    world_points: list[list[float]] = []
    collision_nodes = sorted((node for node in scene["nodes"] if node["name"].startswith("carrier_col_shape")), key=lambda item: item["name"])

    for node in collision_nodes:
        transform = get_transform(scene, node)
        obj = get_object(scene, node)
        geo_vertices = read_cube_vertices(resolve_asset_path(obj["name"]))
        for vertex in geo_vertices:
            rotated = rotate_xyz_degrees(vertex, transform["rot"])
            world_points.append(translate(rotated, transform["pos"]))

    mins = [min(point[i] for point in world_points) for i in range(3)]
    maxs = [max(point[i] for point in world_points) for i in range(3)]
    return mins, maxs


def build_bounds_corners(bounds_min: list[float], bounds_max: list[float]) -> list[list[float]]:
    return [
        [bounds_min[0], bounds_min[1], bounds_min[2]],
        [bounds_min[0], bounds_min[1], bounds_max[2]],
        [bounds_min[0], bounds_max[1], bounds_min[2]],
        [bounds_min[0], bounds_max[1], bounds_max[2]],
        [bounds_max[0], bounds_min[1], bounds_min[2]],
        [bounds_max[0], bounds_min[1], bounds_max[2]],
        [bounds_max[0], bounds_max[1], bounds_min[2]],
        [bounds_max[0], bounds_max[1], bounds_max[2]],
    ]


def project_xz(origin_xz: list[float], axis_xz: list[float], point_xyz: list[float]) -> float:
    dx = point_xyz[0] - origin_xz[0]
    dz = point_xyz[2] - origin_xz[1]
    return dx * axis_xz[0] + dz * axis_xz[1]


def build_corridor(landing_point: dict[str, Any], bounds_min: list[float], bounds_max: list[float], rollout_axis_xz: list[float], deck_top_y: float) -> dict[str, Any]:
    landing_position = landing_point["local_position_m"]
    origin_xz = [landing_position[0], landing_position[2]]
    lateral_axis_xz = [rollout_axis_xz[1], -rollout_axis_xz[0]]

    bound_corners = build_bounds_corners(bounds_min, bounds_max)
    rollout_projections = [project_xz(origin_xz, rollout_axis_xz, point) for point in bound_corners]

    projected_min = min(rollout_projections)
    projected_max = max(rollout_projections)
    forward_rollout_limit = min(
        CORRIDOR_FORWARD_LIMIT_REQUESTED_M,
        projected_max - CORRIDOR_FORWARD_CLEARANCE_M,
    )

    def corridor_point(along_m: float, lateral_m: float) -> list[float]:
        x = origin_xz[0] + rollout_axis_xz[0] * along_m + lateral_axis_xz[0] * lateral_m
        z = origin_xz[1] + rollout_axis_xz[1] * along_m + lateral_axis_xz[1] * lateral_m
        return [x, deck_top_y, z]

    return {
        "centerline_anchor_local_m": landing_position,
        "rollout_axis_xz": rollout_axis_xz,
        "lateral_axis_xz": lateral_axis_xz,
        "lateral_half_width_m": CORRIDOR_LATERAL_HALF_WIDTH_M,
        "aft_margin_m": CORRIDOR_AFT_MARGIN_M,
        "forward_rollout_limit_m": forward_rollout_limit,
        "projected_rollout_bounds_on_collision_aabb_m": {
            "min": projected_min,
            "max": projected_max,
        },
        "corners_local_m": [
            corridor_point(-CORRIDOR_AFT_MARGIN_M, -CORRIDOR_LATERAL_HALF_WIDTH_M),
            corridor_point(-CORRIDOR_AFT_MARGIN_M, CORRIDOR_LATERAL_HALF_WIDTH_M),
            corridor_point(forward_rollout_limit, CORRIDOR_LATERAL_HALF_WIDTH_M),
            corridor_point(forward_rollout_limit, -CORRIDOR_LATERAL_HALF_WIDTH_M),
        ],
    }


def build_approach_entry(landing_point: dict[str, Any], approach_vector_xz: list[float]) -> list[float]:
    landing_position = landing_point["local_position_m"]
    distance = LANDING_HORIZONTAL_AMPLITUDE_M
    return [
        landing_position[0] + approach_vector_xz[0] * distance,
        landing_position[1] + landing_height_offset(
            distance,
            LANDING_HORIZONTAL_AMPLITUDE_M,
            LANDING_VERTICAL_AMPLITUDE_M,
            LANDING_SMOOTH_LEVEL,
        ),
        landing_position[2] + approach_vector_xz[1] * distance,
    ]


@lru_cache(maxsize=1)
def _build_local_carrier_deck_data_cached() -> dict[str, Any]:
    scene = read_scene(SCENE_PATH)

    landing_node = get_node(scene, "landing_point.001")
    landing_transform = get_transform(scene, landing_node)
    landing_point = {
        "name": landing_node["name"],
        "local_position_m": landing_transform["pos"],
        "local_yaw_deg": landing_transform["rot"][1],
    }

    start_nodes = sorted(
        (node for node in scene["nodes"] if node["name"].startswith("carrier_aircraft_start_point.")),
        key=lambda item: item["name"],
    )
    aircraft_start_points = []
    for node in start_nodes:
        transform = get_transform(scene, node)
        aircraft_start_points.append(
            {
                "name": node["name"],
                "local_position_m": transform["pos"],
                "local_yaw_deg": transform["rot"][1],
            }
        )

    bounds_min, bounds_max = build_collision_bounds(scene)
    bounds_size = [bounds_max[i] - bounds_min[i] for i in range(3)]
    deck_top_y = bounds_max[1]

    approach_vector_xz = normalize_xz(yaw_to_negative_z_axis(landing_point["local_yaw_deg"]))
    rollout_vector_xz = [-approach_vector_xz[0], -approach_vector_xz[1]]

    metadata = {
        "export_version": 1,
        "generated_from": {
            "scene_asset": str(SCENE_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
            "collision_geometry": [
                "source/assets/machines/aircraft_carrier_blend/carrier_col_shape.geo",
                "source/assets/machines/aircraft_carrier_blend/carrier_col_shape.001.geo",
                "source/assets/machines/aircraft_carrier_blend/carrier_col_shape.002.geo",
            ],
            "notes": [
                "Collision extents mirror runtime setup in source/Machines.py.",
                "The exporter uses raw collision cube sizes and scene positions/rotations.",
                "The source node 0.1 scale is intentionally ignored because runtime collision boxes are unscaled.",
            ],
        },
        "carrier_frame": {
            "origin_local_m": [0.0, 0.0, 0.0],
            "axes": {
                "+X": "starboard/right",
                "+Y": "up",
                "+Z": "ship-forward",
            },
        },
        "collision_bounds_local": {
            "min_m": bounds_min,
            "max_m": bounds_max,
            "size_m": bounds_size,
        },
        "deck_top_y_m": deck_top_y,
        "aircraft_start_points": aircraft_start_points,
        "landing_point": landing_point,
        "approach_profile": {
            "horizontal_amplitude_m": LANDING_HORIZONTAL_AMPLITUDE_M,
            "vertical_amplitude_m": LANDING_VERTICAL_AMPLITUDE_M,
            "smooth_level": LANDING_SMOOTH_LEVEL,
            "approach_entry_local_m": build_approach_entry(landing_point, approach_vector_xz),
        },
        "landing_vectors": {
            "approach_vector_xz": approach_vector_xz,
            "rollout_vector_xz": rollout_vector_xz,
        },
        "recommended_landing_corridor": build_corridor(
            landing_point,
            bounds_min,
            bounds_max,
            rollout_vector_xz,
            deck_top_y,
        ),
        "rl_landing_spec": {
            "baseline_vehicle": "Rafale",
            "observation_source": [
                "Existing plane state from the network API",
                "Offline deck metadata from this JSON file",
            ],
            "action_space": ["pitch", "roll", "yaw", "thrust"],
            "configuration_policy": {
                "auto_deploy_gear_below_along_track_m": 1200.0,
                "auto_set_flaps_to_landing_below_along_track_m": 1500.0,
                "auto_apply_brakes_after_valid_wheel_contact": True,
            },
            "reset_distribution": {
                "along_track_behind_touchdown_m": [1500.0, 3000.0],
                "cross_track_error_m": [-60.0, 60.0],
                "heading_error_deg": [-8.0, 8.0],
                "altitude_error_relative_to_glide_path_m": [-25.0, 25.0],
                "forward_speed_mps": [72.0, 82.0],
            },
            "success_criteria": {
                "touchdown_inside_valid_corridor": True,
                "touchdown_sink_rate_mps_max": 4.0,
                "absolute_roll_deg_max": 10.0,
                "absolute_pitch_deg_max": 15.0,
                "full_stop_inside_corridor_within_s": 20.0,
            },
            "failure_criteria": {
                "water_collision_or_crash_or_deck_miss": True,
                "first_wheel_contact_outside_corridor": True,
                "max_distance_past_touchdown_without_wheel_contact_m": 50.0,
                "episode_timeout_s": 90.0,
            },
            "reward_defaults": {
                "per_step": [
                    "-0.002*abs(cross_track_m)",
                    "-0.002*abs(alt_error_m)",
                    "-0.25*(abs(heading_error_deg)/45)",
                    "-0.01*max(0, abs(sink_rate_mps)-4)",
                    "-0.002*abs(speed_mps-78)",
                ],
                "near_approach_gate_bonus": {
                    "reward": 25.0,
                    "conditions": {
                        "along_track_m_lt": 500.0,
                        "cross_track_m_abs_lt": 10.0,
                        "alt_error_m_abs_lt": 10.0,
                        "heading_error_deg_abs_lt": 5.0,
                    },
                },
                "valid_touchdown_bonus": 100.0,
                "valid_full_stop_bonus": 150.0,
                "failure_penalty": -100.0,
            },
            "scope_notes": [
                "Static deck only in phase 1.",
                "No arresting wire, catapult, sea-state, or real-carrier calibration.",
            ],
        },
    }
    return round_data(metadata)


def build_local_carrier_deck_data() -> dict[str, Any]:
    return copy.deepcopy(_build_local_carrier_deck_data_cached())


def local_point_to_world(point_local: list[float], axes_world: dict[str, list[float]], origin_world_m: list[float]) -> list[float]:
    return [
        origin_world_m[0] + axes_world["x"][0] * point_local[0] + axes_world["y"][0] * point_local[1] + axes_world["z"][0] * point_local[2],
        origin_world_m[1] + axes_world["x"][1] * point_local[0] + axes_world["y"][1] * point_local[1] + axes_world["z"][1] * point_local[2],
        origin_world_m[2] + axes_world["x"][2] * point_local[0] + axes_world["y"][2] * point_local[1] + axes_world["z"][2] * point_local[2],
    ]


def local_vector_to_world(vector_local: list[float], axes_world: dict[str, list[float]]) -> list[float]:
    return normalize_xyz(
        [
            axes_world["x"][0] * vector_local[0] + axes_world["y"][0] * vector_local[1] + axes_world["z"][0] * vector_local[2],
            axes_world["x"][1] * vector_local[0] + axes_world["y"][1] * vector_local[1] + axes_world["z"][1] * vector_local[2],
            axes_world["x"][2] * vector_local[0] + axes_world["y"][2] * vector_local[1] + axes_world["z"][2] * vector_local[2],
        ]
    )


def yaw_to_forward_vector_local(yaw_deg: float) -> list[float]:
    xz = yaw_to_negative_z_axis(yaw_deg)
    return [xz[0], 0.0, xz[1]]


def build_api_carrier_deck_payload(carrier_id: str, nationality: int, origin_world_m: list[float], axes_world: dict[str, list[float]], local_data: dict[str, Any] | None = None) -> dict[str, Any]:
    if local_data is None:
        local_data = build_local_carrier_deck_data()
    else:
        local_data = copy.deepcopy(local_data)

    frame_axes_world = {axis: normalize_xyz(values) for axis, values in axes_world.items()}

    def point_world(point_local: list[float]) -> list[float]:
        return local_point_to_world(point_local, frame_axes_world, origin_world_m)

    def forward_axis_world(yaw_deg: float) -> list[float]:
        return local_vector_to_world(yaw_to_forward_vector_local(yaw_deg), frame_axes_world)

    aircraft_start_points_world = []
    for item in local_data["aircraft_start_points"]:
        forward_world = forward_axis_world(item["local_yaw_deg"])
        aircraft_start_points_world.append(
            {
                "name": item["name"],
                "world_position_m": point_world(item["local_position_m"]),
                "world_yaw_deg": yaw_from_xz_axis(normalize_xz([forward_world[0], forward_world[2]])),
                "world_forward_axis": forward_world,
            }
        )

    landing_forward_world = forward_axis_world(local_data["landing_point"]["local_yaw_deg"])
    approach_vector_world = local_vector_to_world(
        [
            local_data["landing_vectors"]["approach_vector_xz"][0],
            0.0,
            local_data["landing_vectors"]["approach_vector_xz"][1],
        ],
        frame_axes_world,
    )
    rollout_vector_world = local_vector_to_world(
        [
            local_data["landing_vectors"]["rollout_vector_xz"][0],
            0.0,
            local_data["landing_vectors"]["rollout_vector_xz"][1],
        ],
        frame_axes_world,
    )
    lateral_vector_world = local_vector_to_world(
        [
            local_data["recommended_landing_corridor"]["lateral_axis_xz"][0],
            0.0,
            local_data["recommended_landing_corridor"]["lateral_axis_xz"][1],
        ],
        frame_axes_world,
    )

    world_data = {
        "aircraft_start_points": aircraft_start_points_world,
        "landing_point": {
            "name": local_data["landing_point"]["name"],
            "world_position_m": point_world(local_data["landing_point"]["local_position_m"]),
            "world_yaw_deg": yaw_from_xz_axis(normalize_xz([landing_forward_world[0], landing_forward_world[2]])),
            "world_forward_axis": landing_forward_world,
        },
        "approach_profile": {
            "approach_entry_world_m": point_world(local_data["approach_profile"]["approach_entry_local_m"]),
        },
        "landing_vectors": {
            "approach_vector_world": approach_vector_world,
            "approach_vector_world_xz": normalize_xz([approach_vector_world[0], approach_vector_world[2]]),
            "rollout_vector_world": rollout_vector_world,
            "rollout_vector_world_xz": normalize_xz([rollout_vector_world[0], rollout_vector_world[2]]),
        },
        "recommended_landing_corridor": {
            "centerline_anchor_world_m": point_world(local_data["recommended_landing_corridor"]["centerline_anchor_local_m"]),
            "rollout_axis_world": rollout_vector_world,
            "lateral_axis_world": lateral_vector_world,
            "corners_world_m": [point_world(point) for point in local_data["recommended_landing_corridor"]["corners_local_m"]],
        },
    }

    payload = {
        "carrier_id": carrier_id,
        "type": "SHIP",
        "nationality": nationality,
        "frame": {
            "origin_world_m": origin_world_m,
            "axes_world": frame_axes_world,
        },
        "local": local_data,
        "world": round_data(world_data),
    }
    return round_data(payload)
