// Screen-distance snapping is independent of the 100 mm movement grid.
const cache=new WeakMap();
const cross=(a,b)=>a[0]*b[1]-a[1]*b[0];
const minus=(a,b)=>[a[0]-b[0],a[1]-b[1]];

function targets(plan){
  if(cache.has(plan))return cache.get(plan);
  const scale=plan.pixel_to_meter,segments=[],nodes=new Map();
  function addNode(point,ids){
    const key=point.map(v=>v.toFixed(8)).join(',');
    if(!nodes.has(key))nodes.set(key,{point,ids:new Set()});
    for(const id of ids)nodes.get(key).ids.add(id);
  }
  for(const entity of ['wall','railing'])for(const item of plan[entity==='wall'?'walls':'railings']){
    const id=entity+':'+item[entity+'_id'],[a,b]=item.reference_line.map(p=>p.map(v=>v*scale));
    segments.push({id,a,b});addNode(a,[id]);addNode(b,[id]);
  }
  for(let i=0;i<segments.length;i++)for(let j=i+1;j<segments.length;j++){
    const first=segments[i],second=segments[j],u=minus(first.b,first.a),v=minus(second.b,second.a),den=cross(u,v);
    if(Math.abs(den)<1e-12)continue;
    const w=minus(second.a,first.a),t=cross(w,v)/den,q=cross(w,u)/den;
    if(t>=-1e-8&&t<=1+1e-8&&q>=-1e-8&&q<=1+1e-8)addNode([first.a[0]+u[0]*t,first.a[1]+u[1]*t],[first.id,second.id]);
  }
  const result={segments,nodes:[...nodes.values()]};cache.set(plan,result);return result;
}

export function snapMovement(plan,geometry,name,delta,project,{enabled=true,scale=1}={}){
  if(!enabled||geometry.entity==='opening')return {delta,snap:null};
  const points=geometry.outline;
  let moving;
  if(name==='center')moving=points;
  else if(name==='start'||name==='end')moving=[points[name==='start'?0:1]];
  else if(name.startsWith('corner:'))moving=[points[Number(name.split(':')[1])]];
  else return {delta,snap:null};
  const own=geometry.entity+':'+geometry.id,{nodes,segments}=targets(plan);
  let best=null;
  const consider=(source,target,kind,radius)=>{
    const candidate=[target[0],target[1],source[2]],screen=project(candidate),proposed=project(source.map((v,i)=>v+delta[i]));
    if(!screen||!proposed)return;
    const distance=Math.hypot(screen[0]-proposed[0],screen[1]-proposed[1]);
    if(distance<=radius*scale&&(!best||distance<best.distance))best={distance,point:candidate,kind,
      delta:[target[0]-source[0],target[1]-source[1],0]};
  };
  for(const source of moving)for(const node of nodes){
    if(node.ids.size===1&&node.ids.has(own))continue;
    consider(source,node.point,'node',12);
  }
  if(!best)for(const source of moving)for(const segment of segments){
    if(segment.id===own)continue;
    const proposed=source.map((v,i)=>v+delta[i]),d=minus(segment.b,segment.a),length=d[0]**2+d[1]**2;
    const t=Math.max(0,Math.min(1,((proposed[0]-segment.a[0])*d[0]+(proposed[1]-segment.a[1])*d[1])/length));
    consider(source,[segment.a[0]+d[0]*t,segment.a[1]+d[1]*t],'wall',8);
  }
  return best?{delta:best.delta,snap:{point:best.point,kind:best.kind}}:{delta,snap:null};
}
