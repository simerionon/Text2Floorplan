import {Scene,colors} from './scene.js';
import {PlanNavigation} from './plan_navigation.js';
import {HandleLayer,selectionGeometry} from './edit_handles.js';
import {snapMovement} from './node_snap.js';
import {doorLeaf} from './opening_placement.js';

const $=id=>document.getElementById(id),svgNS='http://www.w3.org/2000/svg';
let plan,selection=null,history=[],future=[],busy=false,jobId=null,language=location.pathname.startsWith('/zh')?'zh':'en',scene,navigation,fitWidth=1,planHandles,modelHandles,elevationHandles,nodeSnapEnabled=true;
const zh={saveImage:'保存 PNG',snapHint:'开启或关闭节点吸附，Alt 临时关闭。',emptyPlan:'从这里，开始你的空间。',emptyPlanHelp:'在上方描述户型，点击生成，得到可编辑的平面图。',emptyModel:'换一个角度，看见空间。',emptyModelHelp:'生成后的三维模型会显示在这里，并随平面编辑同步更新。',emptyInspector:'尚未创建模型',emptyInspectorHelp:'先生成户型或打开 JSON，再选择构件查看尺寸和面积。',emptyReady:'就绪。生成户型或打开 JSON 模型。',promptRequired:'请先输入户型提示词，或选择一个示例。',smallExample:'小户型 · 2 卧室',defaultExample:'默认 · 3 卧室',largeExample:'大户型 · 4 卧室',snap:'吸附',open:'未闭合',merged:'已合并',split:'已分隔',unassigned:'未命名空间',enclosedTotal:'封闭空间总净面积',partialTotal:'已闭合部分净面积',partial:'部分未闭合',offsetX:'X 位移 (mm)',offsetY:'Y 位移 (mm)',base:'离地高度 (mm)',promptHeadline:'描述空间，创造你的家。',projectCaption:'首层 / 可编辑模型',planOnly:'二维平面',splitView:'双视图',modelOnly:'三维模型',examplesLabel:'提示词示例与可改参数',editable:'可编辑',groundFloor:'首层平面',perspective:'透视视图',selectTool:'选择',panTool:'平移',resetView:'重置视角',topView:'俯视',spaceHint:'按住并拖动，可在任意位置平移。',selectHint:'选择构件，编辑边、端点或中心。',panHint:'只移动视图，不选择构件。',spaces:'空间列表',productName:'文字生成户型图',corner:'移动角点',subtitle:'让想象，成为可编辑的空间。',local:'本地运行',promptLabel:'从一个想法开始',generate:'生成户型 ✧',cancel:'取消',examples:'n 替换为数量；默认中户型省略大小词，不要输入 none。',project:'户型设计',undo:'↶ 撤销',redo:'↷ 重做',sample:'导入样例',import:'打开 JSON',export:'保存模型 ↗',plan:'户型平面',planHint:'拖动空白处平移 · 滚轮缩放',model:'空间预览',modelHint:'拖动旋转 · 滚轮缩放',units:'尺寸单位 mm · 面积单位 m²',fit:'适应',live:'实时联动',linked:'与平面联动',properties:'属性面板',workflow:'常用快捷操作',step1:'生成或导入户型。',step2:'编辑平面及构件尺寸。',step3:'保存可编辑模型 JSON。',note:'平面和三维共用一个模型，每次有效修改都会同步更新。',footer:'本地设计，自由保存。',select:'选择一个构件',selectHelp:'选择墙、门窗、栏杆或房间，拖动边、端点或中心进行编辑。',total:'总净面积',rooms:'房间',height:'高度 (mm)',thickness:'厚度 (mm)',width:'宽度 (mm)',sill:'窗台高 (mm)',position:'沿墙位置 (%)',apply:'应用修改',move:'移动选中墙段',wallPosition:'墙线位置 (m)',roomHint:'拖动角点或边调整房间，拖动中心平移整个房间。相邻墙线会同步更新。',railing:'阳台栏杆',wall:'墙体',opening:'门窗',ready:'就绪。选择构件开始编辑。',saving:'正在检查并更新模型…',saved:'模型已更新。',loading:'正在加载…',generating:'正在启动本地推理…',cancelled:'推理已取消。',failed:'推理失败：',loaded:'模型已加载。',downloaded:'已保存 JSON。',bedroom:'卧室',living:'客厅',kitchen:'厨房',bathroom:'卫生间',balcony:'阳台',storage:'储藏间',stair:'楼梯',door:'门',front_door:'入户门',window:'窗',errorPrefix:'修改未应用：'};
const en={emptyInspector:'A blank canvas',emptyInspectorHelp:'Generate a layout or open JSON, then select an element to inspect its dimensions and area.',emptyReady:'Ready. Generate a layout or open a JSON model.',promptRequired:'Enter an apartment prompt or choose an example first.',snap:'Snap',open:'Not enclosed',merged:'Merged',split:'Split',unassigned:'Unnamed space',enclosedTotal:'Total enclosed floor area',partialTotal:'Enclosed floor area (partial)',partial:'Partially enclosed',offsetX:'X offset (mm)',offsetY:'Y offset (mm)',base:'Base height (mm)',promptHeadline:'Describe the space. Make it yours.',projectCaption:'Ground floor / editable model',planOnly:'2D plan',splitView:'Split view',modelOnly:'3D model',examplesLabel:'Prompt examples & supported options',editable:'EDITABLE',groundFloor:'GROUND FLOOR',perspective:'PERSPECTIVE',selectTool:'Select',panTool:'Pan',resetView:'Reset view',topView:'Top',spaceHint:'Hold and drag to pan anywhere.',selectHint:'Select an element to edit its handles.',panHint:'Move around without selecting objects.',spaces:'SPACES',productName:'Text2Floorplan',corner:'Move corner',select:'Select an element',selectHelp:'Select a wall, opening, railing or room to edit its edges, endpoints or center.',total:'Total clear floor area',rooms:'rooms',height:'Height (mm)',thickness:'Thickness (mm)',width:'Width (mm)',sill:'Sill height (mm)',position:'Along wall (%)',apply:'Apply changes',move:'Move selected segment',wallPosition:'Wall position (m)',roomHint:'Drag a corner or edge to reshape; drag the center to move the room. Connected walls update together.',railing:'Balcony railing',wall:'Wall',opening:'Opening',ready:'Ready. Select an element to start editing.',saving:'Checking and updating the model…',saved:'Model updated.',loading:'Loading…',generating:'Starting local inference…',cancelled:'Inference cancelled.',failed:'Inference failed: ',loaded:'Model loaded.',downloaded:'JSON saved.',bedroom:'Bedroom',living:'Living room',kitchen:'Kitchen',bathroom:'Bathroom',balcony:'Balcony',storage:'Storage',stair:'Stair',door:'Door',front_door:'Entrance door',window:'Window',errorPrefix:'Edit not applied: '};
const t=key=>(language==='zh'?zh[key]:en[key])||key;
for(const el of document.querySelectorAll('[data-i18n]'))en[el.dataset.i18n]=el.textContent;
const areaText=(value,state='open')=>value==null?t(state):value.toFixed(1);
const areaTitle=()=>plan?.enclosed_spaces?t(plan.editor?.area_status==='partial'?'partialTotal':'enclosedTotal'):t('total');
function areaWarnings(){return (plan?.editor?.area_issues||[]).map(issue=>{const room=plan.rooms.find(r=>r.room_id===issue.room_id);return t(room?.type||'room')+' '+(issue.room_id+1)+': '+t(issue.code)})}
function floorSpaces(){return plan.enclosed_spaces||plan.rooms.filter(r=>!['door','front_door'].includes(r.type)).map(r=>({room_ids:[r.room_id],polygon:r.polygon,holes:r.holes||[],interior_point:r.interior_point||r.polygon[0],area_m2:plan.room_areas_m2[String(r.room_id)],status:'closed'}))}
function spaceName(space){return space.room_ids.length?space.room_ids.map(id=>t(plan.rooms.find(r=>r.room_id===id)?.type||'room')).join(' + '):t('unassigned')}
function spaceSelection(space){return space.status==='closed'&&space.room_ids.length===1?{entity:'room',id:space.room_ids[0]}:{entity:'space',id:space.space_id}}
function boundaryPath(polygon,holes=[]){return [polygon,...holes].map(ring=>'M '+ring.map(p=>p.join(' ')).join(' L ')+' Z').join(' ')}

