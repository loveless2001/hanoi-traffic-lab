"""Extract a reproducible, contributor-free regional OSM snapshot.
Usage: python scripts/extract_rr3.py vietnam-261027.osm.pbf data/rr3_osm_snapshot.json.gz
Requires osmium (pyosmium). Source PBF is not bundled in this repository.
"""
import argparse,json,gzip
from pathlib import Path
import osmium
p=argparse.ArgumentParser();p.add_argument('pbf',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
BBOX=[105.74,20.94,106.00,21.19]
CLASSES={'motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','living_street'}
class Extract(osmium.SimpleHandler):
 def __init__(self):super().__init__();self.nodes={};self.ways=[];self.needed=set();self.places=[];self.relations=[]
 def node(self,n):
  if n.location.valid() and BBOX[0]<=n.location.lon<=BBOX[2] and BBOX[1]<=n.location.lat<=BBOX[3]:
   tags={}
   if n.tags.get('highway')=='traffic_signals':tags['highway']='traffic_signals'
   if n.tags.get('place') in ['city','town','suburb','quarter'] and n.tags.get('name'):tags.update(place=n.tags.get('place'),name=n.tags.get('name'));self.places.append(n.id)
   self.nodes[n.id]=(n.location.lon,n.location.lat,tags)
 def way(self,w):
  if w.tags.get('highway') not in CLASSES and w.tags.get('natural')!='water':return
  refs=[n.ref for n in w.nodes]
  if not any(n in self.nodes for n in refs):return
  self.ways.append(dict(type='way',id=w.id,nodes=refs,tags=dict(w.tags)));self.needed.update(n for n in refs if n in self.nodes)
 def relation(self,r):
  if r.tags.get('route')=='road' and ('nh đai 3' in r.tags.get('name','') or 'Ring Road 3' in r.tags.get('name','')):self.relations.append(dict(type='relation',id=r.id,tags=dict(r.tags),members=[dict(type=m.type,ref=m.ref,role=m.role) for m in r.members]))
h=Extract();h.apply_file(str(a.pbf));h.needed.update(h.places)
nodes=[dict(type='node',id=i,lon=h.nodes[i][0],lat=h.nodes[i][1],tags=h.nodes[i][2]) for i in sorted(h.needed)]
data=dict(version=.6,generator='Local bounded extraction of Geofabrik Vietnam snapshot',source_url='https://download.geofabrik.de/asia/vietnam-261027.osm.pbf',osm_timestamp='2026-10-27T21:23:59Z',bbox=BBOX,elements=nodes+h.ways+h.relations)
raw=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode();a.output.parent.mkdir(parents=True,exist_ok=True)
with gzip.GzipFile(filename='',mode='wb',fileobj=a.output.open('wb'),mtime=0) as z:z.write(raw)
print('Extracted',len(nodes),'nodes and',len(h.ways),'ways to',a.output)
