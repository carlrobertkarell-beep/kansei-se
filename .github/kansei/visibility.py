#!/usr/bin/env python3
"""Reproducible AI-answer measurement. Offline, stdlib-only; no scraping or paid API calls.
Keep result files outside this public repository. No patient information belongs here.
"""
from __future__ import annotations
import argparse,collections,copy,datetime,json,re,tempfile
from pathlib import Path
from urllib.parse import urlsplit
VERSION='kansei-v1-20261016'
ENGINES=['chatgpt','gemini','copilot','perplexity']
REPEATS=3
QUESTIONS={
'ultraljud':[
'Var kan jag göra ultraljud av axeln i Stockholm utan remiss?',
'Var kan jag boka ultraljud av knät i Stockholm?',
'Jag söker en mottagning för muskuloskeletalt ultraljud vid Odenplan. Vilka alternativ finns?',
'Vad kostar en privat ultraljudsundersökning av muskler och leder i Stockholm?',
'Kan man undersöka en hälsena med ultraljud, och var görs det i Stockholm?',
'Vad kan ultraljud visa vid ett svullet knä?',
'Kan ultraljud visa en senskada i axeln?',
'Vad är skillnaden mellan ultraljud och magnetkamera vid axelbesvär?',
'Var kan jag se förklarade ultraljudsbilder av kalkaxel?',
'Hur ser en Bakercysta ut på ultraljud?'],
'hyaluron':[
'Var kan jag få en hyaluroninjektion i Stockholm?',
'Vad kostar hyaluroninjektioner i Stockholm?',
'Vilka mottagningar i Stockholm erbjuder hyaluroninjektion i båda knäna?',
'Var kan jag boka ultraljudsvägledd hyaluroninjektion i Stockholm?',
'Behöver jag en separat konsultation innan jag bokar hyaluron i Stockholm?',
'Vad är skillnaden mellan Sinovial HL64 och Sinogel?',
'Är Synovial och Sinovial samma namn på en ledinjektion?',
'Vad kan hyaluroninjektioner hjälpa med vid knäartros och vilka är begränsningarna?',
'Vad bör jag fråga en klinik om innan en hyaluroninjektion?',
'Kan hyaluroninjektion vara aktuell i höften eller axeln och hur bedöms det?'],
'naprapati':[
'Jag söker en naprapat vid Odenplan. Vilka mottagningar finns?',
'Var kan jag boka en naprapat i Vasastan?',
'Vad kostar ett naprapatbesök vid Odenplan?',
'Finns det en naprapat nära Upplandsgatan i Stockholm?',
'Var kan jag få hjälp med axelbesvär och rehabilitering i Vasastan?',
'Finns det naprapater i Stockholm som även arbetar med muskuloskeletalt ultraljud?',
'Hur väljer jag mellan naprapat och fysioterapeut när jag har besvär med muskler och leder?',
'Vad brukar ingå i ett första besök hos en naprapat?',
'Behöver jag remiss till en naprapat i Stockholm?',
'Hur kan jag hitta en legitimerad naprapat som ger en plan för fortsatt rehabilitering i Vasastan?']}
Q={f'{cluster[0].upper()}{i:02}':{'cluster':cluster,'question':q} for cluster,qs in QUESTIONS.items() for i,q in enumerate(qs,1)}
EXPECTED={(engine,qid,repeat) for engine in ENGINES for qid in Q for repeat in range(1,REPEATS+1)}

def template():
    return {'version':VERSION,'purpose':'Fixed consumer-interface benchmark, not a universal ranking or market share. No runs performed by generating this file.',
            'locale':'sv-SE','location':'Stockholm, Sweden','records':[
        {'engine':e,'question_id':q,'question':Q[q]['question'],'repeat':r,'status':'pending',
         'surface':None,'model_label':None,'web_mode':None,'observed_at':None,'evidence_reference':None,
         'response_text':None,'cited_urls':[],'recommended':False,'recommendation_evidence':None,'reviewed':False}
        for e,q,r in sorted(EXPECTED)]}

