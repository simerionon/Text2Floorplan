"""Exercise editable documents through the same interface used by the browser."""
import copy
import json
from pathlib import Path
import sys
import unittest

from shapely.geometry import LineString, Polygon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from web_editor.model_document import apply_command, import_document


class EditableDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads((ROOT / "sample" / "plan.json").read_text(encoding="utf-8"))

    def setUp(self):
        self.plan = import_document(self.original)

    def test_import_preserves_sample_area_and_unique_hosts(self):
        self.assertAlmostEqual(self.plan["total_area_m2"], self.original["total_area_m2"])
        self.assertEqual(len(self.plan["walls"]), 28)
        self.assertEqual(len({w["wall_id"] for w in self.plan["walls"]}), 28)
        self.assertEqual(self.original["pixel_to_meter"], self.plan["pixel_to_meter"])

    def test_wall_height_changes_keep_openings_hosted(self):
        wall = self.plan["walls"][0]
        changed = apply_command(self.plan, {"type": "set_parameters", "entity": "wall",
            "id": wall["wall_id"], "values": {"height_m": 3.6}})
        self.assertEqual(changed["walls"][0]["height_m"], 3.6)
        self.assertEqual(self.plan["walls"][0]["height_m"], 3.3)
        self.assertTrue(all(o["wall_id"] in {w["wall_id"] for w in changed["walls"]}
                            for o in changed["openings"]))

    def test_window_sill_and_height_round_trip_without_resampling(self):
        index = next(i for i, o in enumerate(self.plan["openings"]) if o["type"] == "window")
        changed = apply_command(self.plan, {"type": "set_parameters", "entity": "opening",
            "id": index, "values": {"sill_m": 1.1, "height_m": 1.5}})
        reopened = import_document(json.loads(json.dumps(changed)))
        self.assertEqual(reopened["openings"][index]["sill_m"], 1.1)
        self.assertEqual(reopened["openings"][index]["height_m"], 1.5)

    def test_impossible_opening_rejects_edit_atomically(self):
        before = copy.deepcopy(self.plan)
        with self.assertRaises(ValueError):
            apply_command(self.plan, {"type": "set_parameters", "entity": "opening",
                "id": 0, "values": {"width_m": 9}})
        self.assertEqual(self.plan, before)

    def test_low_wall_cannot_cut_existing_window(self):
        opening = next(o for o in self.plan["openings"] if o["type"] == "window")
        with self.assertRaises(ValueError):
            apply_command(self.plan, {"type": "set_parameters", "entity": "wall",
                "id": opening["wall_id"], "values": {"height_m": 1.5}})

    def test_thickness_changes_recalculate_clear_area(self):
        changed = apply_command(self.plan, {"type": "set_parameters", "entity": "wall",
            "id": self.plan["walls"][0]["wall_id"], "values": {"thickness_m": 0.45}})
        self.assertLess(changed["total_area_m2"], self.plan["total_area_m2"])

    def test_corner_move_keeps_room_valid_and_openings_attached(self):
        room = next(r for r in self.plan["rooms"] if r["room_id"] == 2)
        origin = min(room["polygon"], key=lambda p: p[0] - p[1])
        changed = apply_command(self.plan, {"type": "move_corner", "origin": origin,
            "position": [origin[0] - 2, origin[1]]})
        self.assertGreater(changed["total_area_m2"], self.plan["total_area_m2"])
        for room in changed["rooms"]:
            self.assertTrue(Polygon(room["polygon"]).is_valid)
        walls = {w["wall_id"]: w for w in changed["walls"]}
        for opening in changed["openings"]:
            self.assertTrue(LineString(walls[opening["wall_id"]]["reference_line"]).buffer(1e-4)
                            .covers(LineString(opening["reference_line"])))

    def test_railing_edit_is_retained_when_input_order_changes(self):
        self.plan["railings"].reverse()
        target = self.plan["railings"][0]["railing_id"]
        changed = apply_command(self.plan, {"type": "set_parameters", "entity": "railing",
            "id": target, "values": {"height_m": 1.25}})
        item = next(r for r in changed["railings"] if r["railing_id"] == target)
        self.assertEqual(item["height_m"], 1.25)

    def test_nan_parameter_rejected(self):
        with self.assertRaises(ValueError):
            apply_command(self.plan, {"type": "set_parameters", "entity": "wall",
                "id": self.plan["walls"][0]["wall_id"], "values": {"height_m": float("nan")}})

    def test_shared_wall_move_updates_both_rooms_without_a_gap(self):
        document = {"schema_version": "1.0", "coordinate_system": "raw_canvas_px",
            "pixel_to_meter": 0.05, "openings": [], "walls": [], "railings": [],
            "rooms": [
                {"room_id": 0, "name": "living_0", "type": "living",
                 "polygon": [[0, 0], [100, 0], [100, 100], [0, 100]]},
                {"room_id": 1, "name": "bedroom_0", "type": "bedroom",
                 "polygon": [[100, 0], [200, 0], [200, 100], [100, 100]]}]}
        original = import_document(document)
        changed = apply_command(original, {"type": "move_corner", "origin": [100, 0],
            "position": [110, 0]})
        living, bedroom = [Polygon(r["polygon"]) for r in changed["rooms"]]
        self.assertAlmostEqual(living.intersection(bedroom).area, 0)
        self.assertAlmostEqual(living.boundary.intersection(bedroom.boundary).length, 100)
        self.assertEqual(changed["rooms"][0]["polygon"][1], [110, 0])
        self.assertEqual(changed["rooms"][1]["polygon"][0], [110, 0])


if __name__ == "__main__":
    unittest.main()
