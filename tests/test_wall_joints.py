"""Meeting wall faces form full corners without coupling editable segments."""
import sys
import unittest
import json
from pathlib import Path

from shapely.geometry import Point, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plan_quality import build_wall_footprints, load_physical_scale
from web_editor.model_document import import_document, apply_command


def wall(name, a, b, thickness=.4):
    return dict(wall_id=name, reference_line=[a, b], thickness_m=thickness, height_m=3.3)


class WallJointTests(unittest.TestCase):
    def test_published_sample_uses_current_large_scale_and_matching_areas(self):
        root = Path(__file__).resolve().parents[1]
        p = json.loads((root/'sample/plan.json').read_text(encoding='utf-8'))
        metadata = json.loads((root/'sample/model-metadata.json').read_text(encoding='utf-8'))
        self.assertEqual(p['pixel_to_meter'], load_physical_scale('large')['pixel_to_meter'])
        reopened = import_document(p)
        self.assertAlmostEqual(p['total_area_m2'], reopened['total_area_m2'])
        self.assertAlmostEqual(metadata['total_area_m2'], p['total_area_m2'])
        self.assertTrue(all(r['area_status']=='closed' for r in reopened['rooms']
                            if r['type'] not in {'door','front_door'}))
    def test_outer_right_angle_has_no_missing_quarter_square(self):
        walls = [wall('a', [0, 0], [5, 0]), wall('b', [0, 0], [0, 5])]
        shape, joints = build_wall_footprints(walls, 1)
        self.assertTrue(shape.covers(Point(-.1, -.1)))
        self.assertAlmostEqual(shape.area, 4)
        self.assertEqual(len(joints), 1)
        self.assertIn([-.2, -.2], joints[0]['polygon'])
        self.assertEqual(walls[0]['reference_line'], [[0, 0], [5, 0]])

    def test_different_thickness_faces_meet_at_their_exact_intersection(self):
        shape, joints = build_wall_footprints([
            wall('a', [0, 0], [5, 0], .4), wall('b', [0, 0], [0, 5], .2)], 1)
        self.assertIn([-.1, -.2], joints[0]['polygon'])
        self.assertAlmostEqual(shape.area, 3)

    def test_open_end_and_visible_gap_are_not_extended(self):
        shape, joints = build_wall_footprints([
            wall('a', [0, 0], [5, 0]), wall('b', [0, .05], [0, 5])], 1)
        self.assertEqual(joints, [])
        self.assertFalse(shape.covers(Point(-.1, -.1)))

    def test_t_junction_keeps_overlapping_faces_without_extra_corner(self):
        _, joints = build_wall_footprints([wall('a', [-5, 0], [0, 0]),
            wall('b', [0, 0], [5, 0]), wall('c', [0, 0], [0, 5])], 1)
        self.assertEqual(joints, [])

    def test_mixed_t_keeps_exterior_corner_when_an_internal_wall_meets_it(self):
        a=wall('right', [0,0], [5,0]);a['host']='exterior_wall'
        b=wall('up', [0,0], [0,-5]);b['host']='exterior_wall'
        c=wall('inside', [-5,0], [0,0], .2);c['host']='shared_wall'
        shape,joints=build_wall_footprints([a,b,c],1)
        self.assertTrue(shape.covers(Point(-.15,.15)),
                        'the inner branch must not disable the exterior mitre')
        self.assertFalse(shape.covers(Point(-.25,.15)))
        self.assertTrue(all(set(j['wall_ids'])=={'right','up'} for j in joints))
        self.assertAlmostEqual(sum(Polygon(j['polygon']).area for j in joints),.02)

    def test_straight_exterior_t_does_not_get_a_corner_patch(self):
        a=wall('left', [-5,0], [0,0]);a['host']='exterior_wall'
        b=wall('right', [0,0], [5,0]);b['host']='exterior_wall'
        c=wall('inside', [0,0], [0,5], .2);c['host']='shared_wall'
        _,joints=build_wall_footprints([a,b,c],1)
        self.assertEqual(joints,[])

    def test_moved_wall_rejoins_external_corner_without_a_bevel(self):
        room=dict(room_id=0,name='living',type='living',polygon=[[0,0],[100,0],[100,100],[0,100]])
        p=import_document(dict(schema_version='1.0',coordinate_system='raw_canvas_px',
            pixel_to_meter=.05,rooms=[room],walls=[],openings=[],railings=[]))
        top=next(w for w in p['walls'] if w['reference_line']==[[0.,0.],[100.,0.]])
        branch=wall('inside',[-100,0],[0,0],.2)
        branch.update(host='shared_wall',owner_room_ids=[0])
        p['walls'].append(branch);p['editor']['wall_mode']='independent'
        p=import_document(p)
        moved=apply_command(p,dict(type='translate_wall',id=top['wall_id'],delta_m=[0,-.5]))
        for endpoint in ('start','end'):
            moved=apply_command(moved,dict(type='move_wall_endpoint',id=top['wall_id'],
                                         endpoint=endpoint,delta_m=[0,.5]))
        body,_=build_wall_footprints(moved['walls'],.05)
        self.assertTrue(body.covers(Point(-.15/.05,-.15/.05)))
        self.assertEqual(moved['rooms'][0]['area_status'],'closed')
        self.assertEqual(moved['walls'],p['walls'])

    def test_moving_one_wall_removes_the_join_without_moving_neighbors(self):
        room = dict(room_id=0, name='living', type='living', polygon=[[0,0],[100,0],[100,100],[0,100]])
        p = import_document(dict(schema_version='1.0', coordinate_system='raw_canvas_px',
            pixel_to_meter=.05, rooms=[room], walls=[], openings=[], railings=[]))
        first = p['walls'][0]
        changed = apply_command(p, dict(type='translate_wall', id=first['wall_id'], delta_m=[0,-1]))
        self.assertLess(len(changed['wall_joints']), len(p['wall_joints']))
        for before, after in zip(p['walls'], changed['walls']):
            if before['wall_id'] != first['wall_id']:
                self.assertEqual(before['reference_line'], after['reference_line'])

    def test_joined_inner_room_removes_corner_slivers_from_surrounding_area(self):
        ring = [[2,2],[4,2],[4,4],[2,4]]
        shape, _ = build_wall_footprints([wall(str(i), a, ring[(i+1)%4], .2)
                                        for i, a in enumerate(ring)], 1)
        outer = Polygon([[0,0],[6,0],[6,6],[0,6]])
        inner = Polygon(ring)
        self.assertAlmostEqual(outer.difference(inner.union(shape)).area, 36-2.2**2)


if __name__ == '__main__':
    unittest.main()
