"""Run paired-seed experiments and sensitivity checks. Uses stdlib only."""
from simulation import *
from concurrent.futures import ProcessPoolExecutor,as_completed
from dataclasses import replace

def job(args):
    group,scenario,kw=args;c=Config(**kw);r=run(scenario,c,trace=(group=='main' and c.seed==42));r['group']=group;return r

def execute():
    specs=[];seen={}
    def add(group,s,**kw):
        c=asdict(Config(**kw));key=json.dumps([s,c],sort_keys=True)
        if key in seen:return
        seen[key]=True;specs.append((group,s,c))
    for seed in range(40,48):
        for s in SCENARIOS:add('main',s,seed=seed)
    for seed in [42,43,44]:
        for demand in [4500,13500]:
            for s in ['S0','S2','S3']:add('demand_sweep',s,seed=seed,demand=demand)
    for key,values in [('moto_share',[.65,.9]),('moto_pcu',[.2,.5]),('saturation',[1400,2000]),('storage_pcu_per_lane_km',[100,180]),('lost',[8,20])]:
        for value in values:
            for seed in [42,43]:
                for s in ['S0','S3']:add('sensitivity',s,seed=seed,**{key:value})
    for seed in [42,43]:
        for induction in [0,.4]:add('induction', 'S3',seed=seed,induction=induction)
        for s in ['S2','S3']:add('access_count',s,seed=seed,access_count=2)
    for dt in [1,4]:
        for s in ['S0','S2','S3']:add('timestep',s,seed=42,dt=dt)
    for seed in [40,41,43]:
        for s in ['S0','S2','S3']:add('timestep_extra',s,seed=seed,dt=1)
    for s in ['S0','S2','S3']:add('long_drain',s,seed=42,horizon=10800)
    rows=[];t0=time.time();print('RUNS',len(specs),flush=True)
    with ProcessPoolExecutor(max_workers=2) as ex:
        jobs={ex.submit(job,spec):spec for spec in specs}
        for fut in as_completed(jobs):
            r=fut.result();rows.append(r)
            with (HERE/'results.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
            if len(rows)%10==0:print('DONE',len(rows),'/',len(specs),'seconds',round(time.time()-t0,1),flush=True)
    (HERE/'results.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
    print('COMPLETE',len(rows),round(time.time()-t0,1),flush=True)
if __name__=='__main__':
    (HERE/'results.jsonl').write_text('',encoding='utf-8');execute()
