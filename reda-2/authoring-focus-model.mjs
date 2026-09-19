export function authoringFocus(plan,{candidate=false,status=''}={}){
 const count=plan?.exercises?.length||0,warnings=plan?.warnings?.length||0;
 if(candidate)return {phase:'choose',title:'Välj ett upplägg att granska',detail:'Inget förslag används förrän du väljer det.'};
 if(!count)return {phase:'build',title:'Skapa kärnan i planen',detail:'Välj snabbstart, EI-förslag eller lägg till övningar.'};
 if(warnings)return {phase:'fix',title:'Komplettera '+warnings+' markerad'+(warnings===1?' uppgift':'e uppgifter'),detail:'Planen sparas inte som färdig förrän markeringarna är lösta.'};
 return {phase:'review',title:'Finjustera och granska',detail:count+' övningar · ändra bara det som behöver ändras.'};
}
