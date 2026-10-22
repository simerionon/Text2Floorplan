import assert from 'node:assert/strict';
import {test} from 'node:test';
import {selectionGeometry,handleCommand,previewOutline} from '../web_editor/static/edit_handles.js';
import {Scene} from '../web_editor/static/scene.js';

const plan={pixel_to_meter:.05,rooms:[{room_id:0,polygon:[[0,0],[100,0],[100,100],[0,100]],interior_point:[50,50]}],
  walls:[{wall_id:'w',reference_line:[[0,0],[100,0]],height_m:3.3}],railings:[],
  openings:[{wall_id:'w',center:[50,0],width_m:1.2,height_m:1.5,sill_m:.9}]};
const opening=view=>selectionGeometry(plan,{entity:'opening',id:0},view);
test('opening elevation exposes four edges and one center; plan exposes two ends and center',()=>{
  assert.deepEqual(opening('model').handles.map(h=>h.name),['left','right','bottom','top','center']);
  assert.deepEqual(opening('plan').handles.map(h=>h.name),['left','right','center']);
});
test('plan and model center controls preserve XY intent when changing hosts',()=>{
  assert.deepEqual(handleCommand(opening('plan'),'center',[.21,1,0]),handleCommand(opening('model'),'center',[.21,1,0]));
  assert.deepEqual(handleCommand(opening('plan'),'center',[.21,1,1]),{type:'move_opening',id:0,position_m:[2.7,1]});
  assert.deepEqual(handleCommand(opening('elevation'),'center',[.21,1,.1]).delta_m,[.2,0,.1]);
});
test('dragging left edge keeps both opposite corners unchanged in preview',()=>{
  const g=opening('model'),p=previewOutline(g,'left',[.2,0,0]);
  assert.deepEqual(p[1],g.outline[1]);assert.deepEqual(p[2],g.outline[2]);
  assert.ok(Math.abs(p[0][0]-g.outline[0][0]-.2)<1e-10);
});
test('center preview preserves the entire rectangle size',()=>{
  const g=opening('model'),delta=[.2,0,.1],p=previewOutline(g,'center',delta);
  assert.equal(p[1][0]-p[0][0],g.outline[1][0]-g.outline[0][0]);
  assert.ok(Math.abs(p[2][2]-p[0][2]-1.5)<1e-10);
});
test('walls expose distinct segment and free endpoint commands',()=>{
  const g=selectionGeometry(plan,{entity:'wall',id:'w'});
  assert.deepEqual(g.handles.map(h=>h.name),['start','end','center']);
  assert.equal(g.handles.find(h=>h.name==='center').edge,null,
    'the center hit target must not cover endpoint handles');
  const endpoint=handleCommand(g,'start',[.2,.3,.4]),segment=handleCommand(g,'center',[.2,.3,.4]);
  assert.equal(endpoint.type,'move_wall_endpoint');assert.equal(endpoint.endpoint,'start');
  assert.equal(segment.type,'translate_wall');assert.equal('endpoint' in segment,false);
  for(const command of [endpoint,segment])command.delta_m.forEach((v,i)=>assert.ok(Math.abs(v-[.2,.3][i])<1e-10));
  assert.deepEqual(handleCommand(g,'start',[.023,.037,0],false).delta_m,[.023,.037]);
});
test('rooms expose corners, edges and a center and constrain edge movement',()=>{
  const g=selectionGeometry(plan,{entity:'room',id:0});
  assert.equal(g.handles.length,9);
  assert.deepEqual(handleCommand(g,'edge:0',[1,2,0]).delta_m,[0,2,0]);
});
test('opening controls keep 100 mm increments on a rotated wall',()=>{
  const g=opening('model'),d=Math.sqrt(.5);g.direction=[d,d,0];
  const command=handleCommand(g,'right',[d*.1,d*.1,0]);
  assert.ok(Math.abs(Math.hypot(...command.delta_m)-.1)<1e-10);
});
test('3D screen projection and plane intersection round-trip on floor and facade',()=>{
  const rect={left:10,top:20,width:640,height:480};
  const scene={center:[5,7],distance:20,theta:-.9,phi:.85,canvas:{getBoundingClientRect:()=>rect}};
  Scene.prototype.camera.call(scene);
  const world=[6,9,1],screen=Scene.prototype.project.call(scene,world);
  for(const normal of [[0,0,1],[0,1,0]]){
    const point=Scene.prototype.pointOnPlane.call(scene,{clientX:screen[0]+rect.left,clientY:screen[1]+rect.top},world,normal);
    point.forEach((v,i)=>assert.ok(Math.abs(v-world[i])<1e-9));
  }
});
test('editing walls preserves the 3D camera frame until explicit Fit',()=>{
  const scene=Object.assign(Object.create(Scene.prototype),{gl:{bindBuffer(){},bufferData(){}},draw(){}});
  const document=structuredClone(plan);document.openings=[];document.walls[0].thickness_m=.2;
  scene.setPlan(document,null,true);
  const frame=scene.center.slice();
  document.walls[0].reference_line[1]=[500,0];
  scene.setPlan(document,null,false);
  assert.deepEqual(scene.center,frame);
  scene.fit();
  assert.notDeepEqual(scene.center,frame);
  assert.deepEqual(scene.center,scene.boundsCenter);
});
test('wall box faces point outward so corner joins share consistent lighting',()=>{
  const scene=Object.assign(Object.create(Scene.prototype),{gl:{bindBuffer(){},bufferData(){}},draw(){}});
  const document=structuredClone(plan);document.openings=[];document.walls[0].thickness_m=.4;
  scene.setPlan(document,null,true);
  const center=[2.5-scene.center[0],-scene.center[1],1.65];let count=0;
  for(let i=0;i<scene.vertices.length;i+=27){
    const v=scene.vertices.slice(i,i+27);
    if(Math.abs(v[6]-241/255)>1e-10)continue;
    const centroid=[0,1,2].map(k=>(v[k]+v[k+9]+v[k+18])/3-center[k]);
    assert.ok(centroid.reduce((sum,x,k)=>sum+x*v[k+3],0)>0);
    count++;
  }
  assert.equal(count,12);
});
