export const fleetLabels={autonomous:'EI autonomt',evidence:'Samlar evidens',held:'EI avvaktar',review:'Behöver dig',shadow:'Granskningsläge',unmanaged:'Utan EI-ram'};
export function fleetState(row){
 if(row?.needs_review||Number(row?.open_count||0)>0||row?.new_reply)return 'review';
 if(row?.frame_status==='approved'&&row?.frame_execution==='automatic'){
  if(row?.decision_action==='hold'||['load','recovery','partial','effort','difficult'].includes(row?.decision_code))return 'held';
  if(row?.decision_action==='review'||row?.decision_action==='blocked')return 'review';
  return 'autonomous';
 }
 if(row?.frame_status==='approved')return 'shadow';
 if(row?.plan_id)return 'evidence';
 return 'unmanaged';
}
export function fleetCounts(rows=[]){const c={autonomous:0,evidence:0,held:0,review:0,shadow:0,unmanaged:0,total:rows.length};for(const r of rows)c[fleetState(r)]++;return c}
