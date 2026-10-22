import assert from 'node:assert/strict';
import {test} from 'node:test';
import {selectionGeometry,previewOutline,handleCommand} from '../web_editor/static/edit_handles.js';
import {openingPlacement,doorLeaf} from '../web_editor/static/opening_placement.js';

const plan={pixel_to_meter:.05,walls:[
  {wall_id:'bottom',reference_line:[[0,0],[100,0]],height_m:3,host:'exterior_wall'},
  {wall_id:'left',reference_line:[[0,0],[0,100]],height_m:3,host:'exterior_wall'},
  {wall_id:'internal',reference_line:[[100,0],[100,100]],height_m:3,host:'shared_wall'}],
  openings:[{type:'door',wall_id:'bottom',center:[50,0],width_m:1,height_m:2.1,sill_m:0}]};
const geometry=()=>selectionGeometry(plan,{entity:'opening',id:0},'plan');
test('center preview turns onto a perpendicular wall and leaves size unchanged',()=>{
  const g=geometry(),delta=[-2.4,2.5,0],target=openingPlacement(g,delta),points=previewOutline(g,'center',delta);
  assert.equal(target.wallId,'left');assert.deepEqual(target.center,[0,2.5]);
  assert.equal(points[0][0],0);assert.equal(points[1][0],0);
  assert.equal(points[1][1]-points[0][1],1);
  assert.deepEqual(handleCommand(g,'center',delta,false).position_m,[.10000000000000009,2.5]);
});
test('empty space has no valid host and a near end is clamped inside the wall',()=>{
  assert.equal(openingPlacement(geometry(),[0,2.5,0]),null);
  const target=openingPlacement(geometry(),[-2.4,.1,0]);
  assert.ok(Math.abs(Math.hypot(...target.center)-.525)<1e-9);
});
test('window candidates exclude internal walls',()=>{
  const doc=structuredClone(plan);doc.openings[0].type='window';
  const g=selectionGeometry(doc,{entity:'opening',id:0});
  assert.equal(openingPlacement(g,[2.5,2.5,0]),null);
});
test('hinge and normal independently control the door leaf',()=>{
  const o={reference_line:[[0,0],[1,0]],normal:[0,1]};
  const start=doorLeaf(o),end=doorLeaf({...o,hinge_side:'end'}),flipped=doorLeaf({...o,normal:[0,-1]});
  assert.deepEqual(start.hinge,[0,0]);assert.deepEqual(end.hinge,[1,0]);
  assert.ok(Math.abs(start.end[1]-1)<1e-9);assert.ok(Math.abs(end.end[1]-1)<1e-9);
  assert.ok(Math.abs(flipped.end[1]+1)<1e-9);
});
