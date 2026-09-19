const safe=n=>Number.isFinite(Number(n))?Number(n):0;
export function regressionDecision({currentStep=0,policy={},recent=[]}={}){
 if(currentStep<=0)return {action:'escalate',code:'regression_floor',reason:'Patienten är redan på första godkända steget.'};
 const window=Math.max(1,safe(policy.regressionWindow)||2),rows=recent.slice(0,window);
 if(rows.length<window)return {action:'hold',code:'regression_evidence',reason:'Mer uppföljning behövs innan regression.'};
 const worse=rows.filter(x=>x.nextDay==='worse'||x.function==='worse').length,heavy=rows.filter(x=>x.effort==='heavy').length;
 const symptom=rows.some(x=>x.changedSymptoms===true),help=rows.some(x=>x.requestedHelp===true);
 if(symptom||help)return {action:'escalate',code:symptom?'changed_symptoms':'requested_help',reason:'Ny patientsignal ligger utanför automatisk regression.'};
 const need=Math.max(1,safe(policy.regressionSignals)||2);
 if(worse+heavy>=need)return {action:'regress',code:'load_response',toStep:currentStep-1,reason:'Fördefinierade belastningssignaler uppfyller regressionsvillkoren.'};
 return {action:'hold',code:'stable_or_unclear',reason:'Ingen automatisk regression behövs utifrån registrerat underlag.'};
}
export function regressionTarget(frame,decision){if(decision?.action!=='regress')return null;const steps=frame?.steps||[];const target=steps[decision.toStep];return target?.prescription?target:null}
