"""Edit room boundaries and independent wall hosts in one plan document."""
from __future__ import annotations

import copy
import math

import numpy as np
from shapely.geometry import LineString, Point, Polygon

from plan_quality import load_min_areas, measure_room_areas, build_wall_footprints
from revit_geometry import build_revit_geometry, validate_opening_clearances
from web_editor.wall_editing import edit_wall, validate_lines, transform_wall_group
from web_editor.enclosed_areas import recalculate_spaces, room_polygon
from web_editor.opening_editing import move_opening, flip_opening


def number(value, name, minimum=None, maximum=None):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number")
    value = float(value)
    if not math.isfinite(value) or (minimum is not None and value < minimum) or (
            maximum is not None and value > maximum):
        raise ValueError(f"Invalid {name}")
    return value


def point_key(point):
    return tuple(round(float(v), 5) for v in point)


def validate_structure(plan):
    if plan.get("schema_version") != "1.0" or plan.get("coordinate_system") != "raw_canvas_px":
        raise ValueError("Import a Text2Revit schema 1.0 plan in raw_canvas_px coordinates")
    number(plan["pixel_to_meter"], "pixel_to_meter", 1e-6, 100)
    rooms = plan["rooms"]
    if not 1 <= len(rooms) <= 100:
        raise ValueError("A document must contain 1–100 rooms")
    ids = set()
    for room in rooms:
        if not isinstance(room["room_id"], int) or room["room_id"] in ids:
            raise ValueError("Room IDs must be unique integers")
        ids.add(room["room_id"])
        if not 3 <= len(room["polygon"]) <= 4096:
            raise ValueError("Each room must contain 3–4096 corners")
        if len(room.get("holes", [])) > 64:
            raise ValueError("Too many room boundary holes")
        for ring in [room["polygon"], *room.get("holes", [])]:
            if not 3 <= len(ring) <= 4096:
                raise ValueError("Invalid room boundary ring")
            for point in ring:
                if len(point) != 2:
                    raise ValueError("Corners must be XY pairs")
                for coordinate in point:
                    number(coordinate, "corner coordinate", -1e6, 1e6)
    if len(plan.get("openings", [])) > 256:
        raise ValueError("Too many openings")


def move_shared_corner(plan, origin, destination):
    """Propagate X along vertical runs and Y along horizontal runs, including T joins."""
    functional = [room for room in plan["rooms"] if room["type"] not in {"door", "front_door"}
                  and room.get("area_status", "closed") == "closed"]
    points = {point_key(p) for room in functional for p in room["polygon"]}
    origin = point_key(origin)
    if origin not in points:
        raise ValueError("Corner no longer exists")
    destination = [number(v, "corner coordinate", -1e6, 1e6) for v in destination]
    if len(destination) != 2:
        raise ValueError("A corner needs two coordinates")
    graphs = [{p: set() for p in points} for _ in range(2)]
    for room in functional:
        ring = [point_key(p) for p in room["polygon"]]
        for a, b in zip(ring, ring[1:] + ring[:1]):
            vertical = abs(a[0] - b[0]) < 1e-5
            horizontal = abs(a[1] - b[1]) < 1e-5
            if not vertical and not horizontal:
                continue
            fixed, varying = (0, 1) if vertical else (1, 0)
            on_edge = sorted((p for p in points if abs(p[fixed] - a[fixed]) < 1e-5
                              and min(a[varying], b[varying]) - 1e-5 <= p[varying]
                              <= max(a[varying], b[varying]) + 1e-5), key=lambda p: p[varying])
            for p, q in zip(on_edge, on_edge[1:]):
                graphs[fixed][p].add(q)
                graphs[fixed][q].add(p)
    components = []
    for graph in graphs:
        seen, queue = {origin}, [origin]
        while queue:
            for neighbor in graph[queue.pop()] - seen:
                seen.add(neighbor)
                queue.append(neighbor)
        components.append(seen)
    def transform(point):
        key = point_key(point)
        return [float(point[i]) + (destination[i] - origin[i] if key in components[i] else 0)
                for i in range(2)]
    for room in plan["rooms"]:
        room["polygon"] = [transform(p) for p in room["polygon"]]
    return transform


