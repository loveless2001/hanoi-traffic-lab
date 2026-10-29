// Run the same daily model as the interactive viewer, without a browser.
const fs=require('fs'),path=require('path'),{Engine,generate}=require('./engine.js');
const settings=JSON.parse(fs.readFileSync(process.argv[2]||path.join(__dirname,'daily_config.json'),'utf8'));
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'ui_data.json'),'utf8')),pop=JSON.parse(fs.readFileSync(path.join(__dirname,'population.json'),'utf8'));
if(settings.profile.length!==24||settings.profile.some(x=>!Number.isFinite(x)||x<0)||settings.profile.reduce((a,b)=>a+b,0)<=0)throw Error('Exactly 24 nonnegative weights with positive sum are required.');
const trips=generate(data,settings,pop),engine=new Engine(data,settings.scenario,trips,{horizon:90000});engine.snapshot();while(engine.step())if(engine.stepNumber%30===0)engine.snapshot();
const result={settings,metrics:engine.metrics(),series:engine.history.map(({ratios,dots,blocked,...m})=>m),toySimulation:true,calibrated:false};fs.writeFileSync(process.argv[3]||path.join(__dirname,'daily_result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result.metrics));
