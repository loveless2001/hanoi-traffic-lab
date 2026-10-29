"""Build the extended Ring Road 3 coverage from a bounded OSM snapshot.
Requires networkx, numpy, rasterio. Does not modify the legacy experiment data.
"""
from pathlib import Path
import sys,json,math,re,collections,argparse,gzip
ROOT=Path(__file__).resolve().parents[1]
pa=argparse.ArgumentParser();pa.add_argument('--source',type=Path,required=True);pa.add_argument('--population',type=Path,required=True);pa.add_argument('--output',type=Path,default=ROOT/'regions');a=pa.parse_args();a.output.mkdir(parents=True,exist_ok=True)
import networkx as nx
import numpy as np
import rasterio
from rasterio.windows import from_bounds,Window
B=[105.74,20.94,106.00,21.19];KX=111320*math.cos(math.radians(21.021));KY=111320
def xy(n):return ((n['lon']-105.816)*KX,(n['lat']-21.021)*KY)
source_text=gzip.open(a.source,'rt',encoding='utf-8').read() if a.source.suffix=='.gz' else a.source.read_text(encoding='utf-8')
data=json.loads(source_text);raw={x['id']:x for x in data['elements'] if x['type']=='node'}
classes={'motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','living_street'}
g=nx.DiGraph();waters=[];places=[]
for n in raw.values():
 if n.get('tags',{}).get('place') in ['city','town','suburb','quarter'] and n.get('tags',{}).get('name'):places.append(dict(name=n['tags']['name'],lon=n['lon'],lat=n['lat']))