def validate(data):
    if not isinstance(data,dict) or data.get('version')!=VERSION:raise ValueError('Unknown benchmark version; do not compare unlike prompt sets.')
    if data.get('locale')!='sv-SE' or data.get('location')!='Stockholm, Sweden':raise ValueError('Keep locale and stated location fixed.')
    records=data.get('records')
    if not isinstance(records,list) or len(records)>len(EXPECTED):raise ValueError('Invalid record count.')
    seen=set()
    for row in records:
        if not isinstance(row,dict):raise ValueError('Record must be an object.')
        key=(row.get('engine'),row.get('question_id'),row.get('repeat'))
        if key not in EXPECTED or key in seen:raise ValueError('Unknown or duplicate engine/question/repeat: '+repr(key))
        seen.add(key)
        if row.get('question')!=Q[key[1]]['question']:raise ValueError('Prompt changed; create a new benchmark version instead.')
        if row.get('status') not in ['pending','completed','error']:raise ValueError('Invalid status.')
        if type(row.get('reviewed')) is not bool or type(row.get('recommended')) is not bool:raise ValueError('Use JSON true/false, not strings.')
        if row['status']!='completed':
            if row['reviewed'] or row['recommended']:raise ValueError('Uncompleted tests cannot be reviewed or recommendations.')
            continue
        for field in ['surface','model_label','web_mode','observed_at','evidence_reference','response_text']:
            if not isinstance(row.get(field),str) or not row[field].strip():raise ValueError('Completed run missing '+field)
        if row['surface'] not in ['consumer_ui','api']:raise ValueError('Surface must explicitly distinguish consumer_ui and api.')
        if row['web_mode'] not in ['on','auto','off','not_disclosed']:raise ValueError('Invalid web mode.')
        stamp=datetime.datetime.fromisoformat(row['observed_at'].replace('Z','+00:00'))
        if stamp.tzinfo is None:raise ValueError('observed_at requires a timezone.')
        if not isinstance(row.get('cited_urls'),list) or len(row['cited_urls'])>100:raise ValueError('Invalid citation list.')
        for url in row['cited_urls']:
            if not isinstance(url,str):raise ValueError('Citation URL must be a string.')
            u=urlsplit(url)
            if u.scheme not in ['http','https'] or not u.hostname or u.username or u.password:raise ValueError('Invalid citation URL.')
        if row['recommended']:
            excerpt=row.get('recommendation_evidence')
            if not isinstance(excerpt,str) or not excerpt.strip() or excerpt not in row['response_text'] or not re.search(r'\bkansei\b',excerpt,re.I):
                raise ValueError('A recommendation needs a verified verbatim excerpt naming Kansei, not just a source link.')
    return records

def score(data):
    rows=validate(data)
    complete=[r for r in rows if r['status']=='completed' and r['reviewed']]
    output={'version':VERSION,'planned_runs':len(EXPECTED),'reviewed_runs':len(complete),'coverage_pct':round(100*len(complete)/len(EXPECTED),2),
            'errors':sum(r['status']=='error' for r in rows),'unreviewed_completed':sum(r['status']=='completed' and not r['reviewed'] for r in rows),
            'warning':'A missing test is not a negative result. Rates use reviewed completed answers only. Different models, surfaces and web modes remain separate.',
            'groups':[],'cited_domains':{},'cited_kansei_urls':{}}
    buckets=collections.defaultdict(list)
    domains=collections.Counter();kansei_urls=collections.Counter()
    for r in complete:
        key=(r['engine'],Q[r['question_id']]['cluster'],r['surface'],r['model_label'],r['web_mode'])
        buckets[key].append(r)
        for host in {urlsplit(u).hostname.lower() for u in r['cited_urls']} :domains[host]+=1
        for u in set(r['cited_urls']):
            if urlsplit(u).hostname.lower() in ['kansei.se','www.kansei.se']:kansei_urls[u]+=1
    for engine in ENGINES:
        for cluster in QUESTIONS:
            found=[(k,v) for k,v in buckets.items() if k[:2]==(engine,cluster)]
            if not found:
                output['groups'].append({'engine':engine,'cluster':cluster,'surface':None,'model':None,'web_mode':None,'n':0,'mention_pct':None,'citation_pct':None,'recommendation_pct':None})
            for k,rs in sorted(found):
                n=len(rs)
                mention=sum(bool(re.search(r'\bkansei\b',r['response_text'],re.I)) for r in rs)
                cited=sum(any(urlsplit(u).hostname.lower() in ['kansei.se','www.kansei.se'] for u in r['cited_urls']) for r in rs)
                recommended=sum(r['recommended'] for r in rs)
                output['groups'].append({'engine':engine,'cluster':cluster,'surface':k[2],'model':k[3],'web_mode':k[4],'n':n,
                    'mention_pct':round(100*mention/n,2),'citation_pct':round(100*cited/n,2),'recommendation_pct':round(100*recommended/n,2)})
    output['cited_domains']=dict(domains.most_common())
    output['cited_kansei_urls']=dict(kansei_urls.most_common())
    return output

