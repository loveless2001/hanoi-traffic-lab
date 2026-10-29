/* Bundled after engine.js/editor.js into a Blob worker by build_site.py. */
self.onmessage=async function(event){const {data,pop,design,options}=event.data;try{
 const H=self.HanoiEngine,E=self.HanoiEditor,start=performance.now(),trips=H.generate(data,options,pop),fingerprint=E.fingerprint(trips),nets=[E.buildNetwork(data,{lines:[],autoConnect:true,bbox:data.bbox}),E.buildNetwork(data,design)];self.postMessage({type:'progress',t:0,stage:'Đang tính đường đi'});
 const paths=nets.map(net=>E.routeTrips(net,trips)),engines=nets.map((net,i)=>new H.Engine(data,'CUSTOM',trips,{networkOverride:net,pathsOverride:paths[i],horizon:90000}));engines.forEach(e=>e.snapshot());
 while(engines[0].t<90000){for(let j=0;j<300&&engines[0].t<90000;j++){engines[0].step();engines[1].step();if(engines[0].stepNumber%30===0)engines.forEach(e=>e.snapshot());}self.postMessage({type:'progress',t:engines[0].t,completed:engines.map(e=>e.completed)});}
 const metrics=engines.map(e=>e.metrics()),same=engines[0].trips===engines[1].trips;if(!same||metrics.some(m=>m.conservation_error!==0)||metrics[0].generated!==metrics[1].generated)throw Error('Không đạt kiểm tra cùng nhu cầu hoặc bảo toàn xe.');
 self.postMessage({type:'done',histories:engines.map(e=>e.history),metrics,pairedSameDemand:same,fingerprint,tripCount:trips.length,usingNewRoad:paths[1].filter(p=>p.some(i=>nets[1].edges[i][6]!=='existing')).length,movementCounts:engines.map(e=>e.movements.size),seconds:(performance.now()-start)/1000});
 }catch(error){self.postMessage({type:'error',message:error.message});}};
