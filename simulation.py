"""Hanoi arterial mechanism experiment. Standard-library-only runtime.

This is NOT a calibrated Hanoi forecast. Read README.txt and report.html.
All generated trips remain accounted for, including external queues and censoring.
"""
from __future__ import annotations
from collections import deque, defaultdict
from pathlib import Path
from dataclasses import dataclass, asdict
import math, json, random, heapq, copy, argparse, statistics, time

HERE=Path(__file__).resolve().parent
SCENARIOS=['S0','S1','S2','S3','S4']
LABELS={'S0':'Hiện trạng mô hình','S1':'Đường mới, 2 đầu nối','S2':'Đường mới + 4 nhánh','S3':'4 nhánh + nhu cầu tăng 20%','S4':'S3 + điều tiết truy nhập'}

@dataclass
class Config:
    dt:float=2.0
    demand_seconds:int=3600
    horizon:int=5400
    demand:int=9000
    moto_share:float=.80
    moto_pcu:float=.35
    saturation:float=1700
    storage_pcu_per_lane_km:float=140
    cycle:float=90
    lost:float=14
    induction:float=.20
    access_count:int=4
    meter_threshold:float=.65
    seed:int=42

def unit(a):
    d=math.hypot(*a);return (a[0]/d,a[1]/d) if d else (1.,0.)
def right(a):return (a[1],-a[0])
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def sub(a,b):return(a[0]-b[0],a[1]-b[1])
def intersects(a,b,c,d):
    return cross(sub(b,a),sub(c,a))*cross(sub(b,a),sub(d,a)) < -1e-8 and cross(sub(d,c),sub(a,c))*cross(sub(d,c),sub(b,c)) < -1e-8

def prepare_network(scenario='S0',cfg=None):
    cfg=cfg or Config();net=json.loads((HERE/'network_base.json').read_text(encoding='utf-8'))
    ns={n['id']:n for n in net['nodes']};es=net['edges'];neigh=defaultdict(set)
    for e in es:neigh[e['u']].add(e['v']);neigh[e['v']].add(e['u'])
    junctions=[u for u in ns if len(neigh[u])>=3]
    # Map OSM approach signals onto their nearest topological junction. This is
    # an inference, not an observed controller inventory or a surveyed junction count.
    signaled=set()
    for n in ns.values():
        if n['osm_signal'] and junctions:
            u=min(junctions,key=lambda u:math.hypot(ns[u]['x']-n['x'],ns[u]['y']-n['y']))
            if math.hypot(ns[u]['x']-n['x'],ns[u]['y']-n['y'])<=80:signaled.add(u)
    new_nodes=[];feeders=[]
    if scenario!='S0':
        def nearest(lon,lat,exclude=()):return min((u for u in junctions if u not in exclude),key=lambda u:((ns[u]['lon']-lon)*math.cos(math.radians(lat)))**2+(ns[u]['lat']-lat)**2)
        a=nearest(105.8065,21.0270);b=nearest(105.8245,21.0175)
        chain=[a]
        for i in range(1,5):
            z=i/5;u=f'NEW{i}';n=dict(id=u,x=ns[a]['x']*(1-z)+ns[b]['x']*z,y=ns[a]['y']*(1-z)+ns[b]['y']*z,lon=ns[a]['lon']*(1-z)+ns[b]['lon']*z,lat=ns[a]['lat']*(1-z)+ns[b]['lat']*z,osm_signal=False)
            ns[u]=n;new_nodes.append(u);chain.append(u)
        chain.append(b)
        def add(u,v,kind,lanes):
            e=dict(id=len(es),u=u,v=v,length=math.hypot(ns[u]['x']-ns[v]['x'],ns[u]['y']-ns[v]['y']),lanes=lanes,name=kind,highway='hypothetical',way_ids=[],lanes_observed=False,speed_mps=40/3.6 if kind=='new_road' else 20/3.6,geometry=[[ns[u]['lon'],ns[u]['lat']],[ns[v]['lon'],ns[v]['lat']]],kind=kind)
            es.append(e)
        for u,v in zip(chain,chain[1:]):add(u,v,'new_road',2);add(v,u,'new_road',2)
        if scenario in ['S2','S3','S4']:
            used={a,b}
            for u in new_nodes[:cfg.access_count]:
                # Short explicit connector to an existing graph junction. No new
                # demand is attached in S2; only route opportunities and conflicts.
                v=min((v for v in junctions if v not in used),key=lambda v:math.hypot(ns[v]['x']-ns[u]['x'],ns[v]['y']-ns[u]['y']))
                used.add(v);feeders.append(v);add(v,u,'access',1);add(u,v,'access',1)
        signaled.update([a,b])
    for e in es:
        e.setdefault('kind','existing')
        e['capacity_pcu']=max(1.1,e['length']/1000*e['lanes']*cfg.storage_pcu_per_lane_km)
    net['nodes']=list(ns.values());net['signal_junctions']=sorted(signaled);net['feeders']=feeders
    net['new_nodes']=new_nodes
    return net

