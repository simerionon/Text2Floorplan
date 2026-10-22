"""Place an opening on a nearby wall without detaching its cut from the host."""
import math

from shapely.geometry import Polygon


HOST_SNAP_DISTANCE_M = 0.6
END_CLEARANCE_M = 0.025


def move_opening(plan, index, position):
    if len(position) != 2 or any(not math.isfinite(v) or abs(v) > 1e6 for v in position):
        raise ValueError("Opening position needs two finite metre coordinates")
    opening, scale = plan["openings"][index], plan["pixel_to_meter"]
    candidates = []
    for wall in plan["walls"]:
        if opening["type"] in {"window", "front_door"} and wall["host"] != "exterior_wall":
            continue
        if opening.get("sill_m", 0) + opening["height_m"] > wall["height_m"] + 1e-8:
            continue
        a, b = [[v * scale for v in p] for p in wall["reference_line"]]
        length = math.dist(a, b)
        margin = opening["width_m"] / 2 + END_CLEARANCE_M
        if length < 2 * margin:
            continue
        direction = [(b[i] - a[i]) / length for i in range(2)]
        along = max(margin, min(length - margin, sum((position[i] - a[i]) * direction[i] for i in range(2))))
        center = [a[i] + along * direction[i] for i in range(2)]
        distance = math.dist(position, center)
        if distance <= HOST_SNAP_DISTANCE_M:
            candidates.append((distance, wall["wall_id"] != opening["wall_id"], wall, along / length, center, direction))
    if not candidates:
        raise ValueError("Drop the opening within 600 mm of a wall that can contain it")
    _, _, wall, ratio, center, direction = min(candidates, key=lambda c: c[:2])
    owners = wall["owner_room_ids"]
    owner_id = opening["owner_room_id"] if opening["owner_room_id"] in owners else owners[0]
    owner = next(r for r in plan["rooms"] if r["room_id"] == owner_id)
    inside = Polygon(owner["polygon"]).representative_point()
    normal = [-direction[1], direction[0]]
    if sum(normal[i] * ([inside.x, inside.y][i] * scale - center[i]) for i in range(2)) < 0:
        normal = [-v for v in normal]
    if wall["wall_id"] == opening["wall_id"]:
        normal = opening.get("normal", normal)
    elif opening.get("editor_swing_flipped", False):
        normal = [-v for v in normal]
    opening.update(wall_id=wall["wall_id"], host=wall["host"], owner_room_id=owner_id,
                   target_room_id=next((r for r in owners if r != owner_id), None),
                   center=[v / scale for v in center], editor_position=ratio, normal=normal)


def flip_opening(plan, index, axis):
    opening = plan["openings"][index]
    if opening["type"] == "window":
        raise ValueError("Only doors have a swing direction and hinge side")
    if axis == "swing":
        opening["editor_swing_flipped"] = not opening.get("editor_swing_flipped", False)
        opening["normal"] = [-v for v in opening["normal"]]
    elif axis == "hinge":
        opening["hinge_side"] = "start" if opening.get("hinge_side", "start") == "end" else "end"
    else:
        raise ValueError("Choose swing or hinge")
