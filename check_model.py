"""Falsifiable implementation checks, not field validation."""
from simulation import *

def tiny(second=False):
    nodes=[dict(id=x,x=i*100.,y=0.,lon=105.8+i*.001,lat=21.,osm_signal=False) for i,x in enumerate(['A','B','C'] if second else ['A','B'])]
    es=[]
    for i in range(len(nodes)-1):
        es.append(dict(id=i,u=nodes[i]['id'],v=nodes[i+1]['id'],length=100.,lanes=1.,speed_mps=10.,capacity_pcu=14.,kind='existing',geometry=[]))
    if second:es[1].update(lanes=.1,capacity_pcu=1.4)
    return dict(nodes=nodes,edges=es,signal_junctions=[],feeders=[],new_nodes=[])

def main():
    checks=[]
    def check(name,ok,evidence):
        checks.append(dict(name=name,pass_=bool(ok),evidence=evidence));assert ok,(name,evidence)
    c=Config(horizon=600,demand_seconds=1,demand=0,saturation=600,dt=1)
    r=run('S0',c,net_override=tiny(),trips_override=[])
    check('Zero demand',r['completed']==0 and r['total_wait_veh_h']==0,r)
    t=[dict(id=str(i),departure=0.,origin='A',destination='B',mode='car',extra=False) for i in range(400)]
    r=run('S0',c,net_override=tiny(),trips_override=t)
    expected=math.floor((600-1e-8-10)/6)+1
    check('Analytical isolated saturated link',r['completed']==expected,dict(expected=expected,completed=r['completed']))
    check('No loss/overflow under overload',r['generated']==r['completed']+r['unfinished'] and r['max_occupancy_ratio']<=1 and r['conservation_error']==0,{k:r[k] for k in ['generated','completed','unfinished','max_occupancy_ratio','conservation_error']})
    t2=[dict(x,destination='C') for x in t]
    r2=run('S0',c,net_override=tiny(True),trips_override=t2)
    check('Finite downstream storage causes spillback',r2['spillback_link_min']>0 and r2['completed']<r['completed'],{k:r2[k] for k in ['completed','spillback_link_min','external_wait_veh_h','inside_end']})
    check('External queue waiting is counted',r2['external_wait_veh_h']>0,r2['external_wait_veh_h'])
    m=[dict(x,mode='moto') for x in t]
    rm=run('S0',c,net_override=tiny(),trips_override=m)
    check('Different mode service and space',rm['completed']>r['completed'],dict(moto=rm['completed'],car=r['completed']))
    check('Crossing movements intersect',intersects((-1,0),(1,0),(0,-1),(0,1)),True)
    check('Opposing right-hand straight paths are disjoint',not intersects((-1,-.16),(1,-.16),(1,.16),(-1,.16)),True)
    base=prepare_network('S0');cfg=Config(demand=250);a,e=make_trips(cfg,base,prepare_network('S2')['feeders']);b,f=make_trips(cfg,base,prepare_network('S3')['feeders'])
    check('Common base demand across scenarios',a==b and e==f,dict(base=len(a),extra=len(e)))
    r1=run('S2',cfg);r2=run('S2',cfg)
    check('Exact reproducibility',r1==r2,dict(seed=cfg.seed,completed=r1['completed']))
    check('Two classes reconcile totals',sum(x['completed'] for x in r1['mode_stats'].values())==r1['completed'],r1['mode_stats'])
    (HERE/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8');print('PASSED',len(checks),'checks')
if __name__=='__main__':main()
