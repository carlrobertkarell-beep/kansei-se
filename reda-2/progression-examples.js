/* Fictional fixtures for interactive review and regression tests. Not patient protocols. */
(function(root){'use strict';
const profiles={
 daily:{name:'Vardagsfunktion',title:'Orka en längre promenad.',description:'Behov av stöd och tydlig guidning. Målet är en lättare vardag; åldern väljer inte träningsnivån.',options:{blueprintId:'knee_oa',capacity:'supported',stage:'protected',trainingHistory:'new',goalProfile:'daily',equipment:'home',guidance:'guided'}},
 hyrox:{name:'Hyrox',title:'Tillbaka till löpning och stationer.',description:'Hög träningsvana. Belastningen från löpning, styrka och stationsträning behöver vägas ihop. Detta visar en del av rehaben, inte ett komplett Hyroxprogram.',options:{blueprintId:'knee_pf',capacity:'high',stage:'higher',trainingHistory:'rehab_experienced',goalProfile:'hyrox',equipment:'gym',guidance:'trained'}},
 strength:{name:'Avancerad styrka',title:'Bygga vidare på hög kapacitet.',description:'En träningsvan person behöver en relevant utmaning och utrymme för återhämtning. Ett högt utgångsläge är inte i sig ett skäl att öka.',options:{blueprintId:'knee_pf',capacity:'high',stage:'build',trainingHistory:'rehab_experienced',goalProfile:'strength',equipment:'gym',guidance:'trained'}}
};
function example(key){const profile=profiles[key];if(!profile)throw Error('Okänt exempel');const P=root.RedaPlanner,E=root.RedaProgression,base=P.buildProgram({...profile.options,floorOK:true,band:true,goal:profile.title});const index=base.exercises.findIndex(x=>!x.dose.hold),start=base.exercises[index].dose.reps;
 const steps=[0,2,4].map((add,i)=>{const plan=add?P.editExercise(base,index,{reps:start+add}):base;return {id:'step-'+i,label:i===0?'Utgångspunkt':i===1?'Nästa fördefinierade steg':'Sista steget i ramen',plan}});
 const policy=E.compile({id:'fictional-'+key,revision:1,validFrom:'2026-09-01',validUntil:'2026-11-01',rules:{minSuccessfulDays:3,minDaysAtStep:7,maxEvidenceAgeDays:14,acceptedEffort:['easy','okay']},steps});
 return {profile,policy,index,plan:base,state:{stepId:'step-0',policyRevision:1,startedAt:'2026-09-01T08:00:00Z'},now:'2026-09-10T12:00:00Z'};
}
function scenario(model,key){const plus=(n,h=10)=>new Date(Date.parse(model.state.startedAt)+n*86400000).toISOString().slice(0,10)+'T'+h+':00:00Z';const context={sessionOpen:false,concern:false,reviewRequested:false,environmentChanged:false,otherTraining:'usual',recovery:'ready'},rows=[1,3,5].map((n,i)=>({id:model.state.stepId+'-session-'+i,policyId:model.policy.id,policyRevision:1,stepId:model.state.stepId,completedAt:plus(n),respondedAt:plus(n+1),status:'completed',effort:'okay',quality:'controlled',function:'stable',nextDay:'settled',concern:false}));
 if(key==='missing')rows[2].nextDay='unknown';
 if(key==='single')rows.splice(1);
 if(key==='heavy')rows[2].effort='heavy';
 if(key==='worse')rows[2].nextDay='worse';
 if(key==='load')context.otherTraining='high';
 if(key==='low')context.recovery='low';
 if(key==='open')context.sessionOpen=true;
 return {policy:model.policy,plan:model.plan,state:model.state,now:model.now,observations:rows,context};
}
root.RedaProgressionExamples={profiles,example,scenario};
})(typeof window!=='undefined'?window:globalThis);
