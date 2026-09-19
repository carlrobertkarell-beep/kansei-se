-- Aggregate EI QA without patient response content.
create function private.reda_ei_quality(p_days integer default 30) returns jsonb language plpgsql stable security definer set search_path='' as $$
declare actor uuid:=private.reda_live_actor();org uuid:=private.reda_request_organization();since timestamptz;begin
 if not private.reda_is_clinician_aal2() then raise exception using errcode='42501',message='Behandlarbehörighet och MFA krävs.';end if;
 if p_days not between 1 and 365 then raise exception using errcode='22023',message='Välj en period mellan 1 och 365 dagar.';end if;since=now()-make_interval(days=>p_days);
 return (with d as(select ed.id,ed.action,ed.code,ed.applied,ed.result_plan_id,ed.created_at,p.payload->>'blueprintId' blueprint_id,p.payload->>'clinicalKnowledgeVersion' knowledge_version
 from public.reda_engine_decisions ed join public.reda_patients pt on pt.id=ed.patient_id left join public.reda_plans p on p.id=ed.result_plan_id or (p.patient_id=ed.patient_id and p.status='active')
 where pt.organization_id=org and ed.created_at>=since),
 r as(select decision_id,verdict from public.reda_decision_reviews where decision_id in(select id from d)),
 c as(select plan_id,count(*) n from public.reda_review_cases where plan_id in(select result_plan_id from d where result_plan_id is not null) group by plan_id),
 totals as(select count(*) total,count(*)filter(where action='advance')advance,count(*)filter(where action='hold')hold,count(*)filter(where action='regress')regress,count(*)filter(where action in('review','blocked'))escalate,count(*)filter(where applied)applied from d)
 select jsonb_build_object('days',p_days,'totals',to_jsonb(t),'reviewed',(select count(*)from r),'overridden',(select count(*)from r where verdict in('reject','override','changed')),'post_change_cases',(select count(*)from d join c on c.plan_id=d.result_plan_id where d.applied),'by_blueprint',coalesce((select jsonb_agg(to_jsonb(x)order by x.total desc,x.blueprint_id)from(select coalesce(blueprint_id,'unknown')blueprint_id,count(*)total,count(*)filter(where action='advance')advance,count(*)filter(where action='hold')hold,count(*)filter(where action='regress')regress,count(*)filter(where action in('review','blocked'))escalate from d group by 1)x),'[]'::jsonb),'by_knowledge_version',coalesce((select jsonb_agg(to_jsonb(x)order by x.total desc,x.knowledge_version)from(select coalesce(knowledge_version,'unknown')knowledge_version,count(*)total from d group by 1)x),'[]'::jsonb))from totals t);
end$$;
create function public.reda_ei_quality(p_days integer default 30) returns jsonb language sql stable security invoker set search_path='' as $$select private.reda_ei_quality(p_days)$$;
revoke all on function private.reda_ei_quality(integer),public.reda_ei_quality(integer) from public,anon,authenticated;grant execute on function private.reda_ei_quality(integer),public.reda_ei_quality(integer) to authenticated;