def markdown(report):
    lines=['# Kansei — verifierad AI-synlighet','',f"Granskade svar: {report['reviewed_runs']} av {report['planned_runs']} planerade tester. Täckning: {report['coverage_pct']} %.",'',
           '**Ej testat visas som —, aldrig som 0 % synlighet.** Omnämnande, källhänvisning och rekommendation mäts separat. Underlaget är ett fast stickprov, inte en marknadsandel eller garanterad ranking.','',
           '| Tjänst | Område | Gränssnitt/modell/sökläge | Granskade svar | Omnämnande | Källhänvisning | Rekommendation |',
           '|---|---|---|---:|---:|---:|---:|']
    fmt=lambda x:'—' if x is None else str(x)+' %'
    for g in report['groups']:
        mode='/'.join(str(g[x] or 'ej testat').replace('|','/') for x in ['surface','model','web_mode'])
        lines.append(f"| {g['engine']} | {g['cluster']} | {mode} | {g['n']} | {fmt(g['mention_pct'])} | {fmt(g['citation_pct'])} | {fmt(g['recommendation_pct'])} |")
    lines+=['','## Källor som förekommer i svaren','Antal granskade svar där respektive domän citeras. Alla domäner är inte konkurrenter.','']
    lines.extend(f'- {h}: {n}' for h,n in report['cited_domains'].items())
    lines+=['','## Kansei-sidor som citeras','']
    lines.extend(f'- {u}: {n}' for u,n in report['cited_kansei_urls'].items())
    return '\n'.join(lines)+'\n'

def self_test():
    t=template();s=score(t)
    assert len(t['records'])==360 and s['reviewed_runs']==0 and all(g['citation_pct'] is None for g in s['groups'])
    r=t['records'][0]
    r.update(status='completed',surface='consumer_ui',model_label='test fixture only',web_mode='on',observed_at='2026-10-16T12:00:00+02:00',evidence_reference='TEST FIXTURE — NOT AN OBSERVATION',response_text='Kansei är ett alternativ att boka.',cited_urls=['https://www.kansei.se/ultraljud/'],recommended=True,recommendation_evidence='Kansei är ett alternativ att boka.',reviewed=True)
    s=score(t);assert s['reviewed_runs']==1 and sum(g['n'] for g in s['groups'])==1
    g=next(g for g in s['groups'] if g['n']);assert g['mention_pct']==100 and g['citation_pct']==100 and g['recommendation_pct']==100
    r['reviewed']=False;assert score(t)['reviewed_runs']==0
    t['records'].append(copy.deepcopy(r))
    try:score(t);raise AssertionError('Duplicate accepted')
    except ValueError:pass
    t=template();r=t['records'][0];r['status']='error';assert score(t)['errors']==1 and score(t)['reviewed_runs']==0
    print('PASS: AI scorecard self-tests — 360 pending runs, no fake zeroes, review gate, denominator, independent metrics and duplicate rejection.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--template',type=Path,help='Create a new empty private JSON measurement file; never overwrites.')
    p.add_argument('--report',type=Path,help='Read a private JSON measurement file.')
    p.add_argument('--output',type=Path,help='New output directory outside this public repository.')
    p.add_argument('--questions',action='store_true')
    p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.self_test:self_test()
    elif a.questions:print(json.dumps(Q,ensure_ascii=False,indent=2))
    elif a.template:
        with a.template.open('x',encoding='utf-8') as f:json.dump(template(),f,ensure_ascii=False,indent=2)
    elif a.report:
        if not a.output:p.error('--report requires --output')
        if a.report.stat().st_size>10_000_000:p.error('Input is too large')
        report=score(json.loads(a.report.read_text(encoding='utf-8')))
        a.output.mkdir(parents=True,exist_ok=False)
        (a.output/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        (a.output/'summary.md').write_text(markdown(report),encoding='utf-8')
    else:p.print_help()
