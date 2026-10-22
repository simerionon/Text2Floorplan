import {doorLeaf} from './opening_placement.js';
// A small offline WebGL renderer. Geometry is derived from the editable JSON.
const sub=(a,b)=>a.map((v,i)=>v-b[i]),add=(a,b)=>a.map((v,i)=>v+b[i]),mul=(a,s)=>a.map(v=>v*s),dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],unit=a=>mul(a,1/(Math.hypot(...a)||1));
const rgb=hex=>[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255);
const colors={living:'#d6dfc6',bedroom:'#d6dfeb',kitchen:'#e5d8bb',bathroom:'#c7dfdf',balcony:'#c1d6ba',storage:'#ded6cc',stair:'#d4d0df'};
export {colors};
function multiply(a,b){const c=new Float32Array(16);for(let col=0;col<4;col++)for(let row=0;row<4;row++)for(let k=0;k<4;k++)c[col*4+row]+=a[k*4+row]*b[col*4+k];return c;}
function triangles(ring){
  const p=ring.filter((v,i)=>{const a=ring[(i+ring.length-1)%ring.length],b=ring[(i+1)%ring.length];return Math.abs((v[0]-a[0])*(b[1]-v[1])-(v[1]-a[1])*(b[0]-v[0]))>1e-8;});
  const area=p.reduce((s,a,i)=>{const b=p[(i+1)%p.length];return s+a[0]*b[1]-b[0]*a[1]},0),sign=Math.sign(area),indices=p.map((_,i)=>i),out=[];
  const turn=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
  while(indices.length>3){let found=false;for(let j=0;j<indices.length;j++){const ids=[indices[(j+indices.length-1)%indices.length],indices[j],indices[(j+1)%indices.length]], [a,b,c]=ids.map(i=>p[i]);if(sign*turn(a,b,c)<=1e-9)continue;if(indices.some(i=>!ids.includes(i)&&sign*turn(a,b,p[i])>=-1e-9&&sign*turn(b,c,p[i])>=-1e-9&&sign*turn(c,a,p[i])>=-1e-9))continue;out.push([a,b,c]);indices.splice(j,1);found=true;break;}if(!found)throw Error('Unable to triangulate room');}
  if(indices.length===3)out.push(indices.map(i=>p[i]));return out;
}
export class Scene {
  constructor(canvas,onSelect,onDraw=()=>{}){this.canvas=canvas;this.select=onSelect;this.onDraw=onDraw;this.gl=canvas.getContext('webgl',{antialias:true});if(!this.gl)throw Error('WebGL is unavailable. Use a browser with hardware acceleration.');this.theta=-.9;this.phi=.85;this.distance=25;this.faces=[];
    const gl=this.gl,shader=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s};
    this.program=gl.createProgram();gl.attachShader(this.program,shader(gl.VERTEX_SHADER,'attribute vec3 p;attribute vec3 n;attribute vec3 c;uniform mat4 m;varying vec3 color;void main(){gl_Position=m*vec4(p,1.0);float light=0.62+0.38*max(dot(normalize(n),normalize(vec3(-0.4,-0.6,1.0))),0.0);color=c*light;}'));gl.attachShader(this.program,shader(gl.FRAGMENT_SHADER,'precision mediump float;varying vec3 color;void main(){gl_FragColor=vec4(color,1.0);}'));gl.linkProgram(this.program);if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(this.program));gl.useProgram(this.program);this.buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);for(const [i,name] of ['p','n','c'].entries()){const a=gl.getAttribLocation(this.program,name);gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,3,gl.FLOAT,false,36,i*12);}gl.enable(gl.DEPTH_TEST);this.matrix=gl.getUniformLocation(this.program,'m');
    let drag;canvas.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY};canvas.setPointerCapture(e.pointerId)});canvas.addEventListener('pointermove',e=>{if(!drag)return;this.theta-=(e.clientX-drag.x)*.008;this.phi=Math.max(.12,Math.min(1.5,this.phi+(e.clientY-drag.y)*.008));drag.x=e.clientX;drag.y=e.clientY;this.draw()});canvas.addEventListener('pointerup',e=>{if(drag&&Math.hypot(e.clientX-drag.startX,e.clientY-drag.startY)<4)this.pick(e);drag=null});canvas.addEventListener('pointercancel',()=>drag=null);canvas.addEventListener('wheel',e=>{e.preventDefault();this.distance=Math.max(2,Math.min(200,this.distance*Math.exp(e.deltaY*.001)));this.draw()},{passive:false});new ResizeObserver(()=>this.draw()).observe(canvas);
  }
  setPlan(plan,selected,fit=false){this.plan=plan;this.selected=selected;const s=plan.pixel_to_meter,all=[...plan.rooms.flatMap(r=>r.polygon),...plan.walls.flatMap(w=>w.reference_line),...plan.railings.flatMap(r=>r.reference_line)],xs=all.map(p=>p[0]*s),ys=all.map(p=>p[1]*s);this.boundsCenter=[(Math.min(...xs)+Math.max(...xs))/2,(Math.min(...ys)+Math.max(...ys))/2];if(fit||!this.center)this.center=this.boundsCenter.slice();this.span=Math.max(Math.max(...xs)-Math.min(...xs),Math.max(...ys)-Math.min(...ys));if(fit)this.distance=Math.max(8,this.span*1.6);this.vertices=[];this.faces=[];
    const tri=(a,b,c,color,tag)=>{const points=[a,b,c].map(p=>[p[0]-this.center[0],p[1]-this.center[1],p[2]]),normal=unit(cross(sub(points[1],points[0]),sub(points[2],points[0])));if(tag&&['room','space'].includes(tag.entity)&&normal[2]<0)normal[2]*=-1;const selected=tag&&this.selected&&tag.entity===this.selected.entity&&tag.id===this.selected.id,col=rgb(selected?'#dea653':color);for(const p of points)this.vertices.push(...p,...normal,...col);if(tag)this.faces.push({points,tag});};
    const quad=(a,b,c,d,color,tag)=>{tri(a,b,c,color,tag);tri(a,c,d,color,tag)};
    const box=(a,b,width,z0,z1,color,tag)=>{const d=unit([b[0]-a[0],b[1]-a[1],0]),n=[-d[1]*width/2,d[0]*width/2],v=[[a[0]+n[0],a[1]+n[1],z0],[b[0]+n[0],b[1]+n[1],z0],[b[0]-n[0],b[1]-n[1],z0],[a[0]-n[0],a[1]-n[1],z0]];v.push(...v.map(p=>[p[0],p[1],z1]));for(const ids of [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]])quad(...ids.slice().reverse().map(i=>v[i]),color,tag)};
    const ground=Math.min(50,Math.ceil(this.span/2)+3);for(let i=-ground;i<=ground;i++){box([this.center[0]-ground,this.center[1]+i],[this.center[0]+ground,this.center[1]+i],.012,-.13,-.125,'#dce3d9',null);box([this.center[0]+i,this.center[1]-ground],[this.center[0]+i,this.center[1]+ground],.012,-.13,-.125,'#dce3d9',null)}
    if(plan.enclosed_spaces){
      for(const space of plan.enclosed_spaces){const room=plan.rooms.find(r=>r.room_id===space.room_ids[0]),tag=space.status==='closed'?{entity:'room',id:space.room_ids[0]}:{entity:'space',id:space.space_id},color=space.status==='merged'?'#dcd1b5':colors[room?.type]||'#dedbd1';
        for(const t of space.floor_triangles)tri(...t.map(p=>[p[0]*s,p[1]*s,0]),color,tag);
      }
    }else{
    for(const r of plan.rooms){if(['door','front_door'].includes(r.type))continue;const p=r.polygon.map(p=>p.map(v=>v*s)),tag={entity:'room',id:r.room_id},color=colors[r.type]||'#dedbd1';for(const t of triangles(p))tri(...t.map(p=>[...p,0]),color,tag);for(let i=0;i<p.length;i++)box(p[i],p[(i+1)%p.length],.015,-.1,0,color,tag);}
    }
    for(const w of plan.walls){const a=w.reference_line[0].map(v=>v*s),b=w.reference_line[1].map(v=>v*s),length=Math.hypot(b[0]-a[0],b[1]-a[1]),d=[(b[0]-a[0])/length,(b[1]-a[1])/length],at=t=>[a[0]+d[0]*t,a[1]+d[1]*t],tag={entity:'wall',id:w.wall_id};const holes=plan.openings.filter(o=>o.wall_id===w.wall_id).map(o=>{const mid=(o.center[0]*s-a[0])*d[0]+(o.center[1]*s-a[1])*d[1];return{lo:mid-o.width_m/2,hi:mid+o.width_m/2,z0:o.sill_m,z1:o.sill_m+o.height_m,opening:o}}),xx=[0,length,...holes.flatMap(h=>[h.lo,h.hi])].sort((a,b)=>a-b),zz=[0,w.height_m,...holes.flatMap(h=>[h.z0,h.z1])].sort((a,b)=>a-b);
      for(let i=0;i<xx.length-1;i++)for(let j=0;j<zz.length-1;j++){const x=(xx[i]+xx[i+1])/2,z=(zz[j]+zz[j+1])/2;if(xx[i+1]-xx[i]<1e-7||zz[j+1]-zz[j]<1e-7||holes.some(h=>x>h.lo&&x<h.hi&&z>h.z0&&z<h.z1))continue;box(at(xx[i]),at(xx[i+1]),w.thickness_m,zz[j],zz[j+1],'#f1f0e8',tag)}
      for(const h of holes){const o=h.opening,ot={entity:'opening',id:plan.openings.indexOf(o)},frame=o.type==='window'?'#587b7d':'#9f7954',t=.045;box(at(h.lo),at(h.lo+t),w.thickness_m+.025,h.z0,h.z1,frame,ot);box(at(h.hi-t),at(h.hi),w.thickness_m+.025,h.z0,h.z1,frame,ot);box(at(h.lo),at(h.hi),w.thickness_m+.025,h.z1-t,h.z1,frame,ot);if(o.type==='window'){box(at(h.lo),at(h.hi),w.thickness_m+.025,h.z0,h.z0+t,frame,ot);box(at(h.lo+t),at(h.hi-t),.025,h.z0+t,h.z1-t,'#a1c4c8',ot);box(at((h.lo+h.hi)/2-t/2),at((h.lo+h.hi)/2+t/2),.06,h.z0,h.z1,frame,ot)}else{const leaf=doorLeaf({...o,reference_line:[at(h.lo),at(h.hi)]},Math.atan2(.34,.94),t);box(leaf.hinge,leaf.end,.04,h.z0,h.z1-t,'#c3a079',ot)}}
    }
    for(const joint of plan.wall_joints||[]){const p=joint.polygon.map(p=>[p[0]*s,p[1]*s]),z=joint.height_m,tag={entity:'wall',id:joint.wall_ids.includes(this.selected?.id)?this.selected.id:joint.wall_ids[0]};
      for(const t of triangles(p)){tri(...t.map(p=>[...p,z]),'#f1f0e8',tag);tri(...t.slice().reverse().map(p=>[...p,0]),'#f1f0e8',tag);}
      for(let i=0;i<p.length;i++){const a=p[i],b=p[(i+1)%p.length];quad([...a,0],[...b,0],[...b,z],[...a,z],'#f1f0e8',tag);}
    }
    for(const r of plan.railings){const a=r.reference_line[0].map(v=>v*s),b=r.reference_line[1].map(v=>v*s),tag={entity:'railing',id:r.railing_id},length=Math.hypot(...sub(b,a)),n=Math.ceil(length/.7);box(a,b,.055,r.height_m-.055,r.height_m,'#6e8176',tag);box(a,b,.035,.35,.385,'#85968b',tag);for(let i=0;i<=n;i++){const p=a.map((v,j)=>v+(b[j]-v)*i/n);box([p[0]-.02,p[1]],[p[0]+.02,p[1]],.04,0,r.height_m,'#6e8176',tag)}}
    const gl=this.gl;gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(this.vertices),gl.STATIC_DRAW);this.draw();
  }
  setView(name){this.theta=-.9;this.phi=name==='top'?1.5:.85;this.draw()}
  fit(){if(this.plan)this.setPlan(this.plan,this.selected,true)}
  camera(){const cp=Math.cos(this.phi);this.eye=[this.distance*cp*Math.cos(this.theta),this.distance*cp*Math.sin(this.theta),this.distance*Math.sin(this.phi)+.8];this.forward=unit(sub([0,0,.8],this.eye));this.right=unit(cross(this.forward,[0,0,1]));this.up=unit(cross(this.right,this.forward));}
  draw({width:exportWidth,height:exportHeight,notify=true}={}){if(!this.plan||!this.canvas.clientWidth||!this.canvas.clientHeight)return;const c=this.canvas,ratio=Math.min(devicePixelRatio||1,2),width=exportWidth||Math.max(1,Math.round(c.clientWidth*ratio)),height=exportHeight||Math.max(1,Math.round(c.clientHeight*ratio));if(c.width!==width||c.height!==height){c.width=width;c.height=height}this.camera();const z=mul(this.forward,-1),x=this.right,y=this.up,e=this.eye,view=new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,e),-dot(y,e),-dot(z,e),1]),f=1/Math.tan(Math.PI/8),near=.1,far=Math.max(500,this.distance+this.span*3),perspective=new Float32Array([f/(width/height),0,0,0,0,f,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0]),gl=this.gl;gl.viewport(0,0,width,height);gl.clearColor(.949,.965,.941,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.uniformMatrix4fv(this.matrix,false,multiply(perspective,view));gl.drawArrays(gl.TRIANGLES,0,this.vertices.length/9);if(notify)this.onDraw();}
  async exportPng(){
    if(!this.plan)return;
    try{return await new Promise((resolve,reject)=>{this.draw({width:2048,height:1536,notify:false});this.canvas.toBlob(blob=>blob?resolve(blob):reject(Error('Unable to export the model image')),'image/png');});}
    finally{this.draw();}
  }
  project(world){
    const rect=this.canvas.getBoundingClientRect(),p=sub([world[0]-this.center[0],world[1]-this.center[1],world[2]],this.eye),depth=dot(p,this.forward);
    if(depth<=.1)return null;
    const f=1/Math.tan(Math.PI/8);
    return [(1+dot(p,this.right)*f/(rect.width/rect.height)/depth)*rect.width/2,(1-dot(p,this.up)*f/depth)*rect.height/2];
  }
  pointOnPlane(event,origin,normal){
    const rect=this.canvas.getBoundingClientRect(),x=((event.clientX-rect.left)/rect.width*2-1)*Math.tan(Math.PI/8)*rect.width/rect.height,y=(1-(event.clientY-rect.top)/rect.height*2)*Math.tan(Math.PI/8);
    const ray=unit(add(this.forward,add(mul(this.right,x),mul(this.up,y)))),eye=[this.eye[0]+this.center[0],this.eye[1]+this.center[1],this.eye[2]],denominator=dot(ray,normal);
    if(Math.abs(denominator)<.03)return null;
    const distance=dot(sub(origin,eye),normal)/denominator;
    return distance>0?add(eye,mul(ray,distance)):null;
  }
  pick(event){const rect=this.canvas.getBoundingClientRect(),x=((event.clientX-rect.left)/rect.width*2-1)*Math.tan(Math.PI/8)*rect.width/rect.height,y=(1-(event.clientY-rect.top)/rect.height*2)*Math.tan(Math.PI/8),ray=unit(add(this.forward,add(mul(this.right,x),mul(this.up,y))));let best=Infinity,tag=null;for(const f of this.faces){const [a,b,c]=f.points,e1=sub(b,a),e2=sub(c,a),h=cross(ray,e2),det=dot(e1,h);if(Math.abs(det)<1e-8)continue;const s=sub(this.eye,a),u=dot(s,h)/det;if(u<0||u>1)continue;const q=cross(s,e1),v=dot(ray,q)/det;if(v<0||u+v>1)continue;const t=dot(e2,q)/det;if(t>.01&&t<best){best=t;tag=f.tag}}this.select(tag);}
}