def translate_points(plan, points, delta):
    """Move the selected vertices once while propagating each orthogonal constraint."""
    transforms = []
    def composed(point):
        for transform in transforms:
            point = transform(point)
        return list(point)
    for point in points:
        current = composed(point)
        target = [point[i] + delta[i] for i in range(2)]
        if math.dist(current, target) > 1e-6:
            transforms.append(move_shared_corner(plan, current, target))
    return composed


def drag_handle(plan, command):
    """Use world-metre deltas for plan vertices and hosted elevation rectangles."""
    delta = command["delta_m"]
    if len(delta) != 3:
        raise ValueError("A handle displacement needs XYZ metres")
    delta = [number(v, "handle displacement", -100, 100) for v in delta]
    entity, handle = command["entity"], command["handle"]
    scale = plan["pixel_to_meter"]
    if entity in {"wall", "railing"}:
        if handle not in {"start", "end", "center"}:
            raise ValueError("Unknown wall handle")
        edit_wall(plan, {"type": "translate_wall" if handle == "center" else "move_wall_endpoint",
                        "id": command["id"], "endpoint": handle, "delta_m": delta}, entity)
        return lambda p: list(p)
    if entity == "opening":
        item = plan["openings"][int(command["id"])]
        wall = next(w for w in plan["walls"] if w["wall_id"] == item["wall_id"])
        a, b = np.asarray(wall["reference_line"], dtype=float) * scale
        direction = (b - a) / np.linalg.norm(b - a)
        center = np.asarray(item["center"]) * scale
        position = float(np.dot(center - a, direction))
        horizontal = float(np.dot(np.asarray(delta[:2]), direction))
        lo, hi = position - item["width_m"] / 2, position + item["width_m"] / 2
        bottom, top = item.get("sill_m", 0), item.get("sill_m", 0) + item["height_m"]
        if handle == "center":
            lo += horizontal; hi += horizontal
            bottom += delta[2]; top += delta[2]
        elif handle == "left":
            lo += horizontal
        elif handle == "right":
            hi += horizontal
        elif handle == "bottom":
            bottom += delta[2]
        elif handle == "top":
            top += delta[2]
        else:
            raise ValueError("Unknown opening handle")
        item.update(width_m=hi-lo, height_m=top-bottom, sill_m=bottom,
                    editor_position=(lo+hi) / (2*np.linalg.norm(b-a)))
        return lambda p: list(p)
    if abs(delta[2]) > 1e-8:
        raise ValueError("Plan handles move in the floor plane")
    delta = [v / scale for v in delta[:2]]
    if entity == "room":
        item = next(r for r in plan["rooms"] if r["room_id"] == command["id"])
        if item.get("area_status", "closed") != "closed":
            raise ValueError("Close the room's wall boundary before editing its room handles")
        points = item["polygon"]
        if handle.startswith("corner:"):
            points = [points[int(handle.split(":")[1])]]
        elif handle.startswith("edge:"):
            index = int(handle.split(":")[1])
            points = [points[index], points[(index + 1) % len(points)]]
            # Moving a room edge changes its perpendicular coordinate only.
            direction = np.asarray(points[1])-np.asarray(points[0])
            normal = np.array([-direction[1],direction[0]])/np.linalg.norm(direction)
            delta = (normal*np.dot(normal,delta)).tolist()
        elif handle != "center":
            raise ValueError("Unknown room handle")
    else:
        raise ValueError("Unknown editable entity")
    return translate_points(plan, copy.deepcopy(points), delta)


