/* Session transitions: explicit rounds, no automatic completion or dose changes. */
(function(root){'use strict';
function rounds(x){const sides=x.side==='both'?['left','right']:[x.side||'simultaneous'];return Array.from({length:Number(x.dose?.sets||1)},(_,set)=>sides.map(side=>({set:set+1,side}))).flat()}
function create(xs,id,now){return {id,startedAt:now,status:'started',completedAt:null,progress:xs.map(x=>({exerciseId:x.id,status:'pending',roundsDone:0,totalRounds:rounds(x).length,feedback:null}))}}
function open(s){if(!s||!Array.isArray(s.progress))throw Error('Passet kunde inte läsas');if(s.completedAt!=null||!['started','partial'].includes(s.status))throw Error('Passet är avslutat')}
function row(s,index){open(s);if(!Number.isInteger(index)||index<0||index>=s.progress.length)throw Error('Övningen kunde inte hittas');return s.progress[index]}
function copy(s){return JSON.parse(JSON.stringify(s))}
function mark(s,index,round){const p=row(s,index);if(p.status==='skipped')throw Error('Återuppta övningen först');if(!Number.isInteger(round)||round!==p.roundsDone||round<0||round>=p.totalRounds)throw Error('Markera en omgång i taget');const n=copy(s),next=n.progress[index];next.roundsDone++;next.status=next.roundsDone===next.totalRounds?'completed':'partial';n.status='partial';return n}
function undo(s,index){const p=row(s,index);if(p.roundsDone<=0)throw Error('Det finns ingen omgång att ångra');const n=copy(s),next=n.progress[index];next.roundsDone--;next.status=next.roundsDone>0?'partial':'pending';next.feedback=null;n.status='partial';return n}
function skip(s,index){const p=row(s,index);if(p.status==='completed'||p.roundsDone>=p.totalRounds)throw Error('Övningen är redan klar');const n=copy(s),next=n.progress[index];next.status='skipped';if(next.roundsDone===0)next.feedback=null;n.status='partial';return n}
function resume(s,index){const p=row(s,index);if(p.status!=='skipped')throw Error('Övningen är inte överhoppad');const n=copy(s),next=n.progress[index];next.status=next.roundsDone>0?'partial':'pending';n.status='partial';return n}
function finish(s,now){open(s);if(typeof now!=='string'||!now.trim())throw Error('Ange när passet avslutades');const n=copy(s);n.status=n.progress.every(p=>p.status==='completed')?'completed':'partial';n.completedAt=now;return n}
function summary(rows){const completed=rows.filter(x=>x.status==='completed').length,partial=rows.filter(x=>['partial','started'].includes(x.status)).length;const issues={};for(const r of rows)for(const x of r.payload?.exercises||[])if(x.feedback==='heavy'||x.status==='skipped'){const key=x.exerciseId;issues[key]=(issues[key]||0)+1}return {completed,partial,issues}}
root.RedaSession={rounds,create,mark,undo,skip,resume,finish,summary};
})(typeof window!=='undefined'?window:globalThis);
