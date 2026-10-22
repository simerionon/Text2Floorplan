"""Areas follow current bounded wall spaces, not stale room polygons."""
import json
from pathlib import Path
import sys
import unittest

from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from web_editor.model_document import apply_command, import_document


class EnclosedAreaTests(unittest.TestCase):
    def document(self,two=False):
        rooms=[{"room_id":0,"name":"living_0","type":"living","polygon":[[0,0],[100,0],[100,100],[0,100]]}]
        if two:rooms.append({"room_id":1,"name":"bedroom_0","type":"bedroom","polygon":[[100,0],[200,0],[200,100],[100,100]]})
        return import_document({"schema_version":"1.0","coordinate_system":"raw_canvas_px","pixel_to_meter":.05,
            "rooms":rooms,"walls":[],"railings":[],"openings":[]})

    def top(self,plan):
        return next(w for w in plan["walls"] if w["reference_line"]==[[0.,0.],[100.,0.]])

    def move(self,plan,wall,delta):
        return apply_command(plan,{"type":"translate_wall","id":wall["wall_id"],"delta_m":delta})

    def test_closed_wall_move_recomputes_room_polygon_and_net_area(self):
        p=self.document();result=self.move(p,self.top(p),[0,.5])
        self.assertEqual(result["rooms"][0]["area_status"],"closed")
        self.assertAlmostEqual(result["room_areas_m2"]["0"],4.6*4.1)
        self.assertAlmostEqual(Polygon(result["rooms"][0]["polygon"]).area*.05**2,22.5)

    def test_open_room_reports_no_area_and_closing_it_restores_area(self):
        p=self.document();wall=self.top(p);opened=self.move(p,wall,[0,-.5])
        self.assertIsNone(opened["room_areas_m2"]["0"])
        self.assertEqual(opened["rooms"][0]["area_status"],"open")
        self.assertEqual(opened["total_area_m2"],0)
        self.assertEqual(opened["editor"]["area_status"],"partial")
        closed=self.move(opened,wall,[0,.5])
        self.assertAlmostEqual(closed["room_areas_m2"]["0"],4.6**2)

    def test_shared_partition_move_updates_both_rooms_without_double_counting(self):
        p=self.document(True);wall=next(w for w in p["walls"] if w["owner_room_ids"]==[0,1])
        result=self.move(p,wall,[.5,0])
        self.assertAlmostEqual(result["room_areas_m2"]["0"],5.2*4.6)
        self.assertAlmostEqual(result["room_areas_m2"]["1"],4.2*4.6)
        self.assertAlmostEqual(result["total_area_m2"],sum(result["room_areas_m2"].values()))

    def test_merged_rooms_have_one_space_and_one_total_area(self):
        p=self.document(True);wall=next(w for w in p["walls"] if w["owner_room_ids"]==[0,1])
        result=self.move(p,wall,[20,0])
        self.assertEqual(len(result["enclosed_spaces"]),1)
        self.assertEqual(result["enclosed_spaces"][0]["room_ids"],[0,1])
        self.assertEqual([r["area_status"] for r in result["rooms"]],["merged","merged"])
        self.assertAlmostEqual(result["total_area_m2"],9.6*4.6)

    def test_one_open_room_does_not_discard_other_closed_rooms(self):
        p=self.document(True);result=self.move(p,self.top(p),[0,-.5])
        self.assertIsNone(result["room_areas_m2"]["0"])
        self.assertAlmostEqual(result["room_areas_m2"]["1"],4.7*4.6)
        self.assertAlmostEqual(result["total_area_m2"],4.7*4.6)

    def test_slanted_wall_area_survives_reopening(self):
        p=self.document();wall=self.top(p)
        result=apply_command(p,{"type":"move_wall_endpoint","id":wall["wall_id"],"endpoint":"start","delta_m":[0,.5]})
        expected=Polygon([[0,10],[100,0],[100,100],[0,100]])
        footprints=unary_union([LineString(w["reference_line"]).buffer(w["thickness_m"]/(2*.05),cap_style=2,join_style=2) for w in result["walls"]])
        area=expected.difference(footprints).area*.05**2
        self.assertAlmostEqual(result["room_areas_m2"]["0"],area)
        reopened=import_document(json.loads(json.dumps(result)))
        self.assertAlmostEqual(reopened["total_area_m2"],area)

    def test_sample_rooms_balconies_and_floor_mesh_match_measured_areas(self):
        p=import_document(json.loads((Path(__file__).resolve().parents[1]/"sample/plan.json").read_text(encoding="utf-8")))
        result=self.move(p,p["walls"][0],[0,0])
        self.assertEqual(len(result["enclosed_spaces"]),9)
        self.assertTrue(all(r.get("area_status")=="closed" for r in result["rooms"] if r["type"] not in {"door","front_door"}))
        for key,area in p["room_areas_m2"].items():self.assertAlmostEqual(result["room_areas_m2"][key],area)
        mesh_area=sum(Polygon(t).area*.05**2 for s in result["enclosed_spaces"] for t in s["floor_triangles"])
        # The sample has its own calibrated physical scale.
        mesh_area*= (result["pixel_to_meter"]/.05)**2
        self.assertAlmostEqual(mesh_area,result["total_area_m2"])

    def test_exact_endpoint_connections_restore_a_disconnected_room(self):
        p=self.document();wall=self.top(p);opened=self.move(p,wall,[0,-.503])
        first=apply_command(opened,{"type":"move_wall_endpoint","id":wall["wall_id"],"endpoint":"start","delta_m":[0,.503]})
        self.assertIsNone(first["room_areas_m2"]["0"])
        closed=apply_command(first,{"type":"move_wall_endpoint","id":wall["wall_id"],"endpoint":"end","delta_m":[0,.503]})
        self.assertAlmostEqual(closed["room_areas_m2"]["0"],4.6**2)

    def test_explicit_closed_room_edit_moves_boundary_walls_and_recalculates(self):
        p=self.document();p=self.move(p,self.top(p),[0,0])
        result=apply_command(p,{"type":"move_corner","origin":[0,0],"position":[-2,-2]})
        self.assertAlmostEqual(result["room_areas_m2"]["0"],4.7**2)
        self.assertNotEqual(result["walls"],p["walls"])

    def test_split_room_spaces_are_counted_once_each(self):
        p=self.document();p["editor"]["wall_mode"]="independent"
        p["walls"].append({"wall_id":"partition","reference_line":[[50,0],[50,100]],
            "owner_room_ids":[0],"host":"exterior_wall","height_m":3.3,"thickness_m":.2})
        result=import_document(p)
        self.assertEqual(result["rooms"][0]["area_status"],"split")
        self.assertEqual(len(result["enclosed_spaces"]),2)
        self.assertIsNone(result["room_areas_m2"]["0"])
        self.assertAlmostEqual(result["total_area_m2"],4.6**2-.2*4.6)

    def test_nested_enclosures_keep_holes_and_triangulate_without_double_counting(self):
        p=self.document();p["rooms"][0]["polygon"]=[[0,0],[200,0],[200,200],[0,200]]
        p["rooms"].append({"room_id":1,"name":"bedroom_0","type":"bedroom",
            "polygon":[[60,60],[140,60],[140,140],[60,140]]})
        p["walls"]=[];p["editor"]["wall_mode"]="independent"
        for index,room in enumerate(p["rooms"]):
            ring=room["polygon"]
            for i,a in enumerate(ring):p["walls"].append({"wall_id":f"w{index}_{i}",
                "reference_line":[a,ring[(i+1)%4]],"owner_room_ids":[0] if index==0 else [0,1],
                "host":"exterior_wall" if index==0 else "shared_wall","height_m":3.3,"thickness_m":.2})
        result=import_document(p)
        self.assertEqual(len(result["rooms"][0]["holes"]),1)
        # Joined wall faces fill the outer corners of the inner enclosure.
        expected=9.8**2-4.2**2+3.8**2
        self.assertAlmostEqual(result["total_area_m2"],expected)
        self.assertAlmostEqual(sum(Polygon(t).area*.05**2 for s in result["enclosed_spaces"] for t in s["floor_triangles"]),expected)
        self.assertAlmostEqual(import_document(result)["total_area_m2"],expected)


if __name__=="__main__":unittest.main()
