// Shared world-space controls for plan, elevation and perspective views.
import {openingPlacement} from './opening_placement.js';
const add = (a,b) => a.map((v,i) => v+b[i]);
const mid = (a,b) => a.map((v,i) => (v+b[i])/2);
export function selectionGeometry(plan, selection, view = 'plan') {
  if (!plan || !selection) return null;
  const s = plan.pixel_to_meter, {entity,id} = selection;
  const world = (p,z=0) => [p[0]*s,p[1]*s,z];
  const handle = (name,position,edge=null) => ({name,position,edge});
  if (entity === 'opening') {
    const o = plan.openings[id]; if (!o) return null;
    const wall = plan.walls.find(w => w.wall_id===o.wall_id);
    const [a,b] = wall.reference_line;
    const length = Math.hypot(b[0]-a[0],b[1]-a[1]);
    const d = [(b[0]-a[0])/length,(b[1]-a[1])/length,0];
    const c = world(o.center), z0=o.sill_m, z1=z0+o.height_m;
    const placement={rehost:view!=='elevation',hostId:o.wall_id,width:o.width_m,top:z1,
      hostWalls:plan.walls.filter(w=>!['window','front_door'].includes(o.type)||w.host==='exterior_wall')
        .map(w=>({id:w.wall_id,line:w.reference_line.map(p=>p.map(v=>v*s)),height:w.height_m}))};
    const at = (x,z) => [c[0]+d[0]*x,c[1]+d[1]*x,z];
    const p = [at(-o.width_m/2,z0),at(o.width_m/2,z0),at(o.width_m/2,z1),at(-o.width_m/2,z1)];
    if (view === 'plan') {
      const ends=[at(-o.width_m/2,0),at(o.width_m/2,0)];
      return {entity,id,...placement,outline:ends,closed:false,normal:[0,0,1],origin:c,direction:d,vertical:false,
        handles:[handle('left',ends[0]),handle('right',ends[1]),handle('center',c)]};
    }
    return {entity,id,...placement,outline:p,closed:true,normal:[-d[1],d[0],0],origin:c,direction:d,vertical:true,
      handles:[handle('left',mid(p[0],p[3]),[p[0],p[3]]),handle('right',mid(p[1],p[2]),[p[1],p[2]]),
        handle('bottom',mid(p[0],p[1]),[p[0],p[1]]),handle('top',mid(p[3],p[2]),[p[3],p[2]]),
        handle('center',mid(p[0],p[2]))]};
  }
  if (entity === 'wall' || entity === 'railing') {
    const item = (entity==='wall'?plan.walls:plan.railings).find(w=>w[entity+'_id']===id);
    if (!item) return null;
    const p=item.reference_line.map(p=>world(p,view==='plan'?0:item.height_m+.04));
    return {entity,id,outline:p,closed:false,normal:[0,0,1],origin:p[0],
      handles:[handle('start',p[0]),handle('end',p[1]),handle('center',mid(...p))]};
  }
  if (entity === 'room') {
    const room = plan.rooms.find(r=>r.room_id===id); if (!room) return null;
    if(room.area_status&&room.area_status!=='closed'||room.holes?.length)return null;
    const p=room.polygon.map(p=>world(p,.04));
    return {entity,id,outline:p,closed:true,normal:[0,0,1],origin:p[0],handles:[
      ...p.map((v,i)=>handle('corner:'+i,v)),
      ...p.map((v,i)=>handle('edge:'+i,mid(v,p[(i+1)%p.length]),[v,p[(i+1)%p.length]])),
      handle('center',world(room.interior_point||room.polygon[0],.04))]};
  }
  return null;
}

