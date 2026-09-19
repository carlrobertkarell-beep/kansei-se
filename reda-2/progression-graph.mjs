import {prepareCorridor} from './progression-corridor.mjs?v=20260919-1';
const clone=x=>JSON.parse(JSON.stringify(x));
export function graphCorridor(plan,blueprint){
 const base=prepareCorridor(plan);if(!base.valid)return base;
 const nodes=Array.isArray(blueprint?.progressionGraph?.nodes)?blueprint.progressionGraph.nodes:[],edges=Array.isArray(blueprint?.progressionGraph?.edges)?blueprint.progressionGraph.edges:[];
 if(!nodes.length)return {...base,source:'dose'};
 const current=plan.payload.exercises,steps=[{label:'Nuvarande ordination',prescription:clone(current),kind:'current'}];let cursor=blueprint.progressionGraph.start||nodes[0].id,seen=new Set();
 while(cursor&&!seen.has(cursor)&&steps.length<8){seen.add(cursor);const node=nodes.find(n=>n.id===cursor);if(!node)break;const prescription=clone(current).map(x=>{const change=node.exercises?.[x.id];return change?{...x,...change,dose:{...x.dose,...change.dose}}:x});steps.push({label:node.label||cursor,prescription,kind:'blueprint',nodeId:cursor});cursor=edges.find(e=>e.from===cursor&&e.kind!=='regress')?.to||null}
 return {valid:true,steps,source:'blueprint'};
}
export function validateGraph(graph){const nodes=graph?.nodes||[],ids=new Set(nodes.map(n=>n.id));if(!nodes.length||ids.size!==nodes.length)return false;if(graph.start&&!ids.has(graph.start))return false;return (graph.edges||[]).every(e=>ids.has(e.from)&&ids.has(e.to)&&e.from!==e.to)}
