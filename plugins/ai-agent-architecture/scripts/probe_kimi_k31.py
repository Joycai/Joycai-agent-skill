#!/usr/bin/env python3
"""Opt-in paid probes for the fixed Ark plan endpoint; never run in ordinary tests.

Requires SEEDDACE_KEY in the environment. Appends sanitized JSONL to
KIMI_PROBE_OUTPUT (default /tmp/kimi-probe-evidence.jsonl). Each phase makes
a bounded number of requests, at most two concurrent, without retries.
Socket timeout: 900 seconds, not an overall wall-clock deadline.
"""
import os,json,time,urllib.request,urllib.error,pathlib,base64,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]/'skills/llm-api-integration'
OUT=pathlib.Path(os.environ.get('KIMI_PROBE_OUTPUT', '/tmp/kimi-probe-evidence.jsonl'))
def key():
    return os.environ['SEEDDACE_KEY']
def redact(v):
    if isinstance(v,dict):
        if 'reasoning' in v.get('type','') and v.get('type') != 'reasoning':
            v={k:({'redacted':True,'chars':len(str(x))} if k in ('delta','text') else x) for k,x in v.items()}
        return {k:({'redacted':True,'chars':len(str(x))} if k in ('reasoning_content','encrypted_content','signature') or (v.get('type') in ('reasoning_text','summary_text') and k=='text') else redact(x)) for k,x in v.items()}
    if isinstance(v,list):return [redact(x) for x in v]
    if isinstance(v,str) and v.startswith('data:'):return {'data_url_omitted':True,'sha256':hashlib.sha256(base64.b64decode(v.split(',',1)[1])).hexdigest()}
    return v
def assemble_chat(events):
    """Reconstruct one-choice Chat SSE without losing reasoning/tool fragments."""
    message={'role':'assistant','content':'','reasoning_content':''}
    calls={}; finish=None; usage=None; model=None; errors=[]
    for event in events:
        model=event.get('model',model)
        if event.get('error'):errors.append(event['error'])
        if event.get('usage') is not None:usage=event['usage']
        for choice in event.get('choices',[]):
            if choice.get('index',0)!=0:raise ValueError('Probe expects one choice')
            if choice.get('finish_reason') is not None:finish=choice['finish_reason']
            delta=choice.get('delta',{})
            for field in ['content','reasoning_content']:
                if delta.get(field):message[field]+=delta[field]
            for field in ['role','encrypted_content']:
                if delta.get(field):message[field]=delta[field]
            for call in delta.get('tool_calls',[]):
                target=calls.setdefault(call['index'],{'id':'','type':'function','function':{'name':'','arguments':''}})
                if call.get('id'):target['id']+=call['id']
                if call.get('type'):target['type']=call['type']
                for field in ['name','arguments']:
                    target['function'][field]+=call.get('function',{}).get(field) or ''
    if calls:message['tool_calls']=[calls[i] for i in sorted(calls)]
    result={'model':model,'choices':[{'index':0,'message':message,'finish_reason':finish}],'usage':usage,'assembled_from_sse':True}
    if errors:result['stream_errors']=errors
    return result