def portals(net):
    ns={n['id']:n for n in net['nodes'] if not n['id'].startswith('NEW')};used=[]
    # Twenty spatial targets, not population-weighted zones. Repeated target
    # matches are removed; all scenarios use the S0 portal inventory.
    for ix in range(5):
        for iy in range(4):
            x=-1500+ix*750;y=-1100+iy*730
            u=min(ns,key=lambda u:math.hypot(ns[u]['x']-x,ns[u]['y']-y))
            if u not in used:used.append(u)
    return used

def make_trips(cfg,base_net,extra_origins=()):
    ns={n['id']:n for n in base_net['nodes']};ps=portals(base_net);rng=random.Random(cfg.seed)
    def draw(n,origins,extra=False):
        rows=[]
        for i in range(n):
            # Broad peak: triangular arrival density; exact N is held fixed.
            t=rng.triangular(0,cfg.demand_seconds,cfg.demand_seconds/2)
            o=rng.choice(origins)
            ds=[d for d in ps if math.hypot(ns[d]['x']-ns[o]['x'],ns[d]['y']-ns[o]['y'])>=1000]
            if not ds:raise ValueError('No destination at least 1 km away')
            d=rng.choice(ds);m='moto' if rng.random()<cfg.moto_share else 'car'
            rows.append(dict(id=('I' if extra else 'B')+str(i),departure=t,origin=o,destination=d,mode=m,extra=extra))
        return rows
    base=draw(cfg.demand,ps)
    # A separate random stream preserves all base departures, ODs and modes.
    rng=random.Random(cfg.seed+1000003)
    ext=draw(round(cfg.demand*cfg.induction),list(extra_origins) or ps,True)
    return sorted(base,key=lambda x:x['departure']),sorted(ext,key=lambda x:x['departure'])

def route_trips(net,trips,cfg):
    ns={n['id']:n for n in net['nodes']};adj=defaultdict(list);signals=set(net['signal_junctions']);routes={}
    for e in net['edges']:adj[e['u']].append(e)
    for origin in sorted(set(t['origin'] for t in trips)):
        for mode in ['moto','car']:
            dist={origin:0};prev={};heap=[(0,origin)]
            while heap:
                c,u=heapq.heappop(heap)
                if c!=dist[u]:continue
                for e in adj[u]:
                    speed=e['speed_mps']*(1.08 if mode=='moto' else 1.)
                    # Same generalized free-flow rule in every scenario. No
                    # post-hoc assignment tuning and no equilibrium claim.
                    red=(cfg.cycle+cfg.lost)/2
                    delay=red*red/(2*cfg.cycle) if e['v'] in signals else 0
                    z=c+e['length']/speed+delay
                    if z<dist.get(e['v'],math.inf):dist[e['v']]=z;prev[e['v']]=(u,e['id']);heapq.heappush(heap,(z,e['v']))
            for dst in set(t['destination'] for t in trips if t['origin']==origin):
                path=[];u=dst
                while u!=origin:
                    if u not in prev:raise ValueError(f'Unroutable {origin}->{dst}')
                    u,e=prev[u];path.append(e)
                routes[(origin,dst,mode)]=path[::-1]
    return [routes[(t['origin'],t['destination'],t['mode'])] for t in trips]

