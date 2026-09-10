/* Session transitions: explicit rounds, no automatic completion or dose changes. */
(function(root){'use strict';
function rounds(x){const sides=x.side==='both'?['left','right']:[x.side||'simultaneous'];return Array.from({length:Number(x.dose?.sets||1)},(_,set)=>sides.map(side=>({set:set+1,side}))).flat()}
function create(xs,id,now){return {id,startedAt:now,status:'started',completedAt:null,progress:xs.map(x=>({exerciseId:x.id,status:'pending',roundsDone:0,totalRounds:rounds(x).length,feedback:null}))}}
function mark(s,index,round){const n=JSON.parse(JSON.stringify(s)),p=n.progress[index];if(n.completedAt)throw Error('Passet är avslutat');if(round!==p.roundsDone||round>=p.totalRounds)throw Error('Markera en omgång i taget');p.roundsDone++;p.status=p.roundsDone===p.totalRounds?'completed':'partial';n.status='partial';return n}
function summary(rows){const completed=rows.filter(x=>x.status==='completed').length,partial=rows.filter(x=>['partial','started'].includes(x.status)).length;const issues={};for(const r of rows)for(const x of r.payload?.exercises||[])if(x.feedback==='heavy'||x.status==='skipped'){const key=x.exerciseId;issues[key]=(issues[key]||0)+1}return {completed,partial,issues}}
root.RedaSession={rounds,create,mark,summary};
})(typeof window!=='undefined'?window:globalThis);
