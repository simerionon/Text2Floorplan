import assert from 'node:assert/strict';
import {test} from 'node:test';
import {snapMovement} from '../web_editor/static/node_snap.js';
import {handleCommand} from '../web_editor/static/edit_handles.js';

const project=p=>[p[0]*20,p[1]*20];
function fixture(target=[[100,0],[100,100]]){
  const plan={pixel_to_meter:.05,railings:[],walls:[
    {wall_id:'moving',reference_line:[[0,20],[100,20]]},
    {wall_id:'fixed',reference_line:target}]};
  const geometry={entity:'wall',id:'moving',outline:[[0,1,0],[5,1,0]]};
  return {plan,geometry};
}
test('endpoint snaps exactly to an existing node, overriding the movement grid',()=>{
  const {plan,geometry}=fixture([[101.234,0],[101.234,100]]);
  const result=snapMovement(plan,geometry,'end',[.05,-.9,0],project);
  assert.equal(result.snap.kind,'node');
  assert.ok(Math.abs(result.delta[0]-.0617)<1e-10);
  const command=handleCommand(geometry,'end',result.delta,false);
  assert.ok(Math.abs(command.delta_m[0]-.0617)<1e-10);
  assert.equal(command.delta_m[1],-1);
});
test('segment translation snaps one endpoint without changing the segment length',()=>{
  const {plan,geometry}=fixture();
  const result=snapMovement(plan,geometry,'center',[.1,-.8,0],project);
  assert.deepEqual(result.delta,[0,-1,0]);
  const translated=geometry.outline.map(p=>p.map((v,i)=>v+result.delta[i]));
  assert.equal(translated[1][0]-translated[0][0],5);
});
test('disabled snapping preserves the raw displacement',()=>{
  const {plan,geometry}=fixture(),delta=[.05,-.9,0];
  assert.deepEqual(snapMovement(plan,geometry,'end',delta,project,{enabled:false}),{delta,snap:null});
});
test('snap radius follows screen distance at different zoom levels',()=>{
  const {plan,geometry}=fixture([[100,0],[110,0]]);
  assert.equal(snapMovement(plan,geometry,'end',[0,-.8,0],project).snap.kind,'node');
  assert.equal(snapMovement(plan,geometry,'end',[0,-.8,0],p=>[p[0]*200,p[1]*200]).snap,null);
});
test('a node can connect to the middle of another wall at a T junction',()=>{
  const {plan,geometry}=fixture();geometry.outline=[[0,2.5,0],[4.8,2.5,0]];
  const result=snapMovement(plan,geometry,'end',[.3,0,0],project);
  assert.equal(result.snap.kind,'wall');assert.deepEqual(result.snap.point,[5,2.5,0]);
});
test('crossing wall intersections are snap nodes',()=>{
  const {plan,geometry}=fixture();
  plan.walls.push({wall_id:'crossing',reference_line:[[80,50],[120,50]]});
  geometry.outline=[[0,2,0],[4.8,2,0]];
  const result=snapMovement(plan,geometry,'end',[.1,.4,0],project);
  assert.equal(result.snap.kind,'node');assert.deepEqual(result.snap.point,[5,2.5,0]);
});
test('the moving wall does not snap to its own unshared endpoints',()=>{
  const {plan,geometry}=fixture();plan.walls.pop();
  assert.equal(snapMovement(plan,geometry,'start',[.1,.1,0],project).snap,null);
});
test('3D snapping preserves the moving wall plane height',()=>{
  const {plan,geometry}=fixture();geometry.outline=geometry.outline.map(p=>[p[0],p[1],3.34]);
  const result=snapMovement(plan,geometry,'end',[0,-.9,0],project);
  assert.equal(result.snap.point[2],3.34);assert.equal(result.delta[2],0);
});
