"""Direct manipulation preserves dimensions, opposite edges and wall hosts."""
import copy
from pathlib import Path
import sys
import unittest

from shapely.geometry import LineString, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web_editor.model_document import apply_command, import_document


class HandleEditingTests(unittest.TestCase):
    def setUp(self):
        self.plan = import_document({
            "schema_version": "1.0", "coordinate_system": "raw_canvas_px",
            "pixel_to_meter": .05, "openings": [], "walls": [], "railings": [],
            "rooms": [
                {"room_id": 0, "name": "living_0", "type": "living", "polygon": [[0,0],[100,0],[100,100],[0,100]]},
                {"room_id": 1, "name": "bedroom_0", "type": "bedroom", "polygon": [[100,0],[200,0],[200,100],[100,100]]}]})
        self.wall = next(w for w in self.plan["walls"] if w["reference_line"] == [[0.,0.],[100.,0.]])
        self.plan["openings"] = [{"type":"window", "wall_id":self.wall["wall_id"],
            "host":"exterior_wall", "owner_room_id":0, "target_room_id":None,
            "center":[50,0], "width_m":1.2, "height_m":1.5, "sill_m":.9}]
        self.plan = import_document(self.plan)

    def drag(self, entity, handle, delta, id=0):
        return apply_command(self.plan, {"type":"drag_handle", "entity":entity,
            "id":id, "handle":handle, "delta_m":delta})

    def bounds(self, plan):
        o=plan["openings"][0]
        return o["center"][0]*.05-o["width_m"]/2, o["center"][0]*.05+o["width_m"]/2, o["sill_m"], o["sill_m"]+o["height_m"]

    def test_window_center_translation_preserves_size(self):
        result=self.drag("opening","center",[.2,0,.1])
        o=result["openings"][0]
        self.assertAlmostEqual(o["width_m"],1.2)
        self.assertAlmostEqual(o["height_m"],1.5)
        self.assertAlmostEqual(o["center"][0]*.05,2.7)
        self.assertAlmostEqual(o["sill_m"],1.)

    def test_each_edge_preserves_opposite_edge(self):
        before=self.bounds(self.plan)
        for handle,index,delta in [("left",0,[.2,0,0]),("right",1,[.2,0,0]),("bottom",2,[0,0,.1]),("top",3,[0,0,.1])]:
            with self.subTest(handle=handle):
                after=self.bounds(self.drag("opening",handle,delta))
                for i in range(4):
                    self.assertAlmostEqual(after[i]-before[i],(.2 if index<2 else .1) if i==index else 0)

    def test_opening_ignores_displacement_perpendicular_to_wall(self):
        result=self.drag("opening","center",[.2,2,0])
        self.assertAlmostEqual(result["openings"][0]["center"][1],0)

    def test_vertical_host_moves_along_vertical_axis(self):
        wall=next(w for w in self.plan["walls"] if all(p[0]==0 for p in w["reference_line"]))
        self.plan["openings"][0].update(wall_id=wall["wall_id"],center=[0,50])
        self.plan=import_document(self.plan)
        sign=1 if wall["reference_line"][1][1]>wall["reference_line"][0][1] else -1
        o=self.drag("opening","right",[0,.2*sign,0])["openings"][0]
        self.assertAlmostEqual(o["width_m"],1.4)
        self.assertAlmostEqual(o["center"][0],0)

    def test_crossed_edges_reject_atomically(self):
        before=copy.deepcopy(self.plan)
        with self.assertRaises(ValueError):self.drag("opening","left",[2,0,0])
        self.assertEqual(self.plan,before)

    def test_floor_and_wall_top_bound_vertical_drag(self):
        for handle,delta in [("bottom",[0,0,-2]),("top",[0,0,2]),("center",[0,0,-2])]:
            with self.subTest(handle=handle),self.assertRaises(ValueError):self.drag("opening",handle,delta)

    def test_door_uses_same_rectangle_handles(self):
        self.plan["openings"][0].update(type="door",sill_m=0,height_m=2.1)
        self.plan=import_document(self.plan)
        o=self.drag("opening","bottom",[0,0,.1])["openings"][0]
        self.assertAlmostEqual(o["sill_m"],.1)
        self.assertAlmostEqual(o["sill_m"]+o["height_m"],2.1)

    def test_wall_center_translates_both_endpoints_and_hosted_window(self):
        before=self.wall["reference_line"]
        result=self.drag("wall","center",[.2,-.1,0],self.wall["wall_id"])
        window=result["openings"][0]
        moved=next(w for w in result["walls"] if w["wall_id"]==window["wall_id"])
        for a,b in zip(before,moved["reference_line"]):
            self.assertAlmostEqual(b[0]-a[0],4)
            self.assertAlmostEqual(b[1]-a[1],-2)
        self.assertAlmostEqual(window["center"][0],54)
        self.assertAlmostEqual(window["center"][1],-2)
        self.assertAlmostEqual(window["width_m"],1.2)

    def test_wall_endpoint_keeps_opposite_endpoint_fixed(self):
        result=self.drag("wall","start",[-.2,.3,0],self.wall["wall_id"])
        wall=next(w for w in result["walls"] if w["wall_id"]==result["openings"][0]["wall_id"])
        self.assertAlmostEqual(wall["reference_line"][0][0],-4.)
        self.assertAlmostEqual(wall["reference_line"][0][1],6.)
        self.assertEqual(wall["reference_line"][1],[100.,0.])

    def test_room_center_preserves_shape_and_shared_boundary(self):
        result=self.drag("room","center",[.2,.1,0])
        for a,b in zip(self.plan["rooms"][0]["polygon"],result["rooms"][0]["polygon"]):
            self.assertEqual(b,[a[0]+4,a[1]+2])
        a,b=[Polygon(r["polygon"]) for r in result["rooms"]]
        self.assertAlmostEqual(a.intersection(b).area,0)
        self.assertAlmostEqual(a.boundary.intersection(b.boundary).length,100)

    def test_room_edge_moves_perpendicular_only(self):
        result=self.drag("room","edge:1",[.2,2,0])
        self.assertEqual(result["rooms"][0]["polygon"],[[0.,0.],[104.,0.],[104.,100.],[0.,100.]])
        self.assertEqual(result["rooms"][1]["polygon"][0],[104.,0.])

    def test_saved_handle_edit_can_be_reimported(self):
        result=self.drag("opening","center",[.2,0,.1])
        reopened=import_document(result)
        self.assertEqual(self.bounds(result),self.bounds(reopened))
        o=reopened["openings"][0]
        w=next(w for w in reopened["walls"] if w["wall_id"]==o["wall_id"])
        self.assertTrue(LineString(w["reference_line"]).buffer(1e-4).covers(LineString(o["reference_line"])))

    def test_railing_center_moves_open_edge_and_preserves_height(self):
        self.plan["rooms"].append({"room_id":2,"name":"balcony_0","type":"balcony",
            "polygon":[[200,0],[240,0],[240,100],[200,100]]})
        self.plan.update(walls=[],railings=[],openings=[])
        self.plan=import_document(self.plan)
        railing=next(r for r in self.plan["railings"] if all(p[0]==240 for p in r["reference_line"]))
        self.plan=apply_command(self.plan,{"type":"set_parameters","entity":"railing",
            "id":railing["railing_id"],"values":{"height_m":1.3}})
        result=self.drag("railing","center",[.1,0,0],railing["railing_id"])
        moved=next(r for r in result["railings"] if all(p[0]==242 for p in r["reference_line"]))
        self.assertEqual(moved["height_m"],1.3)
        self.assertEqual(len(result["railings"]),3)


if __name__ == "__main__":unittest.main()
