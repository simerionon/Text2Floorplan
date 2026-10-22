"""Deployment physical scale and clear-floor-area checks for generated rooms."""
import json
import math
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

DEFAULT_MIN_AREAS_M2 = {
    "kitchen": 2.0, "bathroom": 2.0,
}


class PlanQualityError(ValueError):
    """A generated layout must be retried instead of imported into Revit."""


def load_physical_scale(size="medium", data_dir=None):
    """Apply deployment area calibration without altering measured dataset stats.

    Multipliers describe polygon area, so lengths change by their square root.
    Clear floor area must still subtract the unchanged physical wall widths.
    """
    if size not in {"small", "medium", "large"}:
        raise ValueError("Physical size must be small, medium or large")
    data_dir = Path(data_dir) if data_dir is not None else Path(__file__).resolve().parent / "data"
    statistics_path = data_dir / "raw_recovery_scale_stats.json"
    reference = 0.05
    if statistics_path.is_file():
        statistics = json.loads(statistics_path.read_text(encoding="utf-8"))
        reference = float(statistics["resplan_meter_scale"]["meters_per_raw_pixel"]["median"])
    policy_path = data_dir / "geometry_policy.json"
    multiplier = 1.0
    if policy_path.is_file():
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        multiplier = float(policy.get("output_area_multipliers", {}).get(size, 1.0))
    if not math.isfinite(reference) or reference <= 0:
        raise ValueError("Reference metre scale must be finite and positive")
    if not math.isfinite(multiplier) or multiplier <= 0:
        raise ValueError("Output area multiplier must be finite and positive")
    linear = math.sqrt(multiplier)
    return {
        "size": size,
        "reference_pixel_to_meter": reference,
        "output_area_multiplier": multiplier,
        "output_length_multiplier": linear,
        "pixel_to_meter": reference * linear,
    }


def load_min_areas():
    path = Path(__file__).resolve().parent / "data" / "geometry_policy.json"
    values = DEFAULT_MIN_AREAS_M2.copy()
    if path.is_file():
        values.update(json.loads(path.read_text(encoding="utf-8"))["minimum_room_areas_m2"])
    if any(not isinstance(v, (int, float)) or v <= 0 for v in values.values()):
        raise ValueError("Minimum room areas must be positive numbers")
    return values


def build_wall_footprints(walls, pixel_to_meter):
    """Join meeting wall faces without changing editable centerline endpoints.

    Two non-collinear end faces meet at their offset-line intersection. A mixed
    T retains the mitre between its two exterior walls while its inner branch
    butts into them. Straight T junctions retain the existing overlapping body.
    Limit very acute mitres to avoid unbounded spikes.
    """
    footprints, endpoints, joints, segments = [], {}, [], []
    tolerance = .00001 / pixel_to_meter
    for index, wall in enumerate(walls):
        line = LineString(wall["reference_line"])
        segments.append(line)
        half = wall["thickness_m"] / (2 * pixel_to_meter)
        footprints.append(line.buffer(half, cap_style=2, join_style=2))
        a, b = list(line.coords)
        length = line.length
        for start, end in ((a, b), (b, a)):
            key = tuple(round(v / tolerance) for v in start)
            endpoints.setdefault(key, []).append((index, start,
                ((end[0]-start[0])/length, (end[1]-start[1])/length), half))
    occupied = unary_union(footprints)
    for entries in endpoints.values():
        members = {entry[0] for entry in entries}
        pair = entries if len(entries) == 2 else [entry for entry in entries
            if walls[entry[0]].get("host") == "exterior_wall"]
        if len(pair) != 2:
            continue
        (i, origin, a, ha), (j, other, b, hb) = pair
        cross = a[0]*b[1]-a[1]*b[0]
        if abs(cross) < 1e-7:
            continue
        # A wall continuing through this point makes an overlapping T junction.
        if any(k not in members and line.distance(Point(origin)) < tolerance
               for k, line in enumerate(segments)):
            continue
        sign = 1 if cross > 0 else -1
        p = (origin[0]+sign*a[1]*ha, origin[1]-sign*a[0]*ha)
        q = (other[0]-sign*b[1]*hb, other[1]+sign*b[0]*hb)
        delta = (q[0]-p[0], q[1]-p[1])
        distance = (delta[0]*b[1]-delta[1]*b[0])/cross
        corner = (p[0]+a[0]*distance, p[1]+a[1]*distance)
        if math.dist(corner, origin) > 4*max(ha, hb):
            corner = origin
        addition = Polygon([origin, p, corner, q]).convex_hull.difference(occupied)
        patches = [addition] if addition.geom_type == "Polygon" else getattr(addition, "geoms", [])
        for patch in patches:
            if patch.geom_type != "Polygon" or patch.area <= tolerance**2:
                continue
            footprints.append(patch)
            occupied = occupied.union(patch)
            joints.append({"wall_ids": [walls[i].get("wall_id", str(i)), walls[j].get("wall_id", str(j))],
                "polygon": [list(p) for p in (list(patch.exterior.coords)[:-1] if patch.exterior.is_ccw
                                               else list(patch.exterior.coords)[:-1][::-1])],
                "height_m": min(walls[i].get("height_m", 3.3), walls[j].get("height_m", 3.3))})
    return unary_union(footprints), joints


def measure_room_areas(rooms, pixel_to_meter, walls=()):
    """Estimate clear floor area after subtracting wall footprints."""
    if pixel_to_meter <= 0:
        raise ValueError("Metre scale must be positive")
    wall_area, _ = build_wall_footprints(walls, pixel_to_meter)
    areas = {}
    for room in rooms:
        if room["type"] in {"front_door", "door"}:
            continue
        polygon = Polygon(room["polygon"])
        if polygon.is_empty or not polygon.is_valid:
            raise PlanQualityError(f"Room {room['room_id']} has invalid geometry")
        areas[str(room["room_id"])] = float(polygon.difference(wall_area).area * pixel_to_meter ** 2)
    return areas


def validate_room_areas(rooms, pixel_to_meter, minimum_areas=None, walls=()):
    limits = load_min_areas() if minimum_areas is None else minimum_areas
    areas = measure_room_areas(rooms, pixel_to_meter, walls)
    for room in rooms:
        kind = room["type"]
        if kind in {"front_door", "door"}:
            continue
        area = areas[str(room["room_id"])]
        minimum = float(limits.get(kind, 0.0))
        if area + 1e-8 < minimum:
            raise PlanQualityError(
                f"{kind} {room['room_id']} is too small: {area:.2f} m²; minimum {minimum:.2f} m²")
    return areas