for w in data['elements']:
 if w['type']!='way':continue
 t=w.get('tags',{});h=t.get('highway');ids=w['nodes']
 if t.get('natural')=='water' and len(ids)>3 and ids[0]==ids[-1] and all(i in raw for i in ids):
  ring=[[round(raw[i]['lon'],6),round(raw[i]['lat'],6)] for i in ids]
  if len(ring)>500:ring=ring[::max(1,len(ring)//350)]+[ring[0]]
  waters.append(dict(type='Feature',geometry=dict(type='Polygon',coordinates=[ring]),properties=dict(name=t.get('name',''),osm_way=w['id'])))
 if h not in classes or t.get('access') in ['private','no'] or t.get('motor_vehicle')=='no':continue
 car=t.get('motorcar')!='no';moto=not h.startswith('motorway') and t.get('motorcycle')!='no' and t.get('motorbike')!='no'
 if not(car or moto):continue
 one=t.get('oneway') in ['yes','1','true','-1'] or t.get('junction')=='roundabout';ids=ids[::-1] if t.get('oneway')=='-1' else ids
 try:lanes=float((t.get('lanes:forward') or t.get('lanes') or '2').split(';')[0]);lanes=lanes if one or 'lanes:forward' in t else max(1,lanes/2)
 except (ValueError,TypeError):lanes=1
 lanes=min(4,max(1,lanes));base=h.replace('_link','');speed={'motorway':80,'trunk':50,'primary':35,'secondary':30,'tertiary':25,'unclassified':20,'residential':20,'living_street':15}.get(base,25)
 if '_link' in h:speed=min(speed,30)
 try:layer=int(t.get('layer','0'))
 except ValueError:layer=0
 for u,v in zip(ids,ids[1:]):
  if u==v or u not in raw or v not in raw:continue
  length=math.dist(xy(raw[u]),xy(raw[v]))
  if length<.05:continue
  attr=dict(length=length,lanes=lanes,name=t.get('name',''),highway=h,geometry=[[raw[u]['lon'],raw[u]['lat']],[raw[v]['lon'],raw[v]['lat']]],moto=moto,car=car,layer=layer,bridge=t.get('bridge','no')!='no',tunnel=t.get('tunnel','no')!='no',speed=speed/3.6,way_ids=[w['id']])
  g.add_edge(u,v,**attr)
  if not one:r=attr.copy();r['geometry']=attr['geometry'][::-1];g.add_edge(v,u,**r)
cg=nx.DiGraph((u,v) for u,v,d in g.edges(data=True) if d['car']);keep=max(nx.strongly_connected_components(cg),key=len);g=g.subgraph(keep).copy();mg=nx.DiGraph((u,v) for u,v,d in g.edges(data=True) if d['moto']);moto_keep=max(nx.strongly_connected_components(mg),key=len)
ug=g.to_undirected();anchors=set()
for u in g:
 parts=list(g.in_edges(u,data=True))+list(g.out_edges(u,data=True));sig={tuple(p[2][k] for k in ['lanes','highway','moto','car','layer','bridge','tunnel','speed']) for p in parts}
 if ug.degree(u)!=2 or raw[u].get('tags',{}).get('highway')=='traffic_signals' or len(sig)>1:anchors.add(u)
nodes=[]
for u in sorted(anchors):
 n=raw[u];x,y=xy(n);nodes.append([str(u),round(n['lon'],7),round(n['lat'],7),round(x,3),round(y,3)])
edges=[];edge_source=[]
for u in sorted(anchors):
 for nxt in g.successors(u):
  path=[u,nxt];prev=u;cur=nxt
  while cur not in anchors:
   choices=[v for v in g.successors(cur) if v!=prev]
   if len(choices)!=1:break
   prev,cur=cur,choices[0];path.append(cur)
   if len(path)>len(g):raise RuntimeError('Cycle while simplifying')
  if cur not in anchors or cur==u:continue
  parts=[g[x][y] for x,y in zip(path,path[1:])];d=parts[0];length=sum(p['length'] for p in parts);geom=[p['geometry'][0] for p in parts]+[parts[-1]['geometry'][-1]];geom=[[round(x,6),round(y,6)] for x,y in geom]
  attrs={k:d[k] for k in ['moto','car','layer','bridge','tunnel','highway']};edges.append([str(u),str(cur),round(length,3),d['lanes'],round(d['speed'],9),round(max(1.1,length/1000*d['lanes']*140),4),'existing',geom,d['name'],None,attrs]);edge_source.append(sorted(set(sum([p['way_ids'] for p in parts],[]))))
node_map={n[0]:n for n in nodes};neigh=collections.defaultdict(set)
for e in edges:neigh[e[0]].add(e[1]);neigh[e[1]].add(e[0])
junctions=[u for u in node_map if len(neigh[u])>=3];bins=collections.defaultdict(list)
for u in junctions:n=node_map[u];bins[(int(n[3]//100),int(n[4]//100))].append(u)
signals=set()
for n in raw.values():
 if n.get('tags',{}).get('highway')!='traffic_signals' or n['id'] not in g:continue
 x,y=xy(n);ix,iy=int(x//100),int(y//100);candidates=[u for dx in [-1,0,1] for dy in [-1,0,1] for u in bins.get((ix+dx,iy+dy),[])]
 if candidates:
  u=min(candidates,key=lambda u:math.hypot(node_map[u][3]-x,node_map[u][4]-y))
  if math.hypot(node_map[u][3]-x,node_map[u][4]-y)<=80:signals.add(u)
eligible=[n for n in nodes if int(n[0]) in moto_keep];portals=[]
for ix in range(9):
 for iy in range(9):
  lon=B[0]+(ix+.5)/9*(B[2]-B[0]);lat=B[1]+(iy+.5)/9*(B[3]-B[1]);x=(lon-105.816)*KX;y=(lat-21.021)*KY
  n=min(eligible,key=lambda n:(n[3]-x)**2+(n[4]-y)**2)
  if n[0] not in portals:portals.append(n[0])
with rasterio.open(a.population) as ds:
 w=from_bounds(*B,ds.transform);w=Window(math.floor(w.col_off),math.floor(w.row_off),math.ceil(w.width)+1,math.ceil(w.height)+1);arr=ds.read(1,window=w,masked=True);tr=ds.window_transform(w);mask=np.ma.getmaskarray(arr);cells=[]
 for row in range(0,arr.shape[0],3):
  for col in range(0,arr.shape[1],3):
   rr=min(arr.shape[0],row+3);cc=min(arr.shape[1],col+3)
   if mask[row:rr,col:cc].all():continue
   value=float(arr[row:rr,col:cc].sum());x1,y1=tr*(col,row);x2,y2=tr*(cc,rr);area=6371**2*math.radians(x2-x1)*(math.sin(math.radians(y1))-math.sin(math.radians(y2)));cells.append([round(x1,7),round(y2,7),round(x2,7),round(y1,7),round(value,2),round(value/area,1)])
pop=dict(cells=cells,year=2020,grid_meters=300,source_grid_meters=100,aggregation='Sum of 3 by 3 original WorldPop cells',source_url='https://hub.worldpop.org/geodata/summary?id=6449',clip_bbox=B,units='people per aggregated cell; density people/km2')
weights={}
for p in portals:
 n=node_map[p];weights[p]=round(max(1,sum(c[4]*math.exp(-(((n[1]-(c[0]+c[2])/2)*KX)**2+((n[2]-(c[1]+c[3])/2)*KY)**2)/(2*1200**2)) for c in cells)),3)
stats=dict(nodes=len(nodes),directed_links=len(edges),junctions=len(junctions),signals=len(signals),directed_km=round(sum(e[2] for e in edges)/1000,2),portals=len(portals),classes=dict(collections.Counter(e[10]['highway'] for e in edges)),moto_prohibited_links=sum(not e[10]['moto'] for e in edges),bbox=B,approx_bbox_km2=round((B[2]-B[0])*KX*(B[3]-B[1])*KY/1e6,1),population_cells=len(cells))
payload=dict(region=dict(id='rr3',label='Vành đai 3 + dải đệm',coverage_note='Khung phủ toàn vùng trong Vành đai 3 và một dải đệm; không phải ranh giới hành chính.',bbox=B,stats=stats,source_url=data['source_url'],osm_timestamp=data.get('osm_timestamp'),population_radius_m=1200),bbox=B,source='© OpenStreetMap contributors / Geofabrik',networks=dict(S0=dict(nodes=nodes,edges=edges,signals=sorted(signals),feeders=[],bbox=B)),routebooks=dict(S0=[]),portals=portals,feeders=[],portalWeights=weights,population=pop,water=dict(type='FeatureCollection',features=waters),places=places)
p=a.output/'inside-ring3.json';p.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8');(a.output/'inside-ring3-stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
with gzip.GzipFile(filename='',mode='wb',fileobj=(a.output/'inside-ring3.json.gz').open('wb'),mtime=0) as zipped:zipped.write(p.read_bytes())
print(json.dumps(dict(**stats,bytes=p.stat().st_size),ensure_ascii=False),flush=True)
