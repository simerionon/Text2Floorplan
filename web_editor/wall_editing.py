"""Independent wall translation and endpoint editing; rooms remain separate."""
import math

import numpy as np


def validate_lines(items, key, scale):
    ids=set()
    if len(items)>2000:
        raise ValueError("Too many wall segments")
    for item in items:
        identity=item[key]
        if not isinstance(identity,str) or identity in ids:
            raise ValueError("Wall and railing IDs must be unique strings")
        ids.add(identity)
        line=np.asarray(item["reference_line"],dtype=float)
        if line.shape!=(2,2) or not np.isfinite(line).all() or np.abs(line).max()>1e6:
            raise ValueError("Wall endpoints must be finite XY pairs")
        if np.linalg.norm(line[1]-line[0])*scale<.005:
            raise ValueError("A wall segment must be at least 5 mm long")
        for name,lo,hi in (("height_m",.1,20),("thickness_m",.03,2)):
            if name not in item and name=="thickness_m":continue
            value=float(item[name])
            if not math.isfinite(value) or not lo<=value<=hi:
                raise ValueError(f"Invalid {name}")


def replace_line(plan,wall,moved,entity="wall"):
    scale=float(plan["pixel_to_meter"])
    original=np.asarray(wall["reference_line"],dtype=float)
    moved=np.asarray(moved,dtype=float)
    length=np.linalg.norm(moved[1]-moved[0])
    if length*scale<.005:raise ValueError("A wall segment must be at least 5 mm long")
    old_length=np.linalg.norm(original[1]-original[0])
    direction=(original[1]-original[0])/old_length
    # Keep each opening's station from the stationary endpoint during resizing.
    for opening in plan.get("openings",[]):
        if entity!="wall" or opening["wall_id"]!=wall["wall_id"]:continue
        station=float(np.dot(np.asarray(opening["center"])-original[0],direction))
        if np.allclose(moved[1],original[1],atol=1e-7,rtol=0):station=length-(old_length-station)
        elif not np.allclose(moved[0]-original[0],moved[1]-original[1],atol=1e-7,rtol=0) and not np.allclose(moved[0],original[0],atol=1e-7,rtol=0):
            station=station/old_length*length
        opening["editor_position"]=station/length
    wall["reference_line"]=moved.tolist()
    plan.setdefault("editor",{})["wall_mode"]="independent"


def edit_wall(plan,command,entity="wall"):
    wall=next(w for w in plan["walls" if entity=="wall" else "railings"] if w[entity+"_id"]==command["id"])
    delta=np.asarray(command["delta_m"],dtype=float)
    if delta.shape not in {(2,),(3,)} or not np.isfinite(delta).all() or np.abs(delta).max()>100:
        raise ValueError("Wall movement needs finite XY metres")
    if len(delta)==3 and abs(delta[2])>1e-8:raise ValueError("Wall controls move in the floor plane")
    moved=np.asarray(wall["reference_line"],dtype=float).copy()
    if command["type"]=="translate_wall":moved+=delta[:2]/plan["pixel_to_meter"]
    elif command["type"]=="move_wall_endpoint":
        endpoint=command["endpoint"]
        if endpoint not in {"start","end"}:raise ValueError("Unknown wall endpoint")
        moved[0 if endpoint=="start" else 1]+=delta[:2]/plan["pixel_to_meter"]
    else:raise ValueError("Unknown wall operation")
    replace_line(plan,wall,moved,entity)


def transform_wall_group(plan,transform):
    """An explicit room-boundary edit moves its connected physical wall nodes."""
    for entity,items in (("wall",plan["walls"]),("railing",plan["railings"])):
        for item in items:
            moved=[transform(p) for p in item["reference_line"]]
            if not np.allclose(moved,item["reference_line"],atol=1e-7,rtol=0):
                replace_line(plan,item,moved,entity)
