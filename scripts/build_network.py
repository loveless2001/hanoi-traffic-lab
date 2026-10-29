from pathlib import Path
import json,math,collections,argparse
import networkx as nx
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=ROOT/'data/osm_snapshot.json');parser.add_argument('--output',type=Path,default=ROOT);args=parser.parse_args()
OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
BBOX=[105.800,21.010,105.832,21.032]
data=json.loads(args.source.read_text(encoding='utf-8'))
raw={a['id']:a for a in data['elements'] if a['type']=='node'}
classes={'primary','primary_link','secondary','secondary_link','tertiary','tertiary_link'}
ways=[a for a in data['elements'] if a['type']=='way' and a.get('tags',{}).get('highway') in classes and a.get('tags',{}).get('access') not in ['private','no'] and a.get('tags',{}).get('motor_vehicle')!='no']
def inside(n):return BBOX[0]<=n['lon']<=BBOX[2] and BBOX[1]<=n['lat']<=BBOX[3]
def xy(n):return [(n['lon']-105.816)*111320*math.cos(math.radians(21.021)),(n['lat']-21.021)*111320]
def dist(a,b):return math.dist(xy(raw[a]),xy(raw[b]))
g=nx.DiGraph()
for w in ways:
    tag=w['tags'];h=tag['highway'];one=tag.get('oneway') in ['yes','1','true'] or tag.get('junction')=='roundabout'
    ids=w['nodes'];ids=ids[::-1] if tag.get('oneway')=='-1' else ids
    one=one or tag.get('oneway')=='-1'
    try: lanes=float(tag.get('lanes:forward') or tag.get('lanes','2').split(';')[0]); lanes=lanes if one or 'lanes:forward' in tag else max(1,lanes/2)
    except (ValueError,TypeError):lanes=1
    for u,v in zip(ids,ids[1:]):
        if u not in raw or v not in raw or not(inside(raw[u]) and inside(raw[v])):continue
        if u==v:continue
        attr=dict(length=dist(u,v),lanes=min(3,max(1,lanes)),name=tag.get('name',''),highway=h,way_ids=[w['id']],geometry=[[raw[u]['lon'],raw[u]['lat']],[raw[v]['lon'],raw[v]['lat']]],lanes_observed=('lanes' in tag or 'lanes:forward' in tag),speed_mps=30/3.6 if 'link' not in h else 20/3.6)
        g.add_edge(u,v,**attr)
        if not one:
            rev=attr.copy();rev['geometry']=attr['geometry'][::-1];g.add_edge(v,u,**rev)
components=list(nx.strongly_connected_components(g)); keep=max(components,key=len)
g=g.subgraph(keep).copy()
# Collapse only geometry vertices. Every branch, signal and lane/class transition is retained.
ug=g.to_undirected();anchors=set()
for u in g:
    inc=list(g.in_edges(u,data=True))+list(g.out_edges(u,data=True))
    if ug.degree(u)!=2 or raw[u].get('tags',{}).get('highway')=='traffic_signals' or len({(e[2]['lanes'],e[2]['highway']) for e in inc})>1:anchors.add(u)
nodes=[]
for u in sorted(anchors):
    n=raw[u];nodes.append(dict(id=str(u),lon=n['lon'],lat=n['lat'],x=xy(n)[0],y=xy(n)[1],osm_signal=n.get('tags',{}).get('highway')=='traffic_signals'))
edges=[]
for u in sorted(anchors):
    for nxt in g.successors(u):
        path=[u,nxt];prev=u;cur=nxt
        while cur not in anchors:
            choices=[v for v in g.successors(cur) if v!=prev]
            if len(choices)!=1:break
            prev,cur=cur,choices[0];path.append(cur)
            if len(path)>len(g):raise RuntimeError('cycle')
        if cur not in anchors or cur==u:continue
        parts=[g[a][b] for a,b in zip(path,path[1:])];attr=parts[0].copy()
        attr['length']=sum(p['length'] for p in parts)
        attr['geometry']=[p['geometry'][0] for p in parts]+[parts[-1]['geometry'][-1]]
        attr['way_ids']=sorted(set(sum([p['way_ids'] for p in parts],[])))
        edges.append(dict(id=len(edges),u=str(u),v=str(cur),**attr))
network=dict(nodes=nodes,edges=edges,bbox=BBOX,source='© OpenStreetMap contributors, ODbL 1.0',source_url=data.get('source_url'),retrieved='2026-10-29',description='Arterial subnetwork only; residential roads, alleys, service roads, trunk roads and external area excluded. Geometry and one-way tags are OSM observations; operating attributes are assumptions unless flagged.')
(OUT/'network_base.json').write_text(json.dumps(network,ensure_ascii=False,indent=2),encoding='utf-8')
geo=dict(type='FeatureCollection',features=[dict(type='Feature',geometry=dict(type='LineString',coordinates=e['geometry']),properties={k:v for k,v in e.items() if k!='geometry'}) for e in edges])
(OUT/'network_base.geojson').write_text(json.dumps(geo,ensure_ascii=False),encoding='utf-8')
st=dict(raw_arterial_nodes=len(g),nodes=len(nodes),directed_links=len(edges),osm_signal_nodes=sum(n['osm_signal'] for n in nodes),lane_tag_links=sum(e['lanes_observed'] for e in edges),directed_km=sum(e['length'] for e in edges)/1000,names=sorted(set(e['name'] for e in edges)))
(OUT/'network_stats.json').write_text(json.dumps(st,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(st,ensure_ascii=True))
