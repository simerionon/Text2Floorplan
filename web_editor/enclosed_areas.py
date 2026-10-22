"""Measure bounded spaces from current wall/railing centerlines and wall faces."""
import copy

from shapely import constrained_delaunay_triangles
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, snap, unary_union
from plan_quality import build_wall_footprints


def room_polygon(room):
    return Polygon(room["polygon"], room.get("holes", []))


def recalculate_spaces(plan):
    scale = float(plan["pixel_to_meter"])
    rooms = [r for r in plan["rooms"] if r["type"] not in {"door", "front_door"}]
    lines = [LineString(w["reference_line"]) for w in plan["walls"] + plan["railings"]]
    network = unary_union(lines)
    # Heal floating-point noise only; visible gaps must be closed by editing.
    network = unary_union(snap(network, network, .00001 / scale))
    footprints, plan["wall_joints"] = build_wall_footprints(plan["walls"], scale)
    cells = sorted(polygonize(network), key=lambda p: (*p.bounds, p.area))
    cells = [(p, p.difference(footprints)) for p in cells]
    cells = [(p, clear) for p, clear in cells if clear.area * scale**2 > 1e-6]
    references = {r["room_id"]: room_polygon(r) for r in rooms}
    anchors = {r["room_id"]: Point(r.get("area_anchor", r.get("interior_point",
        list(references[r["room_id"]].representative_point().coords[0])))) for r in rooms}
    owned = {}
    for room in rooms:
        rid = room["room_id"]
        owned[rid] = unary_union([LineString(w["reference_line"]) for w in plan["walls"]
            if rid in w["owner_room_ids"]] + [LineString(r["reference_line"]) for r in plan["railings"]
            if r["owner_room_id"] == rid])
    matches = []
    for index, (cell, _) in enumerate(cells):
        for room in rooms:
            rid = room["room_id"]
            support = cell.boundary.intersection(owned[rid]).length / cell.length
            overlap = cell.intersection(references[rid]).area / max(cell.area, references[rid].area)
            score = support * 4 + overlap * 2 + .5 * cell.contains(anchors[rid])
            if score > .5:
                matches.append((-score, rid, index))
    owners = [set() for _ in cells]
    assigned = set()
    for _, rid, index in sorted(matches):
        if rid not in assigned and not owners[index]:
            owners[index].add(rid)
            assigned.add(rid)
    # A vanished partition can merge rooms into one bounded space.
    for room in rooms:
        rid = room["room_id"]
        if rid in assigned:
            continue
        candidates = [(cell.intersection(references[rid]).area / references[rid].area, i)
            for i, (cell, _) in enumerate(cells)
            if cell.contains(anchors[rid]) or cell.intersection(references[rid]).area / references[rid].area > .5]
        if candidates:
            owners[max(candidates)[1]].add(rid)
    # Extra bounded cells inside an existing room are shown separately, not lost.
    for i, (cell, _) in enumerate(cells):
        if owners[i]:
            continue
        candidates = [(cell.intersection(references[r["room_id"]]).area / cell.area, r["room_id"]) for r in rooms]
        if candidates and max(candidates)[0] > .6:
            owners[i].add(max(candidates)[1])
    membership = {r["room_id"]: [i for i, group in enumerate(owners) if r["room_id"] in group] for r in rooms}
    spaces = []
    for i, ((cell, clear), group) in enumerate(zip(cells, owners)):
        status = "unassigned" if not group else "merged" if len(group) > 1 else (
            "split" if len(membership[next(iter(group))]) > 1 else "closed")
        point = clear.representative_point()
        mesh = constrained_delaunay_triangles(clear)
        spaces.append({"space_id": f"space_{i:03d}", "room_ids": sorted(group), "status": status,
            "polygon": [list(p) for p in list(cell.exterior.coords)[:-1]],
            "holes": [[list(p) for p in list(ring.coords)[:-1]] for ring in cell.interiors],
            "interior_point": [point.x, point.y], "area_m2": float(clear.area * scale**2),
            "floor_triangles": [[list(p) for p in list(t.exterior.coords)[:3]] for t in mesh.geoms]})
    areas, issues = {}, []
    for room in rooms:
        rid = room["room_id"]
        indices = membership[rid]
        status = "open" if not indices else "split" if len(indices) > 1 else spaces[indices[0]]["status"]
        room["area_status"] = status
        room["space_ids"] = [spaces[i]["space_id"] for i in indices]
        if status == "closed":
            space = spaces[indices[0]]
            room["polygon"], room["holes"] = copy.deepcopy(space["polygon"]), copy.deepcopy(space["holes"])
            room["interior_point"] = space["interior_point"].copy()
            room["area_anchor"] = space["interior_point"].copy()
            room["area"] = float(cells[indices[0]][0].area)
            areas[str(rid)] = space["area_m2"]
        else:
            areas[str(rid)] = None
            issues.append({"code": status, "room_id": rid, "room_name": room["name"]})
    plan["enclosed_spaces"] = spaces
    plan["room_areas_m2"] = areas
    plan["total_area_m2"] = sum(s["area_m2"] for s in spaces)
    plan["area_definition"] = "Current bounded wall/railing spaces minus wall footprints, including balconies; merged spaces counted once; unclosed rooms excluded"
    return issues
