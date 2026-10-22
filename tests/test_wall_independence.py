"""A wall segment and its endpoints must not move neighboring segments."""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web_editor.model_document import apply_command, import_document


class IndependentWallTests(unittest.TestCase):
    def setUp(self):
        self.plan=import_document({"schema_version":"1.0","coordinate_system":"raw_canvas_px",
            "pixel_to_meter":.05,"walls":[],"railings":[],"openings":[],
            "rooms":[{"room_id":0,"name":"living_0","type":"living",
                      "polygon":[[0,0],[100,0],[100,100],[0,100]]}]})
        self.wall=next(w for w in self.plan["walls"] if w["reference_line"]==[[0.,0.],[100.,0.]])

    def drag(self,handle,delta):
        return apply_command(self.plan,{"type":"drag_handle","entity":"wall",
            "id":self.wall["wall_id"],"handle":handle,"delta_m":delta})

    def assert_others_unchanged(self,result):
        self.assertEqual([r["room_id"] for r in result["rooms"]],[r["room_id"] for r in self.plan["rooms"]])
        self.assertEqual([w for w in result["walls"] if w["wall_id"]!=self.wall["wall_id"]],
                         [w for w in self.plan["walls"] if w["wall_id"]!=self.wall["wall_id"]])

    def test_segment_translation_changes_only_the_selected_wall(self):
        result=self.drag("center",[.2,.3,0])
        wall=next(w for w in result["walls"] if w["wall_id"]==self.wall["wall_id"])
        for actual,expected in zip(wall["reference_line"],[[4.,6.],[104.,6.]]):
            for a,b in zip(actual,expected):self.assertAlmostEqual(a,b)
        self.assert_others_unchanged(result)

    def test_endpoint_moves_in_xy_and_keeps_the_other_endpoint_fixed(self):
        result=self.drag("start",[.2,.3,0])
        wall=next(w for w in result["walls"] if w["wall_id"]==self.wall["wall_id"])
        for actual,expected in zip(wall["reference_line"],[[4.,6.],[100.,0.]]):
            for a,b in zip(actual,expected):self.assertAlmostEqual(a,b)
        self.assert_others_unchanged(result)

    def add_window(self):
        self.plan["openings"]=[{"type":"window","wall_id":self.wall["wall_id"],
            "host":"exterior_wall","owner_room_id":0,"target_room_id":None,
            "center":[50,0],"width_m":1.2,"height_m":1.5,"sill_m":.9}]
        self.plan=import_document(self.plan)

    def test_explicit_commands_are_separate_and_match_their_handles(self):
        for handle,kind in [("center","translate_wall"),("end","move_wall_endpoint")]:
            command={"type":kind,"id":self.wall["wall_id"],"delta_m":[.2,.3]}
            if handle!="center":command["endpoint"]=handle
            self.assertEqual(apply_command(self.plan,command),self.drag(handle,[.2,.3,0]))

    def test_translation_carries_hosted_window_without_resizing(self):
        self.add_window()
        o=self.drag("center",[.2,.3,0])["openings"][0]
        self.assertAlmostEqual(o["center"][0],54)
        self.assertAlmostEqual(o["center"][1],6)
        self.assertAlmostEqual(o["width_m"],1.2)
        self.assertAlmostEqual(o["height_m"],1.5)
        self.assertAlmostEqual(o["sill_m"],.9)

    def test_endpoint_resize_preserves_window_station_from_fixed_end(self):
        self.add_window()
        o=self.drag("start",[1.,0,0])["openings"][0]
        self.assertAlmostEqual(o["center"][0],50)
        self.assertAlmostEqual(o["center"][1],0)

    def test_rotating_endpoint_keeps_hosted_opening_on_the_wall(self):
        self.add_window()
        result=self.drag("end",[0,1.,0])
        w=next(w for w in result["walls"] if w["wall_id"]==self.wall["wall_id"])
        o=result["openings"][0]
        a,b=w["reference_line"]
        self.assertAlmostEqual(math.dist(a,o["center"]),50)
        self.assertAlmostEqual((b[0]-a[0])*(o["center"][1]-a[1])-(b[1]-a[1])*(o["center"][0]-a[0]),0)
        self.assert_others_unchanged(result)

    def test_reopen_and_parameter_edits_do_not_rebuild_free_walls(self):
        moved=self.drag("start",[.2,.3,0])
        reopened=import_document(json.loads(json.dumps(moved)))
        self.assertEqual(reopened["walls"],moved["walls"])
        changed=apply_command(reopened,{"type":"set_parameters","entity":"wall",
            "id":self.wall["wall_id"],"values":{"height_m":3.6}})
        w=next(w for w in changed["walls"] if w["wall_id"]==self.wall["wall_id"])
        self.assertEqual(w["reference_line"],moved["walls"][0]["reference_line"])
        self.assertEqual(w["height_m"],3.6)
        self.assertEqual(changed["editor"]["room_boundaries"],"walls")

    def test_unclosed_room_cannot_silently_pull_free_wall_back(self):
        moved=self.drag("center",[.2,.3,0])
        with self.assertRaises(ValueError):
            apply_command(moved,{"type":"move_corner","origin":[0,0],"position":[-4,-2]})

    def test_numeric_segment_move_does_not_move_neighbors(self):
        result=apply_command(self.plan,{"type":"move_wall","id":self.wall["wall_id"],"position_m":.3})
        self.assert_others_unchanged(result)
        w=next(w for w in result["walls"] if w["wall_id"]==self.wall["wall_id"])
        self.assertAlmostEqual(w["reference_line"][0][1],6)

    def test_wall_cannot_collapse_or_cut_off_its_hosted_window(self):
        self.add_window()
        before=copy.deepcopy(self.plan)
        for delta in [[5,0,0],[3,0,0]]:
            with self.subTest(delta=delta),self.assertRaises(ValueError):self.drag("start",delta)
        self.assertEqual(self.plan,before)

    def test_every_sample_wall_translates_without_moving_another_wall(self):
        original=import_document(json.loads((Path(__file__).resolve().parents[1]/"sample"/"plan.json").read_text(encoding="utf-8")))
        for wall in original["walls"]:
            with self.subTest(wall=wall["wall_id"]):
                result=apply_command(original,{"type":"translate_wall","id":wall["wall_id"],"delta_m":[.2,.2]})
                self.assertEqual([r["room_id"] for r in result["rooms"]],[r["room_id"] for r in original["rooms"]])
                self.assertEqual([w for w in result["walls"] if w["wall_id"]!=wall["wall_id"]],
                                 [w for w in original["walls"] if w["wall_id"]!=wall["wall_id"]])


if __name__=="__main__":unittest.main()