export function handleCommand(geometry, name, delta, snap=true) {
  if(geometry.entity==='opening'&&name==='center'&&geometry.rehost){
    const position=geometry.origin.slice(0,2).map((v,i)=>v+(snap?Math.round(delta[i]/.1)*.1:delta[i]));
    return {type:'move_opening',id:geometry.id,position_m:position};
  }
  delta=delta.map(v=>snap&&geometry.entity!=='opening'?Math.round(v/.1)*.1:v);
  if(geometry.entity==='wall')return {type:name==='center'?'translate_wall':'move_wall_endpoint',id:geometry.id,
    ...(name==='center'?{}:{endpoint:name}),delta_m:delta.slice(0,2)};
  if (geometry.entity === 'opening') {
    let along=delta[0]*geometry.direction[0]+delta[1]*geometry.direction[1];
    if(snap)along=Math.round(along/.1)*.1;
    const vertical=geometry.vertical?(snap?Math.round(delta[2]/.1)*.1:delta[2]):0;
    delta=[geometry.direction[0]*along,geometry.direction[1]*along,vertical];
    if (name==='top'||name==='bottom') delta=[0,0,delta[2]];
    else if (name==='left'||name==='right') delta[2]=0;
  } else {
    delta[2]=0;
    if(geometry.entity==='room'&&name.startsWith('edge:')) {
      const i=Number(name.split(':')[1]),a=geometry.outline[i],b=geometry.outline[(i+1)%geometry.outline.length];
      const length=Math.hypot(b[0]-a[0],b[1]-a[1]),n=[-(b[1]-a[1])/length,(b[0]-a[0])/length],amount=delta[0]*n[0]+delta[1]*n[1];
      delta=[n[0]*amount||0,n[1]*amount||0,0];
    }
  }
  return {type:'drag_handle',entity:geometry.entity,id:geometry.id,handle:name,delta_m:delta};
}

export function previewOutline(geometry, name, delta) {
  const p=geometry.outline.map(p=>p.slice());
  if(geometry.entity==='opening'&&name==='center'&&geometry.rehost){
    const target=openingPlacement(geometry,delta);
    if(!target)return p.map(p=>add(p,[delta[0],delta[1],0]));
    return p.map(point=>{const along=(point[0]-geometry.origin[0])*geometry.direction[0]+(point[1]-geometry.origin[1])*geometry.direction[1];
      return [target.center[0]+target.direction[0]*along,target.center[1]+target.direction[1]*along,point[2]]});
  }
  if(name==='center') return p.map(p=>add(p,delta));
  if(geometry.entity==='opening') {
    const d=geometry.direction || (()=>{const [a,b]=p,n=Math.hypot(b[0]-a[0],b[1]-a[1]);return [(b[0]-a[0])/n,(b[1]-a[1])/n,0]})();
    const along=delta[0]*d[0]+delta[1]*d[1];
    const offset=name==='left'||name==='right'?d.map(v=>v*along):[0,0,delta[2]];
    const ids=p.length===2?(name==='left'?[0]:[1]):({left:[0,3],right:[1,2],bottom:[0,1],top:[2,3]})[name];
    for(const i of ids) p[i]=add(p[i],offset);
  } else if(name==='start'||name==='end') p[name==='start'?0:1]=add(p[name==='start'?0:1],delta);
  else if(name.startsWith('edge:')) {
    const i=Number(name.split(':')[1]),j=(i+1)%p.length;
    for(const index of [i,j])p[index]=add(p[index],delta);
  } else if(name.startsWith('corner:')) {
    const i=Number(name.split(':')[1]);p[i]=add(p[i],delta);
  }
  return p;
}