def rebuild(plan, previous=None, transform=lambda p: list(p)):
    """Rebuild linked walls or preserve free wall segments and their hosted openings."""
    validate_structure(plan)
    previous = previous or plan
    scale = float(plan["pixel_to_meter"])
    independent = plan.get("editor", {}).get("wall_mode") == "independent"
    if independent:
        walls, railings = plan["walls"], plan["railings"]
        for room in plan["rooms"]:
            if not room_polygon(room).is_valid or room_polygon(room).area <= 0:
                raise ValueError("Invalid room polygon")
        validate_lines(walls, "wall_id", scale)
        validate_lines(railings, "railing_id", scale)
        # Room edits do not regenerate or transform independently edited walls.
        transform = lambda p: list(p)
    else:
        walls, railings = build_revit_geometry(plan["rooms"], [], scale, int(plan.get("seed", 0)))
    mapping = {}
    for old in previous.get("walls", []):
        line = LineString([transform(p) for p in old["reference_line"]])
        candidates = [wall for wall in walls if wall["wall_id"] == old["wall_id"]] if independent else [wall for wall in walls
                      if set(wall["owner_room_ids"]) == set(old["owner_room_ids"])
                      and LineString(wall["reference_line"]).buffer(1e-4).covers(line)]
        if not candidates:
            raise ValueError("This edit changes wall connectivity. Try a smaller corner movement")
        wall = candidates[0]
        if not independent:
            for key, lower, upper in (("height_m", 0.3, 20), ("thickness_m", 0.03, 2)):
                wall[key] = number(old[key], key, lower, upper)
        mapping[old["wall_id"]] = (old, wall, LineString(wall["reference_line"]) if independent else line)
    for old in previous.get("railings", []):
        line = LineString([transform(p) for p in old["reference_line"]])
        candidates = [r for r in railings if r["railing_id"] == old["railing_id"]] if independent else [r for r in railings if r["owner_room_id"] == old["owner_room_id"]
                      and LineString(r["reference_line"]).buffer(1e-4).covers(line)]
        if not candidates:
            raise ValueError("This edit changes balcony connectivity")
        if not independent:
            candidates[0]["height_m"] = number(old.get("height_m", 1.1), "railing height", 0.1, 5)
    for opening in plan.get("openings", []):
        if opening["wall_id"] not in mapping:
            raise ValueError("Opening refers to a missing wall")
        old_wall, wall, moved_line = mapping[opening["wall_id"]]
        if opening["type"] not in {"door", "front_door", "window"}:
            raise ValueError("Unknown opening type")
        owners = {opening["owner_room_id"]}
        if opening.get("target_room_id") is not None:
            owners.add(opening["target_room_id"])
        if not owners <= set(wall["owner_room_ids"]) or opening["host"] != wall["host"]:
            raise ValueError("Opening ownership does not match its host wall")
        original_line = LineString(old_wall["reference_line"])
        position = opening.pop("editor_position", None)
        if position is None:
            position = original_line.project(Point(opening["center"]), normalized=True)
        else:
            position = number(position, "opening position", 0, 1)
        center = moved_line.interpolate(position, normalized=True)
        width = number(opening["width_m"], "opening width", 0.1, 10)
        height = number(opening["height_m"], "opening height", 0.1, 20)
        sill = number(opening.get("sill_m", 0), "window sill", 0, 20)
        if sill + height > wall["height_m"] + 1e-8:
            raise ValueError("Opening top exceeds its host wall height")
        half = width / (2 * scale)
        distance = moved_line.project(center)
        if distance < half + 0.025 / scale or moved_line.length - distance < half + 0.025 / scale:
            raise ValueError("Opening does not fit within its wall; reduce its width or move it")
        a, b = np.asarray(moved_line.coords[0]), np.asarray(moved_line.coords[-1])
        direction = (b - a) / np.linalg.norm(b - a)
        c = np.asarray(center.coords[0])
        normal = np.array([-direction[1], direction[0]])
        owner = next(r for r in plan["rooms"] if r["room_id"] == opening["owner_room_id"])
        inside = np.asarray(Polygon(owner["polygon"]).representative_point().coords[0])
        old_direction = np.asarray(old_wall["reference_line"][1])-np.asarray(old_wall["reference_line"][0])
        old_normal = np.array([-old_direction[1],old_direction[0]])
        flip = (np.dot(old_normal, opening.get("normal", old_normal)) < 0 if independent else
                (np.dot(normal, inside - c) < 0) != bool(opening.get("editor_swing_flipped", False)))
        if flip:
            normal *= -1
        opening.update(wall_id=wall["wall_id"], reference_line=[(c - direction * half).tolist(),
                       (c + direction * half).tolist()], center=c.tolist(), direction=direction.tolist(),
                       normal=normal.tolist(), width=width / scale, width_m=width, height_m=height, sill_m=sill)
    warnings = []
    if independent:
        for wall in walls:
            validate_opening_clearances([o for o in plan.get("openings", []) if o["wall_id"] == wall["wall_id"]], scale)
        try:
            validate_opening_clearances(plan.get("openings", []), scale)
        except ValueError as error:
            warnings.append(str(error))
    else:
        validate_opening_clearances(plan.get("openings", []), scale)
    plan["walls"], plan["railings"] = walls, railings
    if not independent:
        _, plan["wall_joints"] = build_wall_footprints(walls, scale)
    issues = recalculate_spaces(plan) if independent else []
    areas = plan["room_areas_m2"] if independent else measure_room_areas(plan["rooms"], scale, walls)
    if not independent and any(area <= 0 for area in areas.values()):
        raise ValueError("Wall thickness leaves a room with no clear floor area")
    if not independent:
        plan["room_areas_m2"], plan["total_area_m2"] = areas, sum(areas.values())
        plan["area_definition"] = "Estimated clear floor area including balconies; wall footprints excluded"
    minimums = load_min_areas()
    for room in plan["rooms"]:
        room["area"] = float(room_polygon(room).area)
        area = areas.get(str(room["room_id"]), 0)
        if area is not None and area < minimums.get(room["type"], 0):
            warnings.append(f"{room['name']}: {area:.1f} m² is below the generation minimum")
    plan["editor"] = {"version": 3 if independent else 1, "warnings": warnings}
    if independent:
        plan["editor"].update(wall_mode="independent", room_boundaries="walls", area_issues=issues,
            area_status="partial" if any(i["code"]=="open" for i in issues) else "complete")
    return plan


