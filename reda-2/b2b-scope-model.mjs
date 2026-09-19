export function b2bScopeOptions(org,units=[]){return [{id:'all',label:org?.name||'Hela organisationen',kind:'organization'},...units.filter(x=>x.status==='active').map(x=>({id:x.id,label:x.name,kind:'unit'}))]}
export function b2bBreadcrumb(org,unit,clinician){return [org?.name,unit?.name,clinician?.display_name].filter(Boolean).join(' / ')}