def run(name,body,endpoint='responses'):
    body={'model':'kimi-k3.1-pro',**body}
    start=time.monotonic(); events=[]; status=None; result=None; first=None
    event_times=[]; content_type=None
    try:
        req=urllib.request.Request('https://ark.cn-beijing.volces.com/api/plan/v3/'+endpoint,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key(),'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=900) as r:
            status=r.status
            content_type=r.headers.get("Content-Type")
            if body.get('stream'):
                for line in r:
                    if first is None:first=round(time.monotonic()-start,3)
                    if line.startswith(b'data:'):
                        data=line[5:].strip()
                        if data==b'[DONE]':events.append({'done':True});continue
                        e=json.loads(data);events.append(e);event_times.append(round(time.monotonic()-start,3))
                        if e.get('type') in ('response.completed','response.failed','response.incomplete'):result=e.get('response')
                if endpoint=='chat/completions':result=assemble_chat(events)
                elif result is None:result={'events_without_terminal':True}
            else:result=json.load(r)
    except urllib.error.HTTPError as e:
        status=e.code
        raw=e.read().decode()
        try:result=json.loads(raw)
        except ValueError:result={'error_text':raw[:2000]}
    except Exception as e:result={'transport_error':type(e).__name__,'detail':str(e)}
    rec={'case':name,'endpoint':endpoint,'request':redact(body),'http':status,'seconds':round(time.monotonic()-start,3),'first_line_seconds':first,'response':redact(result)}
    if events:
        rec['events']=redact(events)
        rec['event_seconds']=event_times
        rec['content_type']=content_type
    with OUT.open('a') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    print(json.dumps({'case':name,'http':status,'seconds':rec['seconds'],'status':result.get('status'),'usage':result.get('usage'),'error':result.get('error',result.get('transport_error'))},ensure_ascii=False),flush=True)
    return result


def resp(prompt='Find the smallest positive integer n such that n mod 7 = 3 and n mod 11 = 5. Reply only with the integer.', **kw):
    return {'input':prompt,'max_output_tokens':4096,**kw}
def chat(prompt='Reply with exactly OK.',**kw):
    return {'messages':[{'role':'user','content':prompt}],'max_tokens':4096,**kw}
def phase1():
    from concurrent.futures import ThreadPoolExecutor
    jobs=[('r-effort-'+e,resp(reasoning={'effort':e}),'responses') for e in ['low','high','max','medium','xhigh','minimal','none','bogus']]
    jobs += [('r-effort-default',resp(),'responses'),('r-thinking-disabled',resp(thinking={'type':'disabled'}),'responses'),('c-baseline',chat(),'chat/completions'),('r-stream',resp('Reply with exactly OK.',stream=True,reasoning={'effort':'low'}),'responses')]
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda j:run(*j),jobs))
def phase2():
    from concurrent.futures import ThreadPoolExecutor
    jobs=[]
    for mode in ['responses','chat/completions']:
        pre='r' if mode=='responses' else 'c'
        for tag,file,mime,prompt in [('image','probe-shapes.png','image/png','Count the red squares and blue circles in the attached image. Reply only as red=N,blue=N.'),('pdf','probe-code.pdf','application/pdf','Read DOC-CODE from the attached PDF. Reply only with its value.')]:
            data='data:'+mime+';base64,'+base64.b64encode((ROOT/'assets/api-probes'/file).read_bytes()).decode()
            for stream in ([False,True] if mode=='responses' else [False]):
                if mode=='responses':
                    item={'type':'input_image','image_url':data} if tag=='image' else {'type':'input_file','filename':file,'file_data':data}
                    b=resp([{'role':'user','content':[{'type':'input_text','text':prompt},item]}],stream=stream,reasoning={'effort':'low'})
                else:
                    item={'type':'image_url','image_url':{'url':data}} if tag=='image' else {'type':'file','file':{'filename':file,'file_data':data}}
                    b=chat([{'type':'text','text':prompt},item],reasoning_effort='low')
                jobs.append((pre+'-'+tag+('-stream' if stream else ''),b,mode))
        for value in ['ALPHA','BRAVO']:
            schema={'type':'object','properties':{'code':{'type':'string','enum':[value]}},'required':['code'],'additionalProperties':False}
            prompt='Return JSON with code set to WRONG and extra set to 123.'
            fmt={'type':'json_schema','name':'probe','strict':True,'schema':schema}
            if mode=='responses':b=resp(prompt,text={'format':fmt},reasoning={'effort':'low'})
            else:b=chat(prompt,response_format={'type':'json_schema','json_schema':{k:v for k,v in fmt.items() if k!='type'}},reasoning_effort='low')
            jobs.append((pre+'-schema-'+value,b,mode))
        b=resp('Return a JSON object with count 7.',text={'format':{'type':'json_object'}},reasoning={'effort':'low'}) if mode=='responses' else chat('Return a JSON object with count 7.',response_format={'type':'json_object'},reasoning_effort='low')
        jobs.append((pre+'-json-object',b,mode))
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda j:run(*j),jobs))

