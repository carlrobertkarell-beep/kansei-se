// Teaching time is independent of prescription, repetitions and clinical readiness.
const clamp=x=>Math.max(0,Math.min(1,x));
export function lessonInstructions(x){
 const texts=v=>Array.isArray(v)?v.filter(s=>typeof s==='string'&&s.trim()).map(s=>s.trim()):[];
 const steps=texts(x.instructions).length?texts(x.instructions):texts(x.steps);
 if(!steps.length){const s=x.instruction||x.cue;if(typeof s==='string'&&s.trim())steps.push(s.trim())}
 const support=x.support||x.equipment,range=x.prescribedRange||x.prescription?.rom;
 return [...new Set([typeof support==='string'&&support.trim()?`Utrustning och stöd: ${support.trim()}`:null,...steps,typeof range==='string'&&range.trim()?`Ditt rörelseomfång: ${range.trim()}`:null].filter(Boolean))];
}
export function lessonSegments(key){
 if(/^sit-to-stand\.|^chair-/.test(key))return [
  {label:'Framåtlutning',from:0,to:.23,seconds:6},
  {label:'Uppresning',from:.23,to:1,seconds:10},
  {label:'Tillbaka till stolen',from:1,to:0,seconds:12}];
 return [{label:'Ut från startläget',from:0,to:1,seconds:10},{label:'Tillbaka till startläget',from:1,to:0,seconds:12}];
}
export function localSwedishVoice(voices=[]){return voices.find(v=>v.localService===true&&/^sv(?:[-_]|$)/i.test(v.lang))||null}
export function createLessonPlayback({draw,change=()=>{},clock=()=>performance.now(),request=cb=>requestAnimationFrame(cb),cancel=id=>cancelAnimationFrame(id)}){
 let segment={from:0,to:1,seconds:10},progress=0,playing=false,slow=false,raf=null,last=0;
 const state=()=>({position:segment.from+(segment.to-segment.from)*(progress*progress*(3-2*progress)),progress,playing,slow,complete:progress>=1});
 function paint(){draw(state().position)}
 function advance(now){if(playing){progress=clamp(progress+Math.max(0,now-last)/(1000*segment.seconds*(slow?1.5:1)));last=now;paint()}}
 function pause(){if(!playing)return;advance(clock());playing=false;cancel(raf);raf=null;change(state())}
 function tick(now){if(!playing)return;advance(now);if(progress>=1){playing=false;raf=null;change(state());return}raf=request(tick)}
 return {state,pause,
  select(next){pause();segment=next;progress=0;paint();change(state())},
  play(){if(playing)return;if(progress>=1)progress=0;playing=true;last=clock();paint();change(state());raf=request(tick)},
  speed(value){if(playing)advance(clock());slow=!!value;change(state())},
  still(position){pause();segment={from:position,to:position,seconds:10};progress=0;paint();change(state())}
 };
}
