const num=(v,min,max)=>{const n=Number(v);return Number.isFinite(n)?Math.max(min,Math.min(max,Math.round(n))):null};
export function quickDoseChange(exercise,action){
 const d=exercise?.dose||{};switch(action){
  case 'sets-down':{const n=num(d.sets,1,8);return n&&n>1?{sets:n-1}:null}
  case 'sets-up':{const n=num(d.sets,1,8);return n&&n<8?{sets:n+1}:null}
  case 'reps-down':{const n=num(d.reps,1,100);return n&&n>1?{reps:Math.max(1,n-(n>10?2:1))}:null}
  case 'reps-up':{const n=num(d.reps,1,100);return n&&n<100?{reps:Math.min(100,n+(n>=10?2:1))}:null}
  default:return null;
 }
}
export function quickSideChoices(allowed,current){return (allowed||[]).filter(x=>x!==current)}
export function quickVariantChoices(alternatives,current){return (alternatives||[]).filter(x=>x?.id&&x.id!==current).map(x=>({id:x.id,name:x.name||x.id}))}