def phase3():
    from concurrent.futures import ThreadPoolExecutor
    jobs=[]
    for e in ['low','medium','high','xhigh','max','none','minimal','bogus']:
        jobs.append(('c-effort-'+e,chat(resp()['input'],reasoning_effort=e),'chat/completions'))
    for n in [2,3]:
        for e in ['none','minimal','bogus']:
            jobs.append(('r-effort-'+e+'-repeat'+str(n),resp(reasoning={'effort':e},stream=n==3),'responses'))
        jobs.append(('r-disabled-repeat'+str(n),resp(thinking={'type':'disabled'},stream=n==3),'responses'))
    schema={'type':'object','properties':{'code':{'type':'string','enum':['CHARLIE']}},'required':['code'],'additionalProperties':False}
    jobs.append(('r-schema-stream',resp('Return JSON with code WRONG and extra 123.',text={'format':{'type':'json_schema','name':'probe','strict':True,'schema':schema}},reasoning={'effort':'low'},stream=True),'responses'))
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda j:run(*j),jobs))
def phase4():
    definition={'name':'lookup_probe','description':'Get the verification code for a given label.','parameters':{'type':'object','properties':{'label':{'type':'string'}},'required':['label'],'additionalProperties':False},'strict':True}
    prompt='Use lookup_probe for label cedar. Then reply only with the code returned by the tool.'
    for streaming in [False,True]:
        label='r-tool'+('-stream' if streaming else '')
        tools=[{'type':'function',**definition}]
        first=run(label,resp(prompt,tools=tools,tool_choice='required',stream=streaming,reasoning={'effort':'low'}))
        calls=[x for x in first.get('output',[]) if x.get('type')=='function_call']
        if calls:
            result=[{'type':'function_call_output','call_id':c['call_id'],'output':'{"code":"CEDAR-4826"}'} for c in calls]
            history=[{'role':'user','content':prompt}]+first['output']+result
            run(label+'-return',resp(history,tools=tools,tool_choice='auto',stream=streaming,reasoning={'effort':'low'}))
            if not streaming:
                run('r-tool-previous-id',resp(result,previous_response_id=first['id'],tools=tools,reasoning={'effort':'low'}))
    for choice in ['auto','none',{'type':'function','name':'lookup_probe'}]:
        name=choice if isinstance(choice,str) else 'named'
        run('r-tool-choice-'+name,resp(prompt,tools=[{'type':'function',**definition}],tool_choice=choice,reasoning={'effort':'low'}))
    tools=[{'type':'function','function':definition}]
    first=run('c-tool',chat(prompt,tools=tools,tool_choice='required',reasoning_effort='low'),'chat/completions')
    msg=first.get('choices',[{}])[0].get('message',{})
    if msg.get('tool_calls'):
        history=[{'role':'user','content':prompt},msg]+[{'role':'tool','tool_call_id':c['id'],'content':'{"code":"CEDAR-4826"}'} for c in msg['tool_calls']]
        run('c-tool-return',{'messages':history,'tools':tools,'tool_choice':'auto','reasoning_effort':'low','max_tokens':4096},'chat/completions')

def phase5():
    for e in ['none','minimal','low']:
        run('r-enabled-'+e,resp(thinking={'type':'enabled'},reasoning={'effort':e}))
    run('r-disabled-high',resp(thinking={'type':'disabled'},reasoning={'effort':'high'}))
    first=run('r-store-true',resp('Remember the code ORBIT-6379. Reply OK.',store=True,reasoning={'effort':'low'}))
    if first.get('id'):
        run('r-store-true-followup',resp('What code did I give you? Reply only with the code.',previous_response_id=first['id'],reasoning={'effort':'low'}))
    run('r-temperature',resp('Reply OK.',temperature=0.2,reasoning={'effort':'low'}))
    run('c-temperature',chat(temperature=0.2,reasoning_effort='low'),'chat/completions')

def phase6():
    from concurrent.futures import ThreadPoolExecutor
    definition={'name':'lookup_probe','description':'Get verification code for a label.','parameters':{'type':'object','properties':{'label':{'type':'string'}},'required':['label'],'additionalProperties':False},'strict':True}
    jobs=[]
    for n in [2,3]:
        jobs.append(('r-tool-none-repeat'+str(n),resp('Call lookup_probe with label cedar.',tools=[{'type':'function',**definition}],tool_choice='none',reasoning={'effort':'low'},stream=n==3),'responses'))
    for mode in ['responses','chat/completions']:
        pre='r' if mode=='responses' else 'c'
        for choice,prompt in [('required','Do not call any tools. Reply only OK.'),('none','Call lookup_probe with label cedar.')]:
            if pre=='r':
                if choice=='none':continue
                body=resp(prompt,tools=[{'type':'function',**definition}],tool_choice=choice,reasoning={'effort':'low'})
            else:body=chat(prompt,tools=[{'type':'function','function':definition}],tool_choice=choice,reasoning_effort='low')
            jobs.append((pre+'-tool-conflict-'+choice,body,mode))
        other={**definition,'name':'other_probe'}
        prompt='Call only other_probe with label cedar, never lookup_probe.'
        if pre=='r':body=resp(prompt,tools=[{'type':'function',**d} for d in [definition,other]],tool_choice={'type':'function','name':'lookup_probe'},reasoning={'effort':'low'})
        else:body=chat(prompt,tools=[{'type':'function','function':d} for d in [definition,other]],tool_choice={'type':'function','function':{'name':'lookup_probe'}},reasoning_effort='low')
        jobs.append((pre+'-tool-conflict-named',body,mode))
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda j:run(*j),jobs))
def chat_stream(prompt='Reply with exactly OK.',**kw):
    return chat(prompt,stream=True,stream_options={'include_usage':True},**kw)

