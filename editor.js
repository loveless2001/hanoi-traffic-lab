/* Editable road topology and routing. Coordinates are sourced OSM lon/lat or
   user-drawn design coordinates. Original code, MIT. No dependencies. */
(function(global){
'use strict';
const KX=111320*Math.cos(21.021*Math.PI/180),KY=111320,xy=p=>[(p[0]-105.816)*KX,(p[1]-21.021)*KY],ll=p=>[p[0]/KX+105.816,p[1]/KY+21.021],distance=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
const clamp=x=>Math.max(0,Math.min(1,x)),clone=x=>JSON.parse(JSON.stringify(x)),sub=(a,b)=>[a[0]-b[0],a[1]-b[1]],cross=(a,b)=>a[0]*b[1]-a[1]*b[0];
function project(p,a,b){const d=sub(b,a),t=clamp(((p[0]-a[0])*d[0]+(p[1]-a[1])*d[1])/(d[0]*d[0]+d[1]*d[1]||1));const q=[a[0]+t*d[0],a[1]+t*d[1]];return {t,p:q,d:distance(p,q)};}
function prepareGroup(g){g.pts=g.geometry.map(xy);g.offsets=[0];for(let i=1;i<g.pts.length;i++)g.offsets.push(g.offsets[i-1]+distance(g.pts[i-1],g.pts[i]));g.length=g.offsets.at(-1);g.cuts=[];return g;}
function nearestOnGroup(g,p){let best={d:Infinity};for(let i=1;i<g.pts.length;i++){const r=project(p,g.pts[i-1],g.pts[i]);if(r.d<best.d)best={...r,s:g.offsets[i-1]+r.t*(g.offsets[i]-g.offsets[i-1])};}return best;}
function at(g,s){for(let i=1;i<g.offsets.length;i++)if(s<=g.offsets[i]+1e-7){const z=(s-g.offsets[i-1])/(g.offsets[i]-g.offsets[i-1]||1);return [g.pts[i-1][0]*(1-z)+g.pts[i][0]*z,g.pts[i-1][1]*(1-z)+g.pts[i][1]*z];}return g.pts.at(-1);}
function portion(g,a,b){return [at(g,a),...g.pts.filter((_,i)=>g.offsets[i]>a+1e-6&&g.offsets[i]<b-1e-6),at(g,b)].map(ll);}
function intersection(a,b,c,d){const r=sub(b,a),s=sub(d,c),den=cross(r,s);if(Math.abs(den)<1e-8)return null;const t=cross(sub(c,a),s)/den,u=cross(sub(c,a),r)/den;if(t< -1e-8||t>1+1e-8||u< -1e-8||u>1+1e-8)return null;return {t:clamp(t),u:clamp(u),p:[a[0]+clamp(t)*r[0],a[1]+clamp(t)*r[1]]};}
function baseGroups(base){const groups=[],byKey=new Map();base.edges.forEach((e,i)=>{
 const forward=e[0]<e[1],coords=forward?e[7]:e[7].slice().reverse(),key=[...[e[0],e[1]].sort(),coords.map(p=>p.map(x=>x.toFixed(7)).join(',')).join(';')].join('|');
 if(!byKey.has(key)){const g=prepareGroup({ref:'base:'+i,kind:'existing',geometry:clone(e[7]),u:e[0],v:e[1],directions:[]});groups.push(g);byKey.set(key,g);}
 const g=byKey.get(key);g.directions.push({edge:e,index:i,reverse:e[0]!==g.u});
 });return groups;}
function validateDesign(design){
 if(!design||!Array.isArray(design.lines))throw Error('Phương án không hợp lệ.');if(design.lines.length>24)throw Error('Tối đa 24 đường / nhánh trong một phương án.');
 let n=0;const ids=new Set();for(const line of design.lines){if(typeof line.id!=='string'||ids.has(line.id))throw Error('Mã tuyến không hợp lệ.');ids.add(line.id);if(!['road','access'].includes(line.kind)||!Number.isInteger(line.lanes)||line.lanes<1||line.lanes>3)throw Error('Kiểm tra loại đường và số làn.');if(!Array.isArray(line.points)||line.points.length<2)throw Error('Tuyến cần ít nhất hai điểm.');n+=line.points.length;
 for(const p of line.points)if(!p||!Array.isArray(p.ll)||p.ll.length!==2||!p.ll.every(Number.isFinite)||p.ll[0]<105.800||p.ll[0]>105.832||p.ll[1]<21.010||p.ll[1]>21.032)throw Error('Tuyến phải nằm trong vùng bản đồ đang nghiên cứu.');
 if(!line.points[0].ref||!line.points.at(-1).ref)throw Error('Hai đầu tuyến phải nối vào đường có sẵn.');
 }if(n>120)throw Error('Tối đa 120 điểm vẽ; hãy dùng ít điểm hơn.');
 if(JSON.stringify(design).length>13000)throw Error('Phương án quá lớn để lưu; hãy giảm số điểm vẽ.');return true;
}
function buildNetwork(data,design={lines:[],autoConnect:true}){
 validateDesign(design);const base=clone(data.networks.S0);base.feeders=[];
 if(!design.lines.length){base.edges=base.edges.map((e,i)=>{e[9]={group:'base:'+i,original:i};return e;});const gs=baseGroups(base);for(const g of gs)for(const dir of g.directions)base.edges[dir.index][9].group=g.ref;base.inventory={roads:0,branches:0,addedKm:0,junctions:0};base.connections=[];return base;}
 const nodes=clone(base.nodes),nodeMap=new Map(nodes.map(n=>[n[0],n])),groups=baseGroups(base),gm=new Map(groups.map(g=>[g.ref,g])),usedNodes=new Set();
 function newNode(p,preferred){if(preferred&&nodeMap.has(preferred)){usedNodes.add(preferred);return preferred;}
  for(const id of usedNodes){const n=nodeMap.get(id);if(distance(p,[n[3],n[4]])<.3)return id;}
  for(const n of nodes)if(distance(p,[n[3],n[4]])<.2){usedNodes.add(n[0]);return n[0];}
  // Coordinate-based ids keep the signal offset of an unchanged junction
  // stable when a different branch is added or deleted elsewhere.
  const id='EDIT_'+Math.round(p[0]*1000)+'_'+Math.round(p[1]*1000),q=ll(p),n=[id,q[0],q[1],p[0],p[1]];nodes.push(n);nodeMap.set(id,n);usedNodes.add(id);return id;
 }
 function cut(g,s,id){const old=g.cuts.find(c=>Math.abs(c.s-s)<1e-5);if(old&&old.id!==id)return old.id;g.cuts.push({s:Math.max(0,Math.min(g.length,s)),id});return id;}
 for(const g of groups){g.cuts=[{s:0,id:g.u},{s:g.length,id:g.v}];}
 const newGroups=[];
 for(const line of design.lines){const g=prepareGroup({ref:'design:'+line.id,kind:line.kind,geometry:line.points.map(p=>p.ll),line,lanes:line.lanes,directions:[]});if(g.length<15)throw Error('Đường / nhánh phải dài ít nhất 15 m.');groups.push(g);newGroups.push(g);gm.set(g.ref,g);}
 // Endpoints resolve against a persistent physical-edge reference. No hidden
 // nearest-road reassignment is performed when the design is rebuilt.
 for(const g of newGroups)for(const [index,s] of [[0,0],[g.line.points.length-1,g.length]]){
  const point=g.line.points[index],target=gm.get(point.ref);if(!target||target===g)throw Error('Một đầu tuyến không còn đường để nối.');const hit=nearestOnGroup(target,xy(point.ll));if(hit.d>2)throw Error('Điểm nối cách đường quá xa; hãy vẽ lại điểm đầu/cuối.');
  const preferred=hit.s<.3?target.u:target.length-hit.s<.3?target.v:undefined,id=newNode(hit.p,preferred);cut(target,hit.s,id);cut(g,s,id);
 }
 // Every interior bend is a geometry node; only actual connections receive
 // junction control below. Baseline grade-separated crossings stay separate.
 for(const g of newGroups){for(let i=1;i<g.pts.length-1;i++){const id=newNode(g.pts[i]);cut(g,g.offsets[i],id);}}
 if(design.autoConnect!==false)for(let ai=0;ai<groups.length;ai++)for(let bi=ai+1;bi<groups.length;bi++){
  const a=groups[ai],b=groups[bi];if(a.kind==='existing'&&b.kind==='existing')continue;
  for(let i=1;i<a.pts.length;i++)for(let j=1;j<b.pts.length;j++){
   const hit=intersection(a.pts[i-1],a.pts[i],b.pts[j-1],b.pts[j]);if(!hit)continue;const sa=a.offsets[i-1]+hit.t*(a.offsets[i]-a.offsets[i-1]),sb=b.offsets[j-1]+hit.u*(b.offsets[j]-b.offsets[j-1]);
   const ca=a.cuts.find(c=>Math.abs(c.s-sa)<.3),cb=b.cuts.find(c=>Math.abs(c.s-sb)<.3),id=newNode(hit.p,ca?.id||cb?.id);cut(a,sa,id);cut(b,sb,id);
  }
 }
 // New-road endpoints which hit later design lines may have no u/v yet; all
 // must have resolved cuts after the endpoint pass.
 const edges=[];
 for(const g of groups){g.cuts.sort((a,b)=>a.s-b.s);const cuts=[];for(const c of g.cuts){if(!cuts.length||c.s-cuts.at(-1).s>1e-5)cuts.push(c);}
  if(cuts.length<2||cuts[0].s>.01||g.length-cuts.at(-1).s>.01)throw Error('Có tuyến chưa nối đủ hai đầu.');
  for(let i=1;i<cuts.length;i++){const a=cuts[i-1],b=cuts[i];if(a.id===b.id||b.s-a.s<.01)continue;const geometry=portion(g,a.s,b.s);
   if(g.kind==='existing')for(const dir of g.directions){const e=clone(dir.edge),length=e[2]*(b.s-a.s)/g.length;e[0]=dir.reverse?b.id:a.id;e[1]=dir.reverse?a.id:b.id;e[2]=length;e[5]=Math.max(1.1,length/1000*e[3]*140);e[7]=dir.reverse?geometry.slice().reverse():geometry;e[9]={group:g.ref,original:dir.index};edges.push(e);}
   else for(const reverse of [false,true]){const length=b.s-a.s;edges.push([reverse?b.id:a.id,reverse?a.id:b.id,length,g.lanes,g.kind==='road'?40/3.6:20/3.6,Math.max(1.1,length/1000*g.lanes*140),g.kind==='road'?'new_road':'access',reverse?geometry.slice().reverse():geometry,(g.kind==='road'?'Đường ':'Nhánh ')+g.line.id,{group:g.ref,lineId:g.line.id}]);}
  }
 }
 const neighbors=new Map(nodes.map(n=>[n[0],new Set()]));for(const e of edges){neighbors.get(e[0]).add(e[1]);neighbors.get(e[1]).add(e[0]);}
 const signals=new Set(base.signals);let addedJunctions=0;for(const id of usedNodes)if(neighbors.get(id).size>=3){if(!signals.has(id))addedJunctions++;signals.add(id);}
 return {nodes,edges,signals:Array.from(signals).sort(),feeders:[],connections:Array.from(usedNodes).filter(id=>neighbors.get(id).size>=3),inventory:{roads:design.lines.filter(x=>x.kind==='road').length,branches:design.lines.filter(x=>x.kind==='access').length,addedKm:newGroups.reduce((s,g)=>s+g.length,0)/1000,junctions:addedJunctions}};
}
// Binary heap uses distance, then node id: same tie rule as the Python model.
class Heap{constructor(){this.a=[];}less(a,b){return a[0]<b[0]||a[0]===b[0]&&a[1]<b[1];}push(x){let i=this.a.push(x)-1;while(i){let p=(i-1)>>1;if(!this.less(x,this.a[p]))break;this.a[i]=this.a[p];i=p;}this.a[i]=x;}pop(){const r=this.a[0],x=this.a.pop();if(this.a.length){let i=0;while(i*2+1<this.a.length){let j=i*2+1;if(j+1<this.a.length&&this.less(this.a[j+1],this.a[j]))j++;if(!this.less(this.a[j],x))break;this.a[i]=this.a[j];i=j;}this.a[i]=x;}return r;}get length(){return this.a.length;}}
function routeTrips(net,trips,config={}){const cycle=config.cycle||90,lost=config.lost??14,signals=new Set(net.signals),adj=new Map(),pairs=new Map(),book=new Map();net.edges.forEach((e,i)=>{if(!adj.has(e[0]))adj.set(e[0],[]);adj.get(e[0]).push([e,i]);});for(const t of trips){if(!pairs.has(t.origin))pairs.set(t.origin,new Set());pairs.get(t.origin).add(t.destination);}
 for(const origin of Array.from(pairs.keys()).sort())for(const mode of ['moto','car']){const dist=new Map([[origin,0]]),prev=new Map(),h=new Heap();h.push([0,origin]);while(h.length){const [cost,u]=h.pop();if(dist.get(u)!==cost)continue;for(const [e,i] of adj.get(u)||[]){const red=(cycle+lost)/2,delay=signals.has(e[1])?red*red/(2*cycle):0,z=cost+e[2]/(e[4]*(mode==='moto'?1.08:1))+delay;if(z<(dist.get(e[1])??Infinity)){dist.set(e[1],z);prev.set(e[1],[u,i]);h.push([z,e[1]]);}}}
  for(const dst of pairs.get(origin)){const p=[];let u=dst;while(u!==origin){if(!prev.has(u))throw Error('Phương án làm mất đường đi của một hành trình; chưa thể so sánh.');const v=prev.get(u);p.push(v[1]);u=v[0];}book.set(origin+'|'+dst+'|'+mode,p.reverse());}
 }
 return trips.map(t=>book.get(t.origin+'|'+t.destination+'|'+t.mode));
}
function deleteLine(design,id){const d=clone(design),removed=new Set([id]);let changed=true;while(changed){changed=false;for(const line of d.lines)if(!removed.has(line.id)&&line.points.some(p=>p.ref?.startsWith('design:')&&removed.has(p.ref.slice(7)))){removed.add(line.id);changed=true;}}d.lines=d.lines.filter(l=>!removed.has(l.id));return {design:d,removed:Array.from(removed)};}
function fingerprint(trips){let h=2166136261;for(const t of trips)for(const ch of `${t.id}|${t.departure}|${t.origin}|${t.destination}|${t.mode};`){h^=ch.charCodeAt(0);h=Math.imul(h,16777619);}return (h>>>0).toString(16).padStart(8,'0');}
const api={buildNetwork,routeTrips,deleteLine,validateDesign,fingerprint,xy,ll,project};if(typeof module!=='undefined'&&module.exports)module.exports=api;global.HanoiEditor=api;
})(typeof window==='undefined'?globalThis:window);