def run(scenario='S0',cfg=None,trace=False,trips_override=None,net_override=None):
    cfg=cfg or Config();net=net_override or prepare_network(scenario,cfg);es=net['edges'];ns={n['id']:n for n in net['nodes']};M=len(es)
    assert cfg.horizon>=cfg.demand_seconds and cfg.dt>0 and 0<=cfg.lost<cfg.cycle
    if trips_override is None:
        base,extra=make_trips(cfg,prepare_network('S0',cfg),net['feeders']);trips=sorted(base+(extra if scenario in ['S3','S4'] else []),key=lambda x:x['departure'])
    else:trips=copy.deepcopy(trips_override)
    paths=route_trips(net,trips,cfg);N=len(trips);Q=[deque() for e in es];occ=[0.]*M;inbound=defaultdict(list)
    for e in es:inbound[e['v']].append(e['id'])
    # Movement geometry and conflict graph are rebuilt from actual scenario edges.
    movements={};atnode=defaultdict(list)
    for p in paths:
        for i,e in enumerate(p):
            f=p[i+1] if i+1<len(p) else -1
            if (e,f) in movements:continue
            E=es[e];u=ns[E['u']];v=ns[E['v']];vin=unit((v['x']-u['x'],v['y']-u['y']));ri=right(vin)
            a=(-vin[0]+.16*ri[0],-vin[1]+.16*ri[1]);turn='exit';factor=1.
            if f>=0:
                w=ns[es[f]['v']];vo=unit((w['x']-v['x'],w['y']-v['y']));ro=right(vo);b=(vo[0]+.16*ro[0],vo[1]+.16*ro[1]);ang=math.degrees(math.atan2(cross(vin,vo),sum(x*y for x,y in zip(vin,vo))))
                turn='straight' if abs(ang)<35 else 'left' if ang>0 else 'right';factor=1 if turn=='straight' else 1.25 if turn=='right' else 1.5
            else:b=a
            movements[e,f]=dict(a=a,b=b,turn=turn,factor=factor,axis=0 if abs(vin[0])>=abs(vin[1]) else 1)
            atnode[E['v']].append((e,f))
    conflicts={m:[] for m in movements}
    for node,ms in atnode.items():
        for m in ms:
            for other in ms:
                if m==other or m[0]==other[0] or (m[1]>=0 and m[1]==other[1]) or (m[1]>=0 and other[1]>=0 and intersects(movements[m]['a'],movements[m]['b'],movements[other]['a'],movements[other]['b'])):conflicts[m].append(other)
    # Absolute next service times prevent saving unused green capacity.
    available=defaultdict(float);last_depart=[0.]*M;signals=set(net['signal_junctions'])
    ready=[0.]*N;pos=[0]*N;entered=[None]*N;completed=[None]*N;travelled=[0.]*N;individual_wait=[0.]*N
    pcu=[cfg.moto_pcu if t['mode']=='moto' else 1. for t in trips]
    external=defaultdict(deque);generated=0;completed_n=0;external_count=0;inside_count=0
    external_area=0.;internal_wait_area=0.;spill_area=0.;full_area=0.;max_occ_ratio=0.;series=[];last_c=0;peak_external=0;max_conservation=0
    base_complete=0;link_transfers=0;turn_transfers=defaultdict(int);peak_queue=0;used_new=0
    def green_time(t,node,axis):
        if node not in signals:return t
        offset=(sum(ord(c) for c in str(node))*7)%int(cfg.cycle)
        z=(t+offset)%cfg.cycle;g=(cfg.cycle-cfg.lost)/2
        lo=axis*cfg.cycle/2;hi=lo+g
        if lo<=z<hi-1e-9:return t
        return t+(lo-z if z<lo else cfg.cycle-z+lo)
    def add_to_link(i,e,t):
        Q[e].append(i);occ[e]+=pcu[i]
        speed=es[e]['speed_mps']*(1.08 if trips[i]['mode']=='moto' else 1.)
        ready[i]=t+es[e]['length']/speed
        travelled[i]+=es[e]['length']/speed
    steps=int(math.ceil(cfg.horizon/cfg.dt))
    nodes_order=sorted(inbound)
    for step in range(steps):
        start=step*cfg.dt;end=min(cfg.horizon,start+cfg.dt)
        # Departures become eligible at the actual release time within this step.
        while generated<N and trips[generated]['departure']<end-1e-9:
            t=trips[generated];external[t['origin']].append(generated);generated+=1;external_count+=1
        peak_external=max(peak_external,external_count)
        # External queues are physical pending requests. No vehicle is dropped.
        for o in sorted(external):
            q=external[o]
            while q:
                i=q[0];e=paths[i][0]
                if scenario=='S4' and o in net['feeders'] and occ[e]/es[e]['capacity_pcu']>=cfg.meter_threshold:break
                if occ[e]+pcu[i]>es[e]['capacity_pcu']+1e-8:break
                q.popleft();external_count-=1;inside_count+=1;entered[i]=max(start,trips[i]['departure']);add_to_link(i,e,entered[i])
        blocked=set()
        # Alternating node order reduces deterministic within-step ordering bias.
        order=nodes_order if step%2==0 else reversed(nodes_order)
        for node in order:
            inc=inbound[node]
            while True:
                candidates=[]
                for e in inc:
                    if not Q[e]:continue
                    i=Q[e][0];p=paths[i];j=pos[i];f=p[j+1] if j+1<len(p) else -1;m=(e,f)
                    service=max(start,ready[i],last_depart[e],available[m])
                    if f>=0:service=green_time(service,node,movements[m]['axis'])
                    if service>=end-1e-9:continue
                    if f>=0 and occ[f]+pcu[i]>es[f]['capacity_pcu']+1e-8:
                        blocked.add(e);continue
                    if scenario=='S4' and es[e]['kind']=='access' and f>=0 and occ[f]/es[f]['capacity_pcu']>=cfg.meter_threshold:
                        continue
                    candidates.append((service,(e+step)%max(M,1),e,f,i,m))
                if not candidates:break
                service,_,e,f,i,m=min(candidates);Q[e].popleft();occ[e]-=pcu[i]
                individual_wait[i]+=max(0,service-ready[i])
                h=3600*pcu[i]/(cfg.saturation*es[e]['lanes'])*movements[m]['factor']
                last_depart[e]=service+h
                for other in conflicts[m]:available[other]=max(available[other],service+h)
                link_transfers+=1;turn_transfers[movements[m]['turn']]+=1
                if f<0:
                    completed[i]=service;completed_n+=1;inside_count-=1;base_complete+=not trips[i]['extra']
                else:
                    pos[i]+=1;add_to_link(i,f,service)
                    if es[f]['kind']=='new_road':used_new+=1
        # Snapshots are used for visualization, never to discard censored trips.
        waiting=sum(sum(ready[i]<=end for i in q) for q in Q)
        internal_wait_area+=waiting*(end-start);spill_area+=len(blocked)*(end-start)
        full=sum(occ[e]/es[e]['capacity_pcu']>=.95 for e in range(M));full_area+=full*(end-start)
        peak_queue=max(peak_queue,waiting)
        max_occ_ratio=max(max_occ_ratio,max((occ[e]/es[e]['capacity_pcu'] for e in range(M)),default=0))
        max_conservation=max(max_conservation,abs(generated-completed_n-external_count-inside_count))
        if trace and (step+1)%max(1,round(60/cfg.dt))==0:
            series.append(dict(t=end,generated=generated,completed=completed_n,inside=inside_count,external=external_count,waiting=waiting,blocked_links=len(blocked),full_links=full,completed_last_min=completed_n-last_c));last_c=completed_n
    done=[i for i,c in enumerate(completed) if c is not None]
    for q in Q:
        for i in q:individual_wait[i]+=max(0,cfg.horizon-ready[i])
    internal_wait_area=sum(individual_wait)
    external_area=sum((entered[i] if entered[i] is not None else cfg.horizon)-t['departure'] for i,t in enumerate(trips))
    delays=[max(0,completed[i]-trips[i]['departure']-travelled[i]) for i in done]
    def qtile(a,q):
        if not a:return None
        a=sorted(a);z=(len(a)-1)*q;i=int(z);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(z-i)
    mode_stats={}
    for mode in ['moto','car']:
        ids=[i for i in range(N) if trips[i]['mode']==mode];ds=[i for i in ids if completed[i] is not None]
        mode_stats[mode]=dict(generated=len(ids),completed=len(ds),unfinished=len(ids)-len(ds),mean_completed_trip_s=statistics.mean(completed[i]-trips[i]['departure'] for i in ds) if ds else None,total_wait_veh_h=sum(individual_wait[i]+(entered[i] if entered[i] is not None else cfg.horizon)-trips[i]['departure'] for i in ids)/3600)
    end_to_end=sum((completed[i] if completed[i] is not None else cfg.horizon)-t['departure'] for i,t in enumerate(trips))
    result=dict(scenario=scenario,seed=cfg.seed,config=asdict(cfg),generated=generated,completed=completed_n,base_completed=base_complete,completion_pct=100*completed_n/generated if generated else 100.,throughput_veh_h=completed_n/(cfg.horizon/3600),external_end=external_count,inside_end=inside_count,unfinished=external_count+inside_count,total_wait_veh_h=(external_area+internal_wait_area)/3600,external_wait_veh_h=external_area/3600,internal_wait_veh_h=internal_wait_area/3600,wait_per_generated_s=(external_area+internal_wait_area)/generated if generated else 0,mean_completed_delay_s=statistics.mean(delays) if delays else None,p95_completed_delay_s=qtile(delays,.95),total_observed_time_veh_h=end_to_end/3600,spillback_link_min=spill_area/60,spillback_pct=100*spill_area/(M*cfg.horizon),full_storage_link_min=full_area/60,peak_external=peak_external,peak_waiting=peak_queue,max_occupancy_ratio=max_occ_ratio,conservation_error=max_conservation,link_transfers=link_transfers,turn_transfers=dict(turn_transfers),new_link_entries=used_new,mode_stats=mode_stats,links=M,nodes=len(ns),signal_junctions=len(signals),movement_count=len(movements),conflicting_pairs=sum(map(len,conflicts.values()))//2)
    if trace:result['series']=series
    assert max_conservation==0
    assert min(occ,default=0)>-1e-6 and max_occ_ratio<=1+1e-6
    assert generated==completed_n+inside_count+external_count
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--scenario',choices=SCENARIOS,default='S0');p.add_argument('--seed',type=int,default=42);p.add_argument('--demand',type=int,default=9000);p.add_argument('--dt',type=float,default=2);p.add_argument('--trace',action='store_true');p.add_argument('--out',default='one_run.json');a=p.parse_args()
    c=Config(seed=a.seed,demand=a.demand,dt=a.dt);t=time.time();r=run(a.scenario,c,a.trace);(HERE/a.out).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:r[k] for k in ['scenario','generated','completed','unfinished','total_wait_veh_h','spillback_link_min','new_link_entries']}));print('seconds',round(time.time()-t,2))
