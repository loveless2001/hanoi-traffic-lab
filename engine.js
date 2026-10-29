/* Finite-storage, two-class FIFO network model. Companion to simulation.py.
   Vehicle positions drawn by the viewer are schematic; queues are simulated.
   Original code, MIT. No runtime dependencies. */
(function(global){
'use strict';
const unit=a=>{let d=Math.hypot(...a);return d?[a[0]/d,a[1]/d]:[1,0]},right=a=>[a[1],-a[0]],sub=(a,b)=>[a[0]-b[0],a[1]-b[1]],cross=(a,b)=>a[0]*b[1]-a[1]*b[0];
const intersects=(a,b,c,d)=>cross(sub(b,a),sub(c,a))*cross(sub(b,a),sub(d,a))< -1e-8&&cross(sub(d,c),sub(a,c))*cross(sub(d,c),sub(b,c))< -1e-8;
function network(data,s){const k=s==='S0'?'S0':s==='S1'?'S1':'S2',a=data.networks.S0,b=data.networks[k];return {nodes:k==='S0'?a.nodes:a.nodes.concat(b.nodes),edges:k==='S0'?a.edges:a.edges.concat(b.edges),signals:b.signals,feeders:k==='S2'?data.feeders:[]};}
function rng(seed){let a=seed>>>0;return()=>{a+=0x6D2B79F5;let t=a;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296};}
function generate(data,options,pop){
 const rand=rng(options.seed),ext=rng(options.seed+1000003),net=network(data,'S0'),ns=new Map(net.nodes.map(n=>[n[0],n])),ps=data.portals;
 const cumulative=a=>{let s=0,b=a.map(x=>s+=x);return b.map(x=>x/s)},pick=(c,r)=>{let x=r();return c.findIndex(y=>y>=x)};
 const tc=cumulative(options.profile),weights=ps.map(p=>{
   if(!options.populationWeighted||!pop?.cells?.length)return 1;
   const n=ns.get(p);let val=0;for(const c of pop.cells){const dx=(n[1]-(c[0]+c[2])/2)*104000,dy=(n[2]-(c[1]+c[3])/2)*111320;val+=c[4]*Math.exp(-(dx*dx+dy*dy)/(2*300*300));}return Math.max(val,1);
 });
 function draw(n,origins,r,extra){const wc=cumulative(origins.map(o=>weights[ps.indexOf(o)]||1)),out=[];
   for(let i=0;i<n;i++){const departure=(pick(tc,r)+r())*3600,o=origins[pick(wc,r)],on=ns.get(o),ds=ps.filter(d=>d!==o&&Math.hypot(ns.get(d)[3]-on[3],ns.get(d)[4]-on[4])>=1000),d=ds[Math.floor(r()*ds.length)],mode=r()<options.motoShare?'moto':'car';out.push({id:(extra?'I':'B')+i,departure,origin:o,destination:d,mode,extra});}return out;
 }
 const base=draw(options.daily,data.portals,rand,false),extra=options.scenario==='S3'||options.scenario==='S4'?draw(Math.round(options.daily*options.induction),data.feeders,ext,true):[];
 return base.concat(extra).sort((a,b)=>a.departure-b.departure);
}
class Engine{
 constructor(data,scenario,trips,config={}){
  this.data=data;this.scenario=scenario;this.cfg=Object.assign({dt:2,horizon:90000,moto_pcu:.35,saturation:1700,cycle:90,lost:14,meter_threshold:.65},config);
  this.net=config.networkOverride||network(data,scenario);this.es=this.net.edges;this.ns=new Map(this.net.nodes.map(n=>[n[0],n]));this.trips=trips;this.N=trips.length;this.M=this.es.length;
  const k=scenario==='S0'?'S0':scenario==='S1'?'S1':'S2',book=new Map(data.routebooks[k].map(r=>[r[0]+'|'+r[1]+'|'+r[2],r[3]]));
  this.paths=config.pathsOverride||trips.map(t=>{let p=book.get(t.origin+'|'+t.destination+'|'+(t.mode==='moto'?0:1));if(!p)throw Error('Không tìm được đường: '+t.origin+' → '+t.destination);return p;});
  this.Q=Array.from({length:this.M},()=>[]);this.qhead=new Int32Array(this.M);this.occ=new Float64Array(this.M);this.inbound=new Map();
  this.es.forEach((e,i)=>{if(!this.inbound.has(e[1]))this.inbound.set(e[1],[]);this.inbound.get(e[1]).push(i)});
  this.nodeOrder=Array.from(this.inbound.keys()).sort();this.movements=new Map();const atnode=new Map();
  for(const p of this.paths)for(let i=0;i<p.length;i++){
   const e=p[i],f=i+1<p.length?p[i+1]:-1,key=e+','+f;if(this.movements.has(key))continue;
   const E=this.es[e],u=this.ns.get(E[0]),v=this.ns.get(E[1]),vin=unit([v[3]-u[3],v[4]-u[4]]),ri=right(vin),a=[-vin[0]+.16*ri[0],-vin[1]+.16*ri[1]];let b=a,turn='exit',factor=1;
   if(f>=0){let w=this.ns.get(this.es[f][1]),vo=unit([w[3]-v[3],w[4]-v[4]]),ro=right(vo);b=[vo[0]+.16*ro[0],vo[1]+.16*ro[1]];let ang=Math.atan2(cross(vin,vo),vin[0]*vo[0]+vin[1]*vo[1])*180/Math.PI;turn=Math.abs(ang)<35?'straight':ang>0?'left':'right';factor=turn==='straight'?1:turn==='right'?1.25:1.5;}
   const m={e,f,key,a,b,turn,factor,axis:Math.abs(vin[0])>=Math.abs(vin[1])?0:1,available:0,conflicts:[]};this.movements.set(key,m);if(!atnode.has(E[1]))atnode.set(E[1],[]);atnode.get(E[1]).push(m);
  }
  for(const ms of atnode.values())for(const m of ms)for(const o of ms)if(m===o||m.e===o.e||(m.f>=0&&m.f===o.f)||(m.f>=0&&o.f>=0&&intersects(m.a,m.b,o.a,o.b)))m.conflicts.push(o);
  this.signals=new Set(this.net.signals);this.lastDepart=new Float64Array(this.M);this.ready=new Float64Array(this.N);this.pos=new Int32Array(this.N);this.entered=new Float64Array(this.N).fill(-1);this.completedTimes=new Float64Array(this.N).fill(-1);this.freeTime=new Float64Array(this.N);this.individualWait=new Float64Array(this.N);this.pcu=trips.map(t=>t.mode==='moto'?this.cfg.moto_pcu:1);
  this.external=new Map(Array.from(new Set(trips.map(t=>t.origin))).sort().map(o=>[o,{items:[],head:0}]));
  this.generated=0;this.completed=0;this.baseCompleted=0;this.externalCount=0;this.inside=0;this.spill=0;this.stepNumber=0;this.t=0;this.transfers=0;this.peakExternal=0;this.peakWaiting=0;this.maxOccupancy=0;this.error=0;this.lastBlocked=new Set();this.history=[];this.lastSnapshotCompleted=0;
 }
 green(t,node,axis){if(!this.signals.has(node))return t;const c=this.cfg.cycle,offset=(Array.from(node).reduce((s,c)=>s+c.charCodeAt(0),0)*7)%c,z=(t+offset)%c,g=(c-this.cfg.lost)/2,lo=axis*c/2,hi=lo+g;return lo<=z&&z<hi-1e-9?t:t+(z<lo?lo-z:c-z+lo);}
 add(i,e,t){this.Q[e].push(i);this.occ[e]+=this.pcu[i];const speed=this.es[e][4]*(this.trips[i].mode==='moto'?1.08:1);this.ready[i]=t+this.es[e][2]/speed;this.freeTime[i]+=this.es[e][2]/speed;}
 step(){
  if(this.t>=this.cfg.horizon)return false;
  const start=this.stepNumber*this.cfg.dt,end=Math.min(this.cfg.horizon,start+this.cfg.dt),step=this.stepNumber;
  while(this.generated<this.N&&this.trips[this.generated].departure<end-1e-9){let t=this.trips[this.generated];this.external.get(t.origin).items.push(this.generated++);this.externalCount++;}
  this.peakExternal=Math.max(this.peakExternal,this.externalCount);
  for(const [o,q] of this.external)while(q.head<q.items.length){const i=q.items[q.head],e=this.paths[i][0];if(this.scenario==='S4'&&this.net.feeders.includes(o)&&this.occ[e]/this.es[e][5]>=this.cfg.meter_threshold)break;if(this.occ[e]+this.pcu[i]>this.es[e][5]+1e-8)break;q.head++;this.externalCount--;this.inside++;this.entered[i]=Math.max(start,this.trips[i].departure);this.add(i,e,this.entered[i]);}
  const blocked=new Set(),order=step%2===0?this.nodeOrder:Array.from(this.nodeOrder).reverse();
  for(const node of order){const inc=this.inbound.get(node);while(true){let best=null;
   for(const e of inc){if(this.qhead[e]>=this.Q[e].length)continue;const i=this.Q[e][this.qhead[e]],p=this.paths[i],j=this.pos[i],f=j+1<p.length?p[j+1]:-1,m=this.movements.get(e+','+f);let service=Math.max(start,this.ready[i],this.lastDepart[e],m.available);if(f>=0)service=this.green(service,node,m.axis);if(service>=end-1e-9)continue;
    if(f>=0&&this.occ[f]+this.pcu[i]>this.es[f][5]+1e-8){blocked.add(e);continue;}
    if(this.scenario==='S4'&&this.es[e][6]==='access'&&f>=0&&this.occ[f]/this.es[f][5]>=this.cfg.meter_threshold)continue;
    const tie=(e+step)%this.M;if(!best||service<best.service||service===best.service&&tie<best.tie)best={service,tie,e,f,i,m};
   }
   if(!best)break;const {service,e,f,i,m}=best;this.qhead[e]++;this.occ[e]-=this.pcu[i];this.individualWait[i]+=Math.max(0,service-this.ready[i]);const h=3600*this.pcu[i]/(this.cfg.saturation*this.es[e][3])*m.factor;this.lastDepart[e]=service+h;for(const o of m.conflicts)o.available=Math.max(o.available,service+h);this.transfers++;
   if(f<0){this.completedTimes[i]=service;this.completed++;this.inside--;if(!this.trips[i].extra)this.baseCompleted++;}else{this.pos[i]++;this.add(i,f,service);}
  }}
  this.lastBlocked=blocked;this.spill+=blocked.size*(end-start);this.error=Math.max(this.error,Math.abs(this.generated-this.completed-this.externalCount-this.inside));this.t=end;this.stepNumber++;
  return true;
 }
 metrics(){let internal=0,external=0;for(let i=0;i<this.generated;i++){internal+=this.individualWait[i];external+=(this.entered[i]>=0?this.entered[i]:this.t)-this.trips[i].departure;}
  let waiting=0;for(let e=0;e<this.M;e++)for(let j=this.qhead[e];j<this.Q[e].length;j++){let i=this.Q[e][j];internal+=Math.max(0,this.t-this.ready[i]);if(this.ready[i]<=this.t)waiting++;}
  this.peakWaiting=Math.max(this.peakWaiting,waiting);for(let e=0;e<this.M;e++)this.maxOccupancy=Math.max(this.maxOccupancy,this.occ[e]/this.es[e][5]);
  return {t:this.t,generated:this.generated,completed:this.completed,base_completed:this.baseCompleted,inside:this.inside,external:this.externalCount,unfinished:this.inside+this.externalCount,total_wait_veh_h:(internal+external)/3600,external_wait_veh_h:external/3600,spillback_link_min:this.spill/60,waiting,conservation_error:this.error,throughput_veh_h:this.t?this.completed/(this.t/3600):0};
 }
 snapshot(){const m=this.metrics(),prior=this.history.length?this.history[this.history.length-1].t:0;m.rates=this.t>prior?(this.completed-this.lastSnapshotCompleted)*3600/(this.t-prior):0;this.lastSnapshotCompleted=this.completed;const ratios=Array.from(this.occ,(x,i)=>Math.min(1,x/this.es[i][5])),dots=[];
  for(let e=0;e<this.M;e++){let cumulative=0;for(let j=this.qhead[e];j<this.Q[e].length;j++){let i=this.Q[e][j],sp=this.es[e][4]*(this.trips[i].mode==='moto'?1.08:1),ff=this.es[e][2]/sp,frac=this.ready[i]<=this.t?Math.max(.02,1-cumulative/this.es[e][5]):Math.max(.01,1-(this.ready[i]-this.t)/ff);cumulative+=this.pcu[i];if(i%Math.max(1,Math.ceil(this.N/20000))===0&&dots.length<650)dots.push([e,Math.min(.99,frac),this.trips[i].mode==='moto'?0:1,i]);}}
  const snap={...m,ratios,dots,blocked:Array.from(this.lastBlocked)};this.history.push(snap);return snap;
 }
 runAll(){while(this.step()){}return this.metrics();}
}
const api={Engine,network,generate,rng};if(typeof module!=='undefined'&&module.exports)module.exports=api;global.HanoiEngine=api;
})(typeof window==='undefined'?globalThis:window);