function status(message,error=false){$('status').textContent=message;$('status').classList.toggle('error',error)}
function lock(value){busy=value;document.body.classList.toggle('busy',value);for(const id of ['generate','sample','import'])$(id).disabled=value;syncHistory()}
function syncHistory(){$('undo').disabled=busy||!history.length;$('redo').disabled=busy||!future.length;$('export').disabled=!plan;$('export3').disabled=!plan||!scene;}
async function request(path,body){const response=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-Text2Revit-Editor':'1'},body:JSON.stringify(body)});const result=await response.json();if(!response.ok)throw Error(result.error||'Request failed');return result;}
function remember(){if(plan){history.push(structuredClone(plan));if(history.length>50)history.shift()}future=[];}
function accept(result,fit=false){plan=result;document.body.classList.remove('is-empty');$('area').title=plan.enclosed_spaces?(language==='zh'?'按当前墙线识别封闭区域，扣除墙体占地；未闭合空间不计入总面积。':'Current bounded spaces minus wall footprints; unclosed rooms are excluded.'):'';$('area').textContent=`${plan.rooms.filter(r=>!['door','front_door'].includes(r.type)).length} ${t('rooms')} · ${areaText(plan.total_area_m2)} m²${plan.editor?.area_status==='partial'?' · '+t('partial'):''}`;$('prompt').value=plan.prompt||$('prompt').value;renderPlan(fit);renderInspector();scene?.setPlan(plan,selection,fit);syncHistory();const warnings=[...(plan.editor?.warnings||[]),...areaWarnings()];status(warnings.length?warnings.join(' · '):t('ready'),warnings.length>0);}
function choose(value){if(busy)return;selection=value;renderPlan();renderInspector();document.querySelector('aside').scrollTop=0;if(plan)scene?.setPlan(plan,selection)}
function element(name,attrs={},text){const node=document.createElementNS(svgNS,name);for(const [key,value] of Object.entries(attrs))node.setAttribute(key,value);if(text!==undefined)node.textContent=text;return node;}
function svgPoint(event){const p=$('plan').createSVGPoint();p.x=event.clientX;p.y=event.clientY;return p.matrixTransform($('plan').getScreenCTM().inverse())}
function renderPlan(reset=false){if(!plan)return;const svg=$('plan');svg.replaceChildren();const all=[...plan.rooms.flatMap(r=>r.polygon),...plan.walls.flatMap(w=>w.reference_line),...plan.railings.flatMap(r=>r.reference_line)],xs=all.map(p=>p[0]),ys=all.map(p=>p[1]),minX=Math.min(...xs)-18,minY=Math.min(...ys)-18,width=Math.max(...xs)-minX+18,height=Math.max(...ys)-minY+18;if(reset||!svg.hasAttribute('viewBox')){svg.setAttribute('viewBox',`${minX} ${minY} ${width} ${height}`);fitWidth=width;}
  const defs=element('defs'),pattern=element('pattern',{id:'grid',width:10,height:10,patternUnits:'userSpaceOnUse'});pattern.append(element('circle',{cx:0,cy:0,r:.35,fill:'#d7e0d4'}));defs.append(pattern);svg.append(defs,element('rect',{x:minX,y:minY,width,height,fill:'url(#grid)','data-canvas-background':''}));
  for(const space of floorSpaces()){
    const tag=spaceSelection(space),selected=selection?.entity===tag.entity&&selection.id===tag.id||selection?.entity==='room'&&space.room_ids.includes(selection.id),room=plan.rooms.find(r=>r.room_id===space.room_ids[0]);
    const shape=element('path',{d:boundaryPath(space.polygon,space.holes),fill:space.status==='merged'?'#dcd1b5':colors[room?.type]||'#dedbd1','fill-rule':'evenodd','fill-opacity':selected?.8:.48,class:'room'});
    shape.addEventListener('click',()=>choose(tag));svg.append(shape);
  }
  for(const wall of plan.walls){const [a,b]=wall.reference_line,selected=selection?.entity==='wall'&&selection.id===wall.wall_id;svg.append(element('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:selected?'#cf9a42':'#66766a','stroke-width':wall.thickness_m/plan.pixel_to_meter}));const length=Math.hypot(b[0]-a[0],b[1]-a[1]),half=Math.max(5,wall.thickness_m/plan.pixel_to_meter)/2,n=[-(b[1]-a[1])/length*half,(b[0]-a[0])/length*half],hit=element('polygon',{points:[[a[0]+n[0],a[1]+n[1]],[b[0]+n[0],b[1]+n[1]],[b[0]-n[0],b[1]-n[1]],[a[0]-n[0],a[1]-n[1]]].map(p=>p.join(',')).join(' '),class:'wall-hit',role:'button',tabindex:0,'aria-label':`${t('wall')} ${wall.wall_id}`});hit.addEventListener('click',()=>choose({entity:'wall',id:wall.wall_id}));hit.addEventListener('keydown',e=>{if(e.key==='Enter')choose({entity:'wall',id:wall.wall_id})});svg.append(hit)}
  for(const joint of plan.wall_joints||[]){const selected=selection?.entity==='wall'&&joint.wall_ids.includes(selection.id),shape=element('path',{d:boundaryPath(joint.polygon),fill:selected?'#cf9a42':'#66766a',class:'wall-joint','data-wall-ids':joint.wall_ids.join(' ')});shape.addEventListener('click',()=>choose({entity:'wall',id:joint.wall_ids[0]}));svg.append(shape)}
  for(const railing of plan.railings){const [a,b]=railing.reference_line,line=element('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:selection?.id===railing.railing_id?'#cf9a42':'#7e9684','stroke-width':1.5,'stroke-dasharray':'3 1',class:'opening'});line.addEventListener('click',()=>choose({entity:'railing',id:railing.railing_id}));svg.append(line)}
  for(const [index,opening] of plan.openings.entries()){const [a,b]=opening.reference_line,wall=plan.walls.find(w=>w.wall_id===opening.wall_id),selected=selection?.entity==='opening'&&selection.id===index,width=(wall?.thickness_m||.2)/plan.pixel_to_meter,group=element('g',{class:'opening',role:'button',tabindex:0,'aria-label':`${t(opening.type)} ${index+1}`});group.addEventListener('keydown',e=>{if(e.key==='Enter')choose({entity:'opening',id:index})});if(opening.type!=='window'){const n=opening.normal,w=opening.width;group.append(element('polygon',{points:[a,b,[b[0]+n[0]*w,b[1]+n[1]*w],[a[0]+n[0]*w,a[1]+n[1]*w]].map(p=>p.join(',')).join(' '),fill:'transparent'}))}group.append(element('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'#f8faf7','stroke-width':width+.7}));if(opening.type==='window'){for(const delta of [-width*.25,width*.25])group.append(element('line',{x1:a[0]+opening.normal[0]*delta,y1:a[1]+opening.normal[1]*delta,x2:b[0]+opening.normal[0]*delta,y2:b[1]+opening.normal[1]*delta,stroke:selected?'#d79930':'#568c91','stroke-width':.7}));}else{const n=opening.normal,w=opening.width,{hinge,closed,end:leaf}=doorLeaf(opening);group.append(element('line',{x1:hinge[0],y1:hinge[1],x2:leaf[0],y2:leaf[1],stroke:selected?'#cf9a42':'#ab8459','stroke-width':.8}));group.append(element('path',{d:`M ${closed.join(' ')} Q ${closed[0]+n[0]*w} ${closed[1]+n[1]*w} ${leaf.join(' ')}`,fill:'none',stroke:'#b3a18b','stroke-width':.5}));}group.append(element('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'transparent','stroke-width':width+2}));group.addEventListener('click',()=>choose({entity:'opening',id:index}));svg.append(group)}
  for(const space of floorSpaces()){
    const p=space.interior_point,text=element('text',{x:p[0],y:p[1]-1,class:'room-label','font-size':Math.min(9,Math.max(7.5,width/40))});
    text.append(element('tspan',{x:p[0]},spaceName(space)),element('tspan',{x:p[0],dy:9,'font-size':6,fill:'#6f8175'},`${areaText(space.area_m2)} m²`));svg.append(text);
  }
  for(const room of plan.rooms.filter(r=>r.area_status==='open')){
    svg.append(element('path',{d:boundaryPath(room.polygon,room.holes),class:'unclosed-boundary'}));
    const p=room.interior_point||room.polygon[0],text=element('text',{x:p[0],y:p[1],class:'room-label unclosed-label','font-size':7});
    text.append(element('tspan',{x:p[0]},t(room.type)),element('tspan',{x:p[0],dy:9,'font-size':6},t('open')));svg.append(text);
  }
  updateZoomLabel();
}
function handleLabel(name){
  if(selection?.entity==='wall')return language==='zh'?({center:'移动墙段',start:'移动起点',end:'移动终点'})[name]:({center:'Move wall segment',start:'Move start endpoint',end:'Move end endpoint'})[name];
  const labels=language==='zh'?{center:'移动中心',start:'移动起点',end:'移动终点',left:'移动左边',right:'移动右边',top:'移动上边',bottom:'移动下边'}:{center:'Move center',start:'Move start',end:'Move end',left:'Move left edge',right:'Move right edge',top:'Move top edge',bottom:'Move bottom edge'};
  if(name.startsWith('corner:'))return t('corner')+' '+(Number(name.split(':')[1])+1);
  if(name.startsWith('edge:'))return (language==='zh'?'移动边 ':'Move edge ')+(Number(name.split(':')[1])+1);
  return labels[name]||name;
}
function handleLayer(){return new HandleLayer({commit:edit,enabled:()=>!busy,label:handleLabel,snapLabel:kind=>language==='zh'?(kind==='node'?'节点':'墙线'):kind.toUpperCase()})}
function renderPlanHandles(){
  planHandles ||= handleLayer();
  const svg=$('plan'),matrix=svg.getScreenCTM(),scale=matrix?1/Math.hypot(matrix.a,matrix.b):1;
  const geometry=selectionGeometry(plan,selection,'plan'),project=p=>[p[0]/plan.pixel_to_meter,p[1]/plan.pixel_to_meter];
  planHandles.render(svg,geometry,{project,
    unproject:event=>{const p=svgPoint(event);return [p.x*plan.pixel_to_meter,p.y*plan.pixel_to_meter,0]},scale,
    snap:(delta,name,temporary)=>snapMovement(plan,geometry,name,delta,project,{enabled:nodeSnapEnabled&&temporary,scale})});
}
function renderModelHandles(){
  if(!scene||!plan)return;
  modelHandles ||= handleLayer();const svg=$('model-handles'),canvas=$('model');
  if(!canvas.clientWidth||!canvas.clientHeight)return;
  svg.setAttribute('viewBox',`0 0 ${canvas.clientWidth} ${canvas.clientHeight}`);
  const geometry=selectionGeometry(plan,selection,'model'),project=p=>scene.project(p);modelHandles.render(svg,geometry,{project,unproject:(event,g,handle)=>scene.pointOnPlane(event,handle.position,g.rehost&&handle.name==='center'?[0,0,1]:g.normal),snap:(delta,name,temporary)=>snapMovement(plan,geometry,name,delta,project,{enabled:nodeSnapEnabled&&temporary})});
}
function renderElevation(host){
  const g=selectionGeometry(plan,selection,'elevation');if(!g)return;
  const title=document.createElement('p');title.className='handle-help';
  title.textContent=language==='zh'?'正立面：拖中心移动整块，拖四边调整尺寸。方向键每次移动 100 mm。':'Elevation: drag the center to move; drag an edge to resize. Arrow keys move 100 mm.';
  const svg=element('svg',{class:'opening-elevation',viewBox:'0 0 230 190','aria-label':language==='zh'?'门窗正立面编辑':'Opening elevation editor'});
  host.append(title,svg);elevationHandles ||= handleLayer();
  const o=plan.openings[selection.id],center=g.handles.find(h=>h.name==='center').position,scale=Math.min(170/Math.max(o.width_m,.5),135/Math.max(o.height_m,.5));
  const project=p=>[115+((p[0]-center[0])*g.direction[0]+(p[1]-center[1])*g.direction[1])*scale,95-(p[2]-center[2])*scale];
  elevationHandles.render(svg,g,{project,unproject:event=>{
    const p=svg.createSVGPoint();p.x=event.clientX;p.y=event.clientY;const xy=p.matrixTransform(svg.getScreenCTM().inverse());
    return [center[0]+g.direction[0]*(xy.x-115)/scale,center[1]+g.direction[1]*(xy.x-115)/scale,center[2]-(xy.y-95)/scale];
  }});
}

function field(form,label,key,value){
  const id=`property-${key}`,wrapper=document.createElement('div'),l=document.createElement('label'),shell=document.createElement('div'),input=document.createElement('input'),suffix=document.createElement('span');
  wrapper.className='field';shell.className='input-shell';l.htmlFor=id;l.textContent=t(label).replace(/\s*\((mm|m|%)\)$/,'');input.type='number';input.id=id;input.name=key;input.step='any';input.value=Number(value.toFixed(3));input.required=true;
  suffix.className='unit';suffix.textContent=key==='editor_position'?'%':key==='position_m'?'m':'mm';shell.append(input,suffix);wrapper.append(l,shell);form.append(wrapper);return input;
}
function heading(container,title,detail){const h=document.createElement('h2'),small=document.createElement('div');h.textContent=title;small.className='element-id';small.textContent=detail;container.append(h,small)}
function wallHandleHelp(host){
  const help=document.createElement('p');help.className='wall-handle-help';
  help.textContent=language==='zh'?'拖动两端圆点，只移动这一端，另一端固定；拖动中心方点，平移整段墙及其门窗。其他墙保持原位，面积自动重算。按住 Alt 可临时关闭吸附。':'Drag an endpoint circle to move only that end. Drag the center square to translate the wall and its openings. Other walls stay fixed; areas update automatically. Hold Alt to disable snapping.';
  host.append(help);
}
function openingControls(host,item){
  const help=document.createElement('p');help.className='handle-help';
  help.textContent=language==='zh'?'拖中心方点到另一面墙，门窗自动贴墙转向。下方正立面可沿墙及上下移动。':'Drag the center to another wall to snap and turn. Use the elevation below to move along the wall or vertically.';
  host.append(help);
  if(item.type==='window')return;
  for(const [axis,en,zh] of [['swing','Flip swing direction','翻转开门方向'],['hinge','Swap hinge side','交换铰链侧']]){
    const button=document.createElement('button');button.type='button';button.textContent=language==='zh'?zh:en;
    button.dataset.openingAction=axis;button.onclick=()=>edit({type:'flip_opening',id:selection.id,axis});host.append(button);
  }
}
function renderInspector(){const host=$('inspector');host.replaceChildren();$('selection-count').textContent=selection?'1':'—';if(!plan){heading(host,t('emptyInspector'),t('productName'));const p=document.createElement('p');p.textContent=t('emptyInspectorHelp');host.append(p);return;}
  if(!selection){
    heading(host,t('select'),t('productName'));const p=document.createElement('p');p.textContent=t('selectHelp');host.append(p);
    const card=document.createElement('div'),label=document.createElement('span'),metric=document.createElement('div'),unit=document.createElement('small');card.className='metric-card';label.textContent=areaTitle();metric.className='metric';metric.textContent=areaText(plan.total_area_m2);unit.textContent='m²';metric.append(unit);card.append(label,metric);host.append(card);
    const list=document.createElement('div'),title=document.createElement('div');list.className='room-list';title.className='room-list-heading';title.textContent=t('spaces');list.append(title);
    const ordinals={};for(const room of plan.rooms){if(['door','front_door'].includes(room.type))continue;ordinals[room.type]=(ordinals[room.type]||0)+1;const button=document.createElement('button'),name=document.createElement('span'),dot=document.createElement('i'),area=document.createElement('small');dot.style.background=colors[room.type]||'#d4dacc';const multiple=plan.rooms.filter(r=>r.type===room.type).length>1;name.append(dot,document.createTextNode(t(room.type)+(multiple?' '+ordinals[room.type]:'')));area.textContent=plan.room_areas_m2[String(room.room_id)]==null?t(room.area_status||'open'):`${areaText(plan.room_areas_m2[String(room.room_id)])} m²`;button.append(name,area);button.addEventListener('click',()=>choose({entity:'room',id:room.room_id}));list.append(button)}host.append(list);return;
  }
  const entity=selection.entity;let item;if(entity==='space')item=plan.enclosed_spaces?.find(s=>s.space_id===selection.id);if(entity==='room')item=plan.rooms.find(r=>r.room_id===selection.id);if(entity==='wall')item=plan.walls.find(w=>w.wall_id===selection.id);if(entity==='opening')item=plan.openings[selection.id];if(entity==='railing')item=plan.railings.find(r=>r.railing_id===selection.id);if(!item){selection=null;return renderInspector()}
  if(entity==='space'){heading(host,spaceName(item),t(item.status));const metric=document.createElement('div');metric.className='metric';metric.textContent=item.area_m2.toFixed(1)+' m²';host.append(metric);return;}
  heading(host,t(item.type||entity),item.name||item.wall_id||item.railing_id||`opening_${selection.id}`);
  if(entity==='room'){
    const metric=document.createElement('div');metric.className='metric';const area=plan.room_areas_m2[String(item.room_id)];metric.textContent=area==null?t(item.area_status||'open'):area.toFixed(1)+' m²';
    const p=document.createElement('p');p.textContent=plan.enclosed_spaces?(language==='zh'?'面积按当前墙线和墙厚重新计算；未闭合时请先吸附连接墙节点。':'Area is recalculated from current walls and thickness. Close unbounded rooms by snapping wall nodes.'):t('roomHint');host.append(metric,p);return;
  }
  if(entity==='wall')wallHandleHelp(host);
  if(entity==='opening'){openingControls(host,item);renderElevation(host);}
  const help=document.createElement('p');help.className='handle-help';help.textContent=language==='zh'?'拖动中心移动整体，拖动边或端点调整形状。':'Drag the center to move. Drag an edge or endpoint to reshape.';if(entity!=='wall')host.append(help);
  const form=document.createElement('form');if(entity==='wall'){field(form,'height','height_m',item.height_m*1000);field(form,'thickness','thickness_m',item.thickness_m*1000)}else if(entity==='opening'){field(form,'width','width_m',item.width_m*1000);field(form,'height','height_m',item.height_m*1000);field(form,item.type==='window'?'sill':'base','sill_m',item.sill_m*1000);const w=plan.walls.find(w=>w.wall_id===item.wall_id),[a,b]=w.reference_line,dx=b[0]-a[0],dy=b[1]-a[1],ratio=((item.center[0]-a[0])*dx+(item.center[1]-a[1])*dy)/(dx*dx+dy*dy);field(form,'position','editor_position',ratio*100)}else field(form,'height','height_m',item.height_m*1000);
  const submit=document.createElement('button');submit.type='submit';submit.className='primary';submit.textContent=t('apply');form.append(submit);form.addEventListener('submit',async event=>{event.preventDefault();const values={};for(const [key,value] of new FormData(form))values[key]=Number(value)/(key==='editor_position'?100:1000);await edit({type:'set_parameters',entity,id:selection.id,values})});host.append(form);
  if(entity==='wall'){
    const move=document.createElement('form');field(move,'offsetX','offset_x_m',0);field(move,'offsetY','offset_y_m',0);
    const button=document.createElement('button');button.textContent=t('move');move.append(button);
    move.addEventListener('submit',async e=>{e.preventDefault();const values=new FormData(move),delta=[Number(values.get('offset_x_m'))/1000,Number(values.get('offset_y_m'))/1000];if(delta.some(v=>v!==0))await edit({type:'translate_wall',id:selection.id,delta_m:delta})});host.append(move);
  }
}
async function edit(command){if(busy)return;lock(true);status(t('saving'));try{const updated=await request('/api/edit',{plan,command});remember();accept(updated);if(!updated.editor?.warnings.length&&!updated.editor?.area_issues?.length)status(t('saved'))}catch(error){status(t('errorPrefix')+error.message,true);renderPlan()}finally{lock(false);renderModelHandles()}}
async function loadSample(){if(busy)return;lock(true);status(t('loading'));try{const result=await request('/api/sample');remember();selection=null;accept(result,true)}catch(error){status(error.message,true)}finally{lock(false)}}
$('sample').onclick=loadSample;$('fit2').onclick=()=>renderPlan(true);$('fit3').onclick=()=>{scene?.setView('perspective');scene?.fit()};$('top3').onclick=()=>scene?.setView('top');
$('undo').onclick=()=>{if(busy||!history.length)return;future.push(structuredClone(plan));selection=null;accept(history.pop())};$('redo').onclick=()=>{if(busy||!future.length)return;history.push(structuredClone(plan));selection=null;accept(future.pop())};
document.addEventListener('keydown',event=>{if(['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))return;if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='z'){event.preventDefault();$(event.shiftKey?'redo':'undo').click()}});
$('import').onclick=()=>$('file').click();$('file').onchange=async event=>{const file=event.target.files[0];if(!file)return;lock(true);try{if(file.size>2_000_000)throw Error('The JSON file must be below 2 MB');const result=await request('/api/import',{plan:JSON.parse(await file.text())});remember();selection=null;accept(result,true)}catch(error){status(error.message,true)}finally{event.target.value='';lock(false)}};
$('export3').onclick=async()=>{try{const blob=await scene?.exportPng();if(!blob)return;const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='text2floorplan-3d.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){status(error.message,true)}};
$('export').onclick=()=>{if(!plan)return;const url=URL.createObjectURL(new Blob([JSON.stringify(plan,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='text2floorplan.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status(t('downloaded'))};
function localize(){document.documentElement.lang=language==='zh'?'zh-CN':'en';document.title=t('productName');$('language').value=language;for(const el of document.querySelectorAll('[data-i18n]'))el.textContent=t(el.dataset.i18n);}localize();
$('language').onchange=()=>{language=$('language').value;window.history.replaceState(null,'',language==='zh'?'/zh':'/en');localize();if(plan)accept(plan);else{renderInspector();status(t('emptyReady'));}};
$('generate').onclick=async()=>{if(busy)return;if(!$('prompt').value.trim()){status(t('promptRequired'),true);$('prompt').focus();return;}lock(true);$('cancel').hidden=false;status(t('generating'));try{const result=await request('/api/generate',{prompt:$('prompt').value,language});jobId=result.job_id;let job;do{await new Promise(resolve=>setTimeout(resolve,1000));job=await request(`/api/jobs/${jobId}`);status(job.message||t('generating'))}while(job.state==='running');if(job.state==='complete'){remember();selection=null;accept(job.plan,true)}else if(job.state==='cancelled')status(t('cancelled'));else status(t('failed')+(job.error||''),true)}catch(error){status(error.message,true)}finally{jobId=null;$('cancel').hidden=true;lock(false)}};
$('cancel').onclick=async()=>{if(!jobId)return;try{await request(`/api/jobs/${jobId}/cancel`,{});status(t('cancelled'))}catch(error){status(error.message,true)}};
try{scene=new Scene($('model'),choose,renderModelHandles)}catch(error){status(error.message,true);$('model').insertAdjacentText('afterend',error.message)}
renderInspector();syncHistory();status(t('emptyReady'));
for(const button of document.querySelectorAll('[data-prompt]')){button.title=button.dataset.prompt;button.onclick=()=>{if(busy)return;$('prompt').value=button.dataset.prompt;$('prompt').focus();};}
$('prompt').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.isComposing){event.preventDefault();$('generate').click();}});

function updateZoomLabel(){
  const svg=$('plan'),b=svg.viewBox.baseVal;if(!b.width)return;$('zoom-label').textContent=`${Math.round(fitWidth/b.width*100)}%`;renderPlanHandles();
  const background=svg.querySelector('[data-canvas-background]');if(background){for(const [key,value] of Object.entries({x:b.x-b.width*2,y:b.y-b.height*2,width:b.width*5,height:b.height*5}))background.setAttribute(key,value);}
}
navigation=new PlanNavigation($('plan'),{onToolChange:tool=>{for(const name of ['select','pan']){const button=$(name+'-tool');button.classList.toggle('active',tool===name);button.setAttribute('aria-pressed',String(tool===name))}},onZoomChange:updateZoomLabel});
$('plan').addEventListener('click',event=>{if(event.target===$('plan')||event.target.hasAttribute('data-canvas-background'))choose(null)});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!['INPUT','TEXTAREA','SELECT'].includes(event.target.tagName))choose(null)});
$('select-tool').onclick=()=>navigation.setTool('select');$('pan-tool').onclick=()=>navigation.setTool('pan');$('zoom-in').onclick=()=>navigation.zoom(.8);$('zoom-out').onclick=()=>navigation.zoom(1.25);
for(const button of document.querySelectorAll('[data-view]'))button.addEventListener('click',()=>{document.querySelector('.views').dataset.mode=button.dataset.view;for(const item of document.querySelectorAll('[data-view]'))item.setAttribute('aria-pressed',String(item===button));renderPlanHandles();scene?.draw()});

function toggleNodeSnap(){nodeSnapEnabled=!nodeSnapEnabled;$('node-snap').setAttribute('aria-pressed',String(nodeSnapEnabled));}
$('node-snap').onclick=toggleNodeSnap;
window.addEventListener('keydown',event=>{if(event.key?.toLowerCase()==='s'&&!event.ctrlKey&&!event.metaKey&&!event.altKey&&!['INPUT','TEXTAREA','SELECT'].includes(event.target.tagName)){event.preventDefault();toggleNodeSnap()}});
