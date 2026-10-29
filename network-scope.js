/* Road-class filtering and fixed, shared demand projection. Original code, MIT. */
(function(global){
'use strict';
const groups={'no-small':new Set(['motorway','trunk','primary','secondary','tertiary']),arterial:new Set(['motorway','trunk','primary','secondary'])};
function visible(edge,detail){const h=edge[10]?.highway;return detail==='all'||edge[6]!=='existing'||!h||!!groups[detail]?.has(h.replace(/_link$/,''));}
function filter(net,detail,originalSignals=net.signals){
 if(detail!=='all'&&!groups[detail])throw Error('Bộ lọc đường không hợp lệ.');
 const indices=[];net.edges.forEach((e,i)=>{if(visible(e,detail))indices.push(i);});
 if(indices.length===net.edges.length)return {net,edgeMap:null};
 const edges=indices.map(i=>net.edges[i]),neighbors=new Map();for(const e of edges){if(!neighbors.has(e[0]))neighbors.set(e[0],new Set());if(!neighbors.has(e[1]))neighbors.set(e[1],new Set());neighbors.get(e[0]).add(e[1]);neighbors.get(e[1]).add(e[0]);}
 const existing=new Set(originalSignals),signals=net.signals.filter(id=>neighbors.has(id)&&(existing.has(id)||neighbors.get(id).size>=3));
 return {net:{...net,nodes:net.nodes.filter(n=>neighbors.has(n[0])),edges,signals,connections:(net.connections||[]).filter(id=>neighbors.get(id)?.size>=3)},edgeMap:indices};
}
function largestComponent(net,mode){
 const ids=net.nodes.map(n=>n[0]),index=new Map(ids.map((id,i)=>[id,i])),adj=ids.map(()=>[]),rev=ids.map(()=>[]);
 for(const e of net.edges)if(e[10]?.[mode]!==false){const u=index.get(e[0]),v=index.get(e[1]);adj[u].push(v);rev[v].push(u);}
 const seen=new Uint8Array(ids.length),order=[];
 for(let root=0;root<ids.length;root++)if(!seen[root]){seen[root]=1;const stack=[[root,0]];while(stack.length){const frame=stack.at(-1),u=frame[0];if(frame[1]<adj[u].length){const v=adj[u][frame[1]++];if(!seen[v]){seen[v]=1;stack.push([v,0]);}}else{order.push(u);stack.pop();}}}
 seen.fill(0);let largest=[];for(let j=order.length-1;j>=0;j--){const root=order[j];if(seen[root])continue;const component=[],stack=[root];seen[root]=1;while(stack.length){const u=stack.pop();component.push(u);for(const v of rev[u])if(!seen[v]){seen[v]=1;stack.push(v);}}if(component.length>largest.length)largest=component;}
 return new Set(largest.map(i=>ids[i]));
}
function projectDemand(data,net,trips){
 const car=largestComponent(net,'car'),moto=largestComponent(net,'moto'),eligible=net.nodes.filter(n=>car.has(n[0])&&moto.has(n[0])),source=new Map(data.networks.S0.nodes.map(n=>[n[0],n])),eligibleIds=new Set(eligible.map(n=>n[0])),portals=Array.from(new Set(data.portals)),mapping=new Map(),used=new Set();
 if(eligible.length<portals.length)throw Error('Mạng sau lọc không đủ điểm kết nối cho xe máy và ô tô; hãy chọn Hiện tất cả.');
 // Reserve still-valid original anchors before assigning off-network points.
 for(const id of portals)if(eligibleIds.has(id)){mapping.set(id,id);used.add(id);}
 for(const id of portals)if(!mapping.has(id)){const origin=source.get(id);let best=null,bestD=Infinity;for(const n of eligible){if(used.has(n[0]))continue;const d=(n[3]-origin[3])**2+(n[4]-origin[4])**2;if(d<bestD||d===bestD&&n[0]<best[0]){best=n;bestD=d;}}mapping.set(id,best[0]);used.add(best[0]);}
 const target=new Map(net.nodes.map(n=>[n[0],n])),assignments=portals.map(id=>{const a=source.get(id),b=target.get(mapping.get(id));return {original:id,node:b[0],shiftMeters:Math.hypot(a[3]-b[3],a[4]-b[4])};});
 return {trips:trips.map(t=>({...t,originalOrigin:t.origin,originalDestination:t.destination,origin:mapping.get(t.origin),destination:mapping.get(t.destination)})),projection:{assignments,remappedPortals:assignments.filter(a=>a.original!==a.node).length,maxShiftMeters:Math.max(...assignments.map(a=>a.shiftMeters)),meanShiftMeters:assignments.reduce((s,a)=>s+a.shiftMeters,0)/assignments.length}};
}
function prepare(data,drawingNets,trips,options){
 const detail=options.simulateVisibleOnly?options.roadDetail||'no-small':'all',filtered=drawingNets.map(net=>filter(net,detail,data.networks.S0.signals)),projection=filtered[0].edgeMap?projectDemand(data,filtered[0].net,trips):{trips,projection:{assignments:[],remappedPortals:0,maxShiftMeters:0,meanShiftMeters:0}};
 return {trips:projection.trips,nets:filtered.map(x=>x.net),edgeMaps:filtered.map(x=>x.edgeMap),scope:{filtered:!!filtered[0].edgeMap,detail,linkCounts:filtered.map(x=>x.net.edges.length),removedLinkCounts:filtered.map((x,i)=>drawingNets[i].edges.length-x.net.edges.length),projection:projection.projection}};
}
function mapSnapshot(snapshot,edgeMap){if(!edgeMap)return snapshot;const ratios={};for(const [id,value] of Object.entries(snapshot.ratios))if(value)ratios[edgeMap[Number(id)]]=value;snapshot.ratios=ratios;snapshot.dots=snapshot.dots.map(d=>[edgeMap[d[0]],...d.slice(1)]);snapshot.blocked=snapshot.blocked.map(id=>edgeMap[id]);return snapshot;}
const api={visible,filter,projectDemand,prepare,mapSnapshot};if(typeof module!=='undefined'&&module.exports)module.exports=api;global.HanoiScope=api;
})(typeof window==='undefined'?globalThis:window);