def phase7():
    from concurrent.futures import ThreadPoolExecutor
    jobs=[]
    for effort in ['low','medium','high','xhigh','max','none','minimal','bogus']:
        jobs.append(('s-chat-effort-'+effort,chat_stream(resp()['input'],reasoning_effort=effort),'chat/completions'))
    for kind,file,mime,prompt in [('image','probe-shapes.png','image/png','Count the red squares and blue circles. Reply only as red=N,blue=N.'),('pdf','probe-code.pdf','application/pdf','Read DOC-CODE from the attached PDF. Reply only with its value.')]:
        data='data:'+mime+';base64,'+base64.b64encode((ROOT/'assets/api-probes'/file).read_bytes()).decode()
        item={'type':'image_url','image_url':{'url':data}} if kind=='image' else {'type':'file','file':{'filename':file,'file_data':data}}
        jobs.append(('s-chat-'+kind,chat_stream([{'type':'text','text':prompt},item],reasoning_effort='low'),'chat/completions'))
    for value in ['DELTA','ECHO']:
        schema={'type':'object','properties':{'code':{'type':'string','enum':[value]}},'required':['code'],'additionalProperties':False}
        jobs.append(('s-chat-schema-'+value,chat_stream('Return JSON with code WRONG and extra 123.',reasoning_effort='low',response_format={'type':'json_schema','json_schema':{'name':'probe','strict':True,'schema':schema}}),'chat/completions'))
    jobs.append(('s-chat-json',chat_stream('Return a JSON object with count 7.',reasoning_effort='low',response_format={'type':'json_object'}),'chat/completions'))
    jobs.append(('s-chat-no-usage-option',chat('Reply only OK.',reasoning_effort='low',stream=True),'chat/completions'))
    for endpoint in ['responses','chat/completions']:
        body=resp('List integers from 1 to 200, one per line.',reasoning={'effort':'low'},stream=True,max_output_tokens=16) if endpoint=='responses' else chat_stream('List integers from 1 to 200, one per line.',reasoning_effort='low',max_tokens=16)
        jobs.append(('s-'+('responses' if endpoint=='responses' else 'chat')+'-truncated',body,endpoint))
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda j:run(*j),jobs))

def phase8():
    definition={'name':'lookup_probe','description':'Get verification code for a label.','parameters':{'type':'object','properties':{'label':{'type':'string'}},'required':['label'],'additionalProperties':False},'strict':True}
    tools=[{'type':'function','function':definition}]
    prompt='Use lookup_probe for label cedar. Then reply only with the code returned by the tool.'
    first=run('s-chat-tool',chat_stream(prompt,tools=tools,tool_choice='required',reasoning_effort='low'),'chat/completions')
    msg=first.get('choices',[{}])[0].get('message',{})
    calls=msg.get('tool_calls',[])
    if calls:
        for call in calls:
            assert call['function']['name']=='lookup_probe' and json.loads(call['function']['arguments'])=={'label':'cedar'}
        history=[{'role':'user','content':prompt},msg]+[{'role':'tool','tool_call_id':c['id'],'content':'{"code":"CEDAR-4826"}'} for c in calls]
        run('s-chat-tool-return',{'model':'kimi-k3.1-pro','messages':history,'tools':tools,'tool_choice':'auto','reasoning_effort':'low','max_tokens':4096,'stream':True,'stream_options':{'include_usage':True}},'chat/completions')
    from concurrent.futures import ThreadPoolExecutor
    jobs=[]
    for endpoint in ['responses','chat/completions']:
        for choice,prompt in [('required','Do not call any tools. Reply only OK.'),('none','Call lookup_probe with label cedar.'),('named','Call only other_probe with label cedar, never lookup_probe.')]:
            defs=[definition]+([{**definition,'name':'other_probe'}] if choice=='named' else [])
            if endpoint=='responses':
                selected={'type':'function','name':'lookup_probe'} if choice=='named' else choice
                body=resp(prompt,tools=[{'type':'function',**d} for d in defs],tool_choice=selected,reasoning={'effort':'low'},stream=True)
            else:
                selected={'type':'function','function':{'name':'lookup_probe'}} if choice=='named' else choice
                body=chat_stream(prompt,tools=[{'type':'function','function':d} for d in defs],tool_choice=selected,reasoning_effort='low')
            jobs.append(('s-'+('responses' if endpoint=='responses' else 'chat')+'-choice-'+choice,body,endpoint))
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda j:run(*j),jobs))

if __name__=='__main__':
    import sys
    if len(sys.argv) != 2 or sys.argv[1] not in ['baseline', 'phase1', 'phase2', 'phase3', 'phase4', 'phase5', 'phase6', 'phase7', 'phase8']:
        raise SystemExit('Usage: SEEDDACE_KEY=<set privately> python3 probe_kimi_k31.py baseline|phase1|phase2|phase3|phase4|phase5|phase6|phase7|phase8')
    key()  # Fail before requests when credentials are absent.
    phase=sys.argv[1]
    if phase=='baseline':run('responses-baseline',resp('Reply with exactly OK.'))
    else:globals()[phase]()