def import_document(document):
    return rebuild(copy.deepcopy(document))


def apply_command(document, command):
    """Apply an atomic edit to a copy. A rejected edit leaves the original untouched."""
    plan, previous = copy.deepcopy(document), copy.deepcopy(document)
    transform = lambda p: list(p)
    kind = command["type"]
    if kind == "move_opening":
        position = [number(v, "opening position", -1e6, 1e6) for v in command["position_m"]]
        move_opening(plan, int(command["id"]), position)
    elif kind == "flip_opening":
        flip_opening(plan, int(command["id"]), command["axis"])
    elif kind in {"translate_wall", "move_wall_endpoint"}:
        edit_wall(plan, command)
    elif kind == "drag_handle":
        transform = drag_handle(plan, command)
    elif kind == "move_corner":
        transform = move_shared_corner(plan, command["origin"], command["position"])
    elif kind == "move_wall":
        wall = next(w for w in plan["walls"] if w["wall_id"] == command["id"])
        a, b = wall["reference_line"]
        axis = 0 if abs(a[0] - b[0]) < 1e-5 else 1
        delta = [0, 0]
        delta[axis] = number(command["position_m"], "wall position") - a[axis] * plan["pixel_to_meter"]
        edit_wall(plan, {"type": "translate_wall", "id": command["id"], "delta_m": delta})
    elif kind == "set_parameters":
        entity = command["entity"]
        if entity == "wall":
            source = plan if plan.get("editor", {}).get("wall_mode") == "independent" else previous
            item = next(w for w in source["walls"] if w["wall_id"] == command["id"])
            allowed = {"height_m", "thickness_m"}
        elif entity == "opening":
            item = plan["openings"][int(command["id"])]
            allowed = {"height_m", "width_m", "sill_m", "editor_position"}
        elif entity == "railing":
            source = plan if plan.get("editor", {}).get("wall_mode") == "independent" else previous
            index = next(i for i, r in enumerate(source["railings"]) if r["railing_id"] == command["id"])
            item, allowed = source["railings"][index], {"height_m"}
        else:
            raise ValueError("Unknown editable entity")
        if set(command["values"]) - allowed:
            raise ValueError("Unsupported property")
        for key, value in command["values"].items():
            item[key] = number(value, key)
    else:
        raise ValueError("Unknown edit command")
    if plan.get("editor", {}).get("wall_mode") == "independent" and (
            kind == "move_corner" or kind == "drag_handle" and command["entity"] == "room"):
        transform_wall_group(plan, transform)
    plan.pop("debug", None)
    result = rebuild(plan, previous, transform)
    if kind == "move_opening":
        validate_opening_clearances(result["openings"], result["pixel_to_meter"])
    return result
