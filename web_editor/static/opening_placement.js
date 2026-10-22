// Preview host placement in metres; the backend validates the final edit.
export function openingPlacement(geometry, delta) {
  const position=geometry.origin.slice(0,2).map((v,i)=>v+delta[i]);
  let best=null;
  for(const wall of geometry.hostWalls||[]) {
    const [a,b]=wall.line,length=Math.hypot(b[0]-a[0],b[1]-a[1]),margin=geometry.width/2+.025;
    if(length<2*margin||geometry.top>wall.height+1e-8)continue;
    const d=[(b[0]-a[0])/length,(b[1]-a[1])/length];
    const along=Math.max(margin,Math.min(length-margin,(position[0]-a[0])*d[0]+(position[1]-a[1])*d[1]));
    const center=[a[0]+d[0]*along,a[1]+d[1]*along],distance=Math.hypot(center[0]-position[0],center[1]-position[1]);
    if(distance<=.6&&(!best||distance<best.distance-1e-10||Math.abs(distance-best.distance)<=1e-10&&wall.id===geometry.hostId))
      best={distance,center,direction:d,wallId:wall.id};
  }
  return best;
}

export function doorLeaf(opening, angle=Math.PI/2, inset=0) {
  const reversed=opening.hinge_side==='end',ends=opening.reference_line;
  const hinge=ends[reversed?1:0],other=ends[reversed?0:1],length=Math.hypot(other[0]-hinge[0],other[1]-hinge[1]);
  const direction=[(other[0]-hinge[0])/length,(other[1]-hinge[1])/length];
  const start=hinge.map((v,i)=>v+direction[i]*inset);
  return {hinge:start,closed:other,end:start.map((v,i)=>v+(direction[i]*Math.cos(angle)+opening.normal[i]*Math.sin(angle))*(length-2*inset))};
}
