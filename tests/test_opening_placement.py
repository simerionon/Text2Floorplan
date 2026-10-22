"""Cross-wall opening edits retain dimensions and update the physical host."""
import copy
import unittest

from tests import test_edit_handles as fixtures
from web_editor.model_document import apply_command, import_document


class OpeningPlacementTests(unittest.TestCase):
    setUp = fixtures.HandleEditingTests.setUp
    def move(self, x, y):
        return apply_command(self.plan, {"type": "move_opening", "id": 0,
                                        "position_m": [x, y]})

    def test_move_around_corner_rotates_and_updates_host(self):
        before = copy.deepcopy(self.plan)
        changed = self.move(0.1, 2.5)
        opening = changed["openings"][0]
        self.assertNotEqual(opening["wall_id"], before["openings"][0]["wall_id"])
        self.assertAlmostEqual(opening["center"][0], 0)
        self.assertAlmostEqual(abs(opening["direction"][1]), 1)
        self.assertEqual(opening["width_m"], 1.2)
        self.assertEqual(opening["sill_m"], .9)
        self.assertEqual(self.plan, before)
        self.assertEqual(import_document(changed)["openings"], changed["openings"])

    def test_drop_in_empty_space_rejects_atomically(self):
        before = copy.deepcopy(self.plan)
        with self.assertRaisesRegex(ValueError, "wall"):
            self.move(2.5, 2.5)
        self.assertEqual(self.plan, before)

    def test_near_corner_keeps_opening_within_wall(self):
        opening = self.move(.1, .1)["openings"][0]
        wall = next(w for w in self.plan["walls"] if w["wall_id"] == opening["wall_id"])
        from shapely.geometry import LineString
        self.assertTrue(LineString(wall["reference_line"]).buffer(1e-6).covers(LineString(opening["reference_line"])))

    def test_window_cannot_move_to_internal_wall(self):
        with self.assertRaises(ValueError):
            self.move(5, 2.5)

    def test_front_door_cannot_move_to_internal_wall(self):
        self.plan["openings"][0].update(type="front_door", sill_m=0, height_m=2.1)
        with self.assertRaises(ValueError):
            self.move(5, 2.5)

    def test_low_host_is_not_a_valid_target(self):
        self.plan["editor"] = {"wall_mode": "independent"}
        wall = next(w for w in self.plan["walls"] if all(p[0] == 0 for p in w["reference_line"]))
        wall["height_m"] = 2
        with self.assertRaises(ValueError):
            self.move(0, 2.5)

    def test_collision_on_new_host_rejects_without_mutating_document(self):
        wall = next(w for w in self.plan["walls"] if all(p[0] == 0 for p in w["reference_line"]))
        other = copy.deepcopy(self.plan["openings"][0])
        other.update(wall_id=wall["wall_id"], center=[0, 50])
        self.plan["openings"].append(other)
        self.plan = import_document(self.plan)
        before = copy.deepcopy(self.plan)
        with self.assertRaisesRegex(ValueError, "too close"):
            self.move(0, 2.5)
        self.assertEqual(self.plan, before)

    def test_door_can_change_connected_rooms(self):
        self.plan["openings"][0].update(type="door", sill_m=0, height_m=2.1)
        opening = self.move(5, 2.5)["openings"][0]
        self.assertEqual({opening["owner_room_id"], opening["target_room_id"]}, {0, 1})
        self.assertEqual(opening["host"], "shared_wall")

    def test_swing_and_hinge_flip_persist_and_are_independent(self):
        self.plan["openings"][0].update(type="door", sill_m=0, height_m=2.1)
        for independent in [False, True]:
            plan = copy.deepcopy(self.plan)
            if independent:
                plan["editor"] = {"wall_mode": "independent"}
            original = import_document(plan)
            flipped = apply_command(original, {"type": "flip_opening", "id": 0, "axis": "swing"})
            self.assertEqual(flipped["openings"][0]["normal"], [-v for v in original["openings"][0]["normal"]])
            hinge = apply_command(flipped, {"type": "flip_opening", "id": 0, "axis": "hinge"})
            self.assertEqual(hinge["openings"][0]["hinge_side"], "end")
            self.assertEqual(import_document(hinge)["openings"], hinge["openings"])
            restored = apply_command(flipped, {"type": "flip_opening", "id": 0, "axis": "swing"})
            self.assertEqual(restored["openings"][0]["normal"], original["openings"][0]["normal"])


if __name__ == "__main__":
    unittest.main()
