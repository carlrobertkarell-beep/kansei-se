const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function firstSteps(state){
 const sessions=(state.sessions||[]).filter(s=>s.plan_id===state.plan.id&&s.status!=='planned_rest');
 const ended=sessions.filter(s=>s.completed_at);
 const replied=(state.reflections||[]).some(r=>ended.some(s=>s.id===r.session_id));
 return [{label:'Din plan är tillgänglig',done:true},{label:ended.length?'Första passet avslutat':sessions.length?'Fortsätt ditt första pass':'Starta ditt första pass',done:ended.length>0},{label:'Berätta hur passet fungerade',done:replied}];
}
export function startHTML(state,message=''){
 const steps=firstSteps(state);if(steps.every(s=>s.done)&&!message)return '';
 return '<div class="patient-start"><h3>'+esc(state.plan.version>1?'Din aktuella plan · v'+state.plan.version:'Välkommen till din plan')+'</h3>'+(message?'<p>'+esc(message)+'</p>':'')+'<ol>'+steps.map(s=>'<li>'+(s.done?'✓ ':'')+esc(s.label)+'</li>').join('')+'</ol><p>Du kan pausa ett pass och fortsätta senare. Om något är oklart finns hjälp vid varje övning.</p></div>';
}
