import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
// No network or real credentials. Delay authentication to exercise the moment
// where a workspace can change before the database request has actually started.
test('pending clinical requests retain the workspace where they were started',async()=>{
 const writes=[],reads=[];let release;
 const auth={getUser:()=>new Promise(r=>release=()=>r({data:{user:{id:'fictional-staff'}}})),getSession:async()=>({data:{session:null}})};
 globalThis.window={REDA_BACKEND:{url:'https://fictional.invalid',publishableKey:'fictional-public'}};
 globalThis.orgTestClient=(_u,_k,options)=>({auth,from:table=>{
  const org=options.global?.headers?.['x-reda-organization']||null;
  const query={eq(){return this},select(){return this},order(){return this},limit(){return this},insert(data){writes.push({org,table,data});return this},single:async()=>({data:{id:'fictional',version:1}}),then(resolve){reads.push({org,table});return Promise.resolve({data:[]}).then(resolve)}};return query;
 }});
 const source=(await readFile(new URL('../../reda-2/secure-browser.mjs',import.meta.url),'utf8')).replace(/^import[^\n]+/, 'const createClient=globalThis.orgTestClient');
 const api=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
 api.setWorkspace({id:'clinic-a'});const pending=api.createPatient('Fictional A');api.setWorkspace({id:'clinic-b'});release();await pending;
 assert.equal(writes[0].org,'clinic-a');assert.equal(writes[0].data.organization_id,'clinic-a');
 const list=api.listPatients();api.setWorkspace({id:'clinic-a'});release();await list;assert.equal(reads.at(-1).org,'clinic-b');
 api.setWorkspace(null);await assert.rejects(api.listPatients(),/arbetsyta/);
 delete globalThis.orgTestClient;delete globalThis.window;
});
