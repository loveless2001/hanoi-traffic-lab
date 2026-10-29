from pathlib import Path
import sys,json,math
P=Path(sys.argv[sys.argv.index('--model-dir')+1]).resolve() if '--model-dir' in sys.argv else Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from simulation import *
base=prepare_network('S0');net=prepare_network('S2');ps=portals(base);feeders=net['feeders'];origins=ps+[x for x in feeders if x not in ps]
ns={n['id']:n for n in base['nodes']}
alltrips=[]
for o in origins:
 for d in ps:
  if o!=d and math.hypot(ns[o]['x']-ns[d]['x'],ns[o]['y']-ns[d]['y'])>=1000:
   for m in ['moto','car']:alltrips.append(dict(origin=o,destination=d,mode=m))
payload=dict(portals=ps,feeders=feeders,routebooks={},networks={},source='© OpenStreetMap contributors',bbox=base['bbox'])
for s in ['S0','S1','S2']:
 n=prepare_network(s);paths=route_trips(n,alltrips,Config())
 payload['routebooks'][s]=[[t['origin'],t['destination'],0 if t['mode']=='moto' else 1,p] for t,p in zip(alltrips,paths)]
 nn=n['nodes'] if s=='S0' else n['nodes'][len(base['nodes']):]
 ee=n['edges'] if s=='S0' else n['edges'][len(base['edges']):]
 payload['networks'][s]=dict(nodes=[[x['id'],x['lon'],x['lat'],x['x'],x['y']] for x in nn],edges=[[e['u'],e['v'],e['length'],e['lanes'],e['speed_mps'],e['capacity_pcu'],e['kind'],e['geometry'],e['name']] for e in ee],signals=n['signal_junctions'])
(P/'ui_data.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
# Exact high precision reference fixture is kept outside the inline visualization.
if '--data-only' in sys.argv:print('ui payload bytes',(P/'ui_data.json').stat().st_size);sys.exit(0)
fixtures={}
for s in ['S0','S2','S3']:
 n=prepare_network(s);a,e=make_trips(Config(),base,n['feeders']);ts=sorted(a+(e if s=='S3' else []),key=lambda t:t['departure'])
 fixtures[s]=dict(trips=ts,expected=run(s,Config()))
(P/'reference_fixtures.json').write_text(json.dumps(fixtures,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('ui payload bytes',(P/'ui_data.json').stat().st_size)