const ns='http://www.w3.org/2000/svg';
const node=(tag,attrs={})=>{const el=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))el.setAttribute(k,v);return el;};
export class HandleLayer {
  constructor({commit,enabled,label,snapLabel=kind=>kind.toUpperCase()}) {this.commit=commit;this.enabled=enabled;this.label=label;this.snapLabel=snapLabel;this.dragging=false;}
  render(svg,geometry,{project,unproject,scale=1,snap=delta=>({delta,snap:null})}) {
    if(this.dragging)return;
    if(this.svg!==svg){
      svg.addEventListener('wheel',e=>{if(this.dragging){e.preventDefault();e.stopImmediatePropagation();}},{capture:true,passive:false});
      this.svg=svg;
    }
    this.group?.remove();this.group=null;
    if(!geometry)return;
    const group=node('g',{'class':'edit-handles'});svg.append(group);this.group=group;
    const points=geometry.outline.map(project);
    if(points.some(p=>!p))return;
    const outline=node(geometry.closed?'polygon':'polyline',{points:points.map(p=>p.join(',')).join(' '),'class':'handle-outline','vector-effect':'non-scaling-stroke'});group.append(outline);
    const radius=5*scale;
    const marker=node('g',{'class':'snap-indicator',visibility:'hidden'}),ring=node('circle',{r:8*scale}),caption=node('text',{'font-size':10*scale});marker.append(ring,caption);group.append(marker);
    for(const descriptor of geometry.handles) {
      const xy=project(descriptor.position);if(!xy)continue;
      const g=node('g',{'class':'edit-handle','role':'button',tabindex:0,'aria-label':this.label(descriptor.name),'data-handle':descriptor.name});
      if(descriptor.edge){const [a,b]=descriptor.edge.map(project);if(a&&b)g.append(node('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'transparent','stroke-width':12*scale}));}
      g.append(node(descriptor.name==='center'?'rect':'circle',descriptor.name==='center'?
        {x:xy[0]-radius,y:xy[1]-radius,width:radius*2,height:radius*2,rx:2*scale,'class':'center-handle'}:
        {cx:xy[0],cy:xy[1],r:radius,'class':descriptor.name.startsWith('edge:')?'edge-handle':'point-handle'}));
      const title=node('title');title.textContent=this.label(descriptor.name);g.append(title);group.append(g);
      let gesture;
      g.addEventListener('click',e=>e.stopPropagation());
      g.addEventListener('pointerdown',e=>{
        if(e.button!==0||!this.enabled())return;
        const origin=unproject(e,geometry,descriptor);if(!origin)return;
        e.preventDefault();e.stopPropagation();g.setPointerCapture(e.pointerId);
        gesture={origin,pointerId:e.pointerId,delta:[0,0,0]};this.dragging=true;g.classList.add('dragging');
      });
      g.addEventListener('pointermove',e=>{
        if(!gesture||gesture.pointerId!==e.pointerId)return;
        const point=unproject(e,geometry,descriptor);if(!point)return;
        const raw=point.map((v,i)=>v-gesture.origin[i]),result=snap(raw,descriptor.name,!e.altKey);
        const command=handleCommand(geometry,descriptor.name,result.delta,result.snap?false:!e.altKey);
        gesture.delta=command.type==='move_opening'?[...command.position_m.map((v,i)=>v-geometry.origin[i]),0]:command.delta_m;
        if(gesture.delta.length===2)gesture.delta.push(0);
        if(command.type==='move_opening'){
          const target=openingPlacement(geometry,gesture.delta);
          if(target)result.snap={point:[...target.center,descriptor.position[2]],kind:'wall'};
        }
        marker.setAttribute('visibility',result.snap?'visible':'hidden');
        if(result.snap){const xy=project(result.snap.point);ring.setAttribute('cx',xy[0]);ring.setAttribute('cy',xy[1]);caption.setAttribute('x',xy[0]+12*scale);caption.setAttribute('y',xy[1]-12*scale);caption.textContent=this.snapLabel(result.snap.kind);marker.dataset.snapKind=result.snap.kind;marker.dataset.snapTarget=result.snap.point.join(',');}
        const preview=previewOutline(geometry,descriptor.name,gesture.delta).map(project);
        if(preview.every(Boolean))outline.setAttribute('points',preview.map(p=>p.join(',')).join(' '));
        group.classList.add('previewing');
      });
      const end=async(e,cancel=false)=>{
        if(!gesture||gesture.pointerId!==e.pointerId)return;
        e.preventDefault();e.stopPropagation();
        if(g.hasPointerCapture(e.pointerId))g.releasePointerCapture(e.pointerId);
        const delta=gesture.delta;gesture=null;this.dragging=false;
        marker.setAttribute('visibility','hidden');
        g.classList.remove('dragging');group.classList.remove('previewing');
        outline.setAttribute('points',points.map(p=>p.join(',')).join(' '));
        if(!cancel&&delta.some(v=>Math.abs(v)>1e-8))await this.commit(handleCommand(geometry,descriptor.name,delta,false));
      };
      g.addEventListener('pointerup',e=>end(e));g.addEventListener('pointercancel',e=>end(e,true));g.addEventListener('lostpointercapture',e=>end(e,true));
      g.addEventListener('keydown',e=>{
        const d={ArrowLeft:[-.1,0,0],ArrowRight:[.1,0,0],ArrowUp:[0,-.1,0],ArrowDown:[0,.1,0]}[e.key];
        if(!d||!this.enabled())return;
        e.preventDefault();e.stopPropagation();
        if(geometry.entity==='opening'&&geometry.vertical&&!(geometry.rehost&&descriptor.name==='center')){
          if(e.key==='ArrowUp'||e.key==='ArrowDown')d.splice(0,3,0,0,e.key==='ArrowUp'?.1:-.1);
          else {const sign=e.key==='ArrowRight'?1:-1;d.splice(0,3,...geometry.direction.map(v=>v*.1*sign));}
        }
        const command=handleCommand(geometry,descriptor.name,d);
        if(command.type==='move_opening'||command.delta_m.some(v=>Math.abs(v)>1e-8))this.commit(command);
      });
    }
  }
}
