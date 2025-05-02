'''
## Instant response
pretty_print( ichat( thread.id, "امروز چندمه؟") )

## Stream response
for chunk in schat( thread.id, "یه جوک بگو؟"):
    print(chunk.delta.content[0].text.value, end="", flush=True)
print('\\n===')

## Always, the last (completed) response is accessible via thread.messages
last_msg = client.beta.threads.messages.retrieve(thread_id=thread.id, message_id=chunk.id)
print(last_msg.content[0].text.value)
'''

from openai import OpenAI
from ..cache import cache
import json as _json

_DEFAULT_CONFIG="openai_client_config"
_DEFAULT_CLIENT=0
_config_files={_DEFAULT_CLIENT:_DEFAULT_CONFIG}
_configs={}
_clients={}
_busy_threads=set()
_SUSPEND_RUN_TIMEOUT=600

def set_config(config_file, client_id=_DEFAULT_CLIENT):
    assert client_id not in _config_files or _config_files[client_id][0]!='^',f"Cannot set over a previously loaded config ({_config_files[client_id][1:]})"
    _config_files[client_id]=config_file

## Everything starts with a client!
def add_client(client_id=_DEFAULT_CLIENT):
    from ._openai_module00 import safe_provider
    if client_id not in _config_files:
        import re
        generic_config_file=re.sub("\\^|[_-]*[0-9]*$","",_config_files[_DEFAULT_CLIENT])
        generic_config_file+=f"_{client_id:02}"
        set_config(generic_config_file,client_id)
    with open(_config_files[client_id]+'.json',encoding='utf-8') as config_file:
        config = _configs[client_id] = _json.load(config_file)
        global _client_ipn
        OPENAI_BASE_URL,_client_ipn = safe_provider(config['GATEWAY'],config['PROTOCOL'])
        _clients[client_id] = OpenAI(base_url=OPENAI_BASE_URL+"/v1", api_key=config['ACCESS_TOKEN'])
        _config_files[client_id]='^'+_config_files[client_id]

def client(client_id=_DEFAULT_CLIENT):
    if client_id not in _clients:
        add_client(client_id)
    return _clients[client_id]

def create_thread( ORGANIZATION, CASE, USER, title="Temp", *, client_id=_DEFAULT_CLIENT ):
    thread = client(client_id).beta.threads.create(
        metadata = {
            "organization": ORGANIZATION,  # End-user organization
            "case": CASE,  # The case
            "user": USER,  # Logged in user
            "client": _configs[client_id]['CLIENT'],
            "client_ipn": _client_ipn,
            "title": title
        }
    )
    return thread

@cache(ttl=86400)
def _get_thread_meta( thrd_id, /, *, client_id=_DEFAULT_CLIENT ):
    cl = client(client_id)
    t = cl.beta.threads.retrieve(thrd_id)
    return t.metadata

def _set_thread_meta( thrd_id, meta, /, *, client_id=_DEFAULT_CLIENT ):
    clid = {} if client_id==_DEFAULT_CLIENT else {'client_id':client_id}
    if _get_thread_meta(thrd_id, **clid ) != meta:
        cl = client(client_id)
        cl.beta.threads.update(thrd_id,metadata=meta)
        _get_thread_meta( thrd_id, __FRESH=True, __HACK=meta, **clid )

def get_thread_tag( thrd_id, tag, default=None, /, *, client_id=_DEFAULT_CLIENT ):
    clid = {} if client_id==_DEFAULT_CLIENT else {'client_id':client_id}
    meta = _get_thread_meta(thrd_id, **clid )
    return meta.get(tag,default)

def set_thread_tag( thrd_id, tag, value='*', /, *, client_id=_DEFAULT_CLIENT ):
    clid = {} if client_id==_DEFAULT_CLIENT else {'client_id':client_id}
    if not value:
        del_thread_tag(thrd_id, tag, **clid)
    else:
        meta = _get_thread_meta(thrd_id, **clid )
        if meta.get(tag,None) != value:
            meta[tag]=str(value)
            cl = client(client_id)
            cl.beta.threads.update(thrd_id,metadata=meta)
            _get_thread_meta( thrd_id, __FRESH=True, __HACK=meta, **clid )

def del_thread_tag( thrd_id, tag, /, *, client_id=_DEFAULT_CLIENT ):
    clid = {} if client_id==_DEFAULT_CLIENT else {'client_id':client_id}
    meta = _get_thread_meta(thrd_id, **clid )
    if tag in meta:
        del meta[tag]
        cl = client(client_id)
        cl.beta.threads.update(thrd_id,metadata=meta)
        _get_thread_meta( thrd_id, __FRESH=True, __HACK=meta, **clid )

def delete_threads( threads_id, /, *, client_id=_DEFAULT_CLIENT, verbose=True ):
    from time import sleep
    cl = client(client_id)
    for tid in threads_id:
        if verbose: print(tid,end=' ... ')
        cl.beta.threads.delete(tid)
        sleep(1)
        if verbose: print('deleted.')

@cache(ttl=86400)
def assistant_info( asst_id='DEFAULT_ASST', /, *, client_id=_DEFAULT_CLIENT ):
    import base64
    cl = client(client_id)
    cnfg =_configs[client_id]
    if asst_id in cnfg: asst_id=cnfg[asst_id]
    asst_obj = cl.beta.assistants.retrieve(asst_id)
    try:
        vs_id = asst_obj.tool_resources.file_search.vector_store_ids[0]
        max_ret=next(o.file_search.max_num_results for o in asst_obj.tools if o.type=='file_search')
        vs_name = cl.beta.vector_stores.retrieve(vs_id).name
    except AttributeError:
        vs_name = None
    pre=f"Asst:{asst_obj.name} - Vs:{vs_name}" + (f" @{max_ret}" if vs_name else '')
    return f"{pre} {base64.b64encode(asst_obj.model.encode('utf-8')).decode('utf-8')}.{hash(pre)%100000}"

def is_closed_msg(msg_obj):
    return ( msg_obj.metadata.get("closed",None) or 
             msg_obj.content[0].text.value[:2]=="~~" )

def _check_closed_user_msg(user_msg, _closed):
    msg = { 'role':'user', 'content': user_msg }
    if _closed:
        user_msg = "~~ "+user_msg
    elif user_msg[:2]=="~~":
        _closed=True
    if _closed:
        msg['metadata']={'closed':'*'}
    return msg, _closed

def _check_closed_resp(resp,_closed,_cl):
    if resp.content[0].text.value[:2]=="~~":
        _closed=True
    if ( _closed and not resp.metadata.get("closed",None) ):
        resp.metadata["closed"]='*'
        _cl.beta.threads.messages.update(
            message_id=resp.id,
            thread_id=resp.thread_id,
            metadata=resp.metadata
        )

# Instant chat
def ichat( thrd_id, user_msg, /, asst_id='DEFAULT_ASST', *,
           client_id=_DEFAULT_CLIENT, model_id=None, closed=False, verbose=False):
    cl = client(client_id)
    cnfg = _configs[client_id]
    if asst_id in cnfg: asst_id=cnfg[asst_id]
    if model_id in cnfg: model_id=cnfg[model_id]
    if verbose:
        print(user_msg)
    user_msg, closed = _check_closed_user_msg(user_msg,closed)
    clid = {} if client_id==_DEFAULT_CLIENT else {'client_id':client_id}
    lm = list_messages(thrd_id,**clid)
    global _busy_threads
    from time import sleep
    for _ in range(_SUSPEND_RUN_TIMEOUT):
        if thrd_id in _busy_threads:
            sleep(0.25)
        else:
            break
    else:
        cancel_run(thrd_id,**clid)
    _busy_threads.add(thrd_id)
    run = cl.beta.threads.runs.create_and_poll(
        thread_id = thrd_id,
        assistant_id = asst_id,
        model = model_id,
        additional_messages = [user_msg]
    )
    if thrd_id in _busy_threads:
        _busy_threads.remove(thrd_id)
    msg_rsp = cl.beta.threads.messages.list(thrd_id, limit=2).data[::-1]
    _check_closed_resp(msg_rsp[-1],closed,cl)
    list_messages(thrd_id,__FRESH=True,__HACK=lm+msg_rsp,**clid)
    if verbose:
        print(msg_rsp[-1])
    return msg_rsp[-1]

## Stream chat
def schat( thrd_id, user_msg, /, asst_id='DEFAULT_ASST', *,
           client_id=_DEFAULT_CLIENT, model_id=None, closed=False):
    cl = client(client_id)
    cnfg = _configs[client_id]
    if asst_id in cnfg: asst_id=cnfg[asst_id]
    if model_id in cnfg: model_id=cnfg[model_id]
    user_msg, closed = _check_closed_user_msg(user_msg,closed)
    clid = {} if client_id==_DEFAULT_CLIENT else {'client_id':client_id}
    lm = list_messages(thrd_id,**clid)
    global _busy_threads
    from time import sleep
    for _ in range(_SUSPEND_RUN_TIMEOUT):
        if thrd_id in _busy_threads:
            sleep(0.25)
        else:
            break
    else:
        cancel_run(thrd_id,**clid)
    lm.append( cl.beta.threads.messages.create (
        thread_id = thrd_id,
        **user_msg
    ) )
    _busy_threads.add(thrd_id)
    for e in cl.beta.threads.runs.create(
        thread_id = thrd_id,
        assistant_id = asst_id,
        model = model_id,
        stream = True
    ):
        sse = e.event
        if sse[:14]=="thread.message":
            sse=sse[15:]
            if sse=="delta":
                if not resp.content:
                    resp.content=e.data.delta.content
                else:
                    tdelta = e.data.delta.content[0].text
                    resp.content[0].text.value+=tdelta.value
                yield resp
            elif sse=="created":
                resp = e.data
                if closed:
                    resp.metadata['closed']='*'
            elif sse=="completed":
                resp = e.data
                if closed:
                    resp.metadata['closed']='*'
                yield resp
            elif sse=="incomplete":
                resp = e.data
                if closed:
                    resp.metadata['closed']='*'
                resp.content[0].text.value+=" /.. ..."
                yield resp
    if thrd_id in _busy_threads:
        _busy_threads.remove(thrd_id)
    _check_closed_resp(resp,closed,cl)
    lm.append(resp)
    list_messages(thrd_id,__FRESH=True,__HACK=lm,**clid)
    return resp

## Pacing chat. It is in fact a Stream chat, but yields also empty deltas when the ai is thinking.
def pchat( thrd_id, user_msg, /, asst_id='DEFAULT_ASST', *,
           client_id=_DEFAULT_CLIENT, model_id=None, closed=False):
    cl = client(client_id)
    cnfg = _configs[client_id]
    if asst_id in cnfg: asst_id=cnfg[asst_id]
    if model_id in cnfg: model_id=cnfg[model_id]
    user_msg, closed = _check_closed_user_msg(user_msg,closed)
    clid = {} if client_id==_DEFAULT_CLIENT else {'client_id':client_id}
    lm = list_messages(thrd_id,**clid)
    global _busy_threads
    from time import sleep
    for _ in range(_SUSPEND_RUN_TIMEOUT):
        if thrd_id in _busy_threads:
            sleep(0.25)
        else:
            break
    else:
        cancel_run(thrd_id,**clid)
    lm.append( cl.beta.threads.messages.create (
        thread_id = thrd_id,
        **user_msg
    ) )
    _busy_threads.add(thrd_id)
    resp = None
    for e in cl.beta.threads.runs.create(
        thread_id = thrd_id,
        assistant_id = asst_id,
        model = model_id,
        stream = True
    ):
        sse = e.event
        if sse[:14]=="thread.message":
            sse=sse[15:]
            if sse=="delta":
                if not resp.content:
                    resp.content=e.data.delta.content
                else:
                    tdelta = e.data.delta.content[0].text
                    resp.content[0].text.value+=tdelta.value
                yield resp
            elif sse=="created":
                resp = e.data
                if closed:
                    resp.metadata['closed']='*'
            elif sse=="completed":
                resp = e.data
                if closed:
                    resp.metadata['closed']='*'
                yield resp
            elif sse=="incomplete":
                resp = e.data
                if closed:
                    resp.metadata['closed']='*'
                resp.content[0].text.value+=" /.. ..."
                yield resp
        else:
            if resp and resp.content:
                yield resp
    if thrd_id in _busy_threads:
        _busy_threads.remove(thrd_id)
    _check_closed_resp(resp,closed,cl)
    lm.append(resp)
    list_messages(thrd_id,__FRESH=True,__HACK=lm,**clid)
    return resp

def cancel_run(thrd_id, /, *, client_id=_DEFAULT_CLIENT):
    global _busy_threads
    if thrd_id in _busy_threads:
        from openai import BadRequestError
        cl = client(client_id)
        runs = cl.beta.threads.runs.list(thrd_id, limit=1)
        latest_run = runs.data[0] if runs.data else None
        if latest_run and latest_run.status in ["queued", "in_progress"]:
            try:
                cl.beta.threads.runs.cancel(latest_run.id,thread_id=thrd_id)
                _busy_threads.remove(thrd_id)
            except BadRequestError as e:
                print(f"Failed to cancel run {latest_run.id}: {str(e)}")

def last_message(thrd_id, /, *, client_id=_DEFAULT_CLIENT, closed=False):
    clid = {} if client_id==_DEFAULT_CLIENT else {'client_id':client_id}
    lm = list_messages(thrd_id,**clid)
    for m in lm[::-1]:
        if closed or not is_closed_msg(m):
            return m

def dump_msg_obj(obj):
    from openai.types.beta.threads.message import Message
    if isinstance(obj,Message):
        if not obj.status:
            obj.status='completed'
        return obj.model_dump()
    else:
        return None

def load_msg_obj(data):
    from openai.types.beta.threads.message import Message
    if data.get('object',None)=='thread.message':
        return Message.model_validate(data)
    else:
        return None

@cache(ttl=864000,dump_fallback=dump_msg_obj,load_fallback=load_msg_obj)
def list_messages(thrd_id, /, *, client_id=_DEFAULT_CLIENT):
    cl = client(client_id)
    return cl.beta.threads.messages.list(thrd_id, limit=100).data[::-1]

def undo_chat(thrd_id, n_msg_rsp=1, /, *, client_id=_DEFAULT_CLIENT, closed=False):
    clid = {} if client_id==_DEFAULT_CLIENT else {'client_id':client_id}
    lm = list_messages(thrd_id, **clid)
    cl = client(client_id)
    n_msg_rsp*=2
    back=0
    for m in lm[::-1]:
        if n_msg_rsp==0:
            break
        cl.beta.threads.messages.delete(m.id,thread_id=thrd_id)
        if closed or not is_closed_msg(m):
            n_msg_rsp-=1
        back+=1
    list_messages(thrd_id,__FRESH=True,__HACK=lm[:-back],**clid)

@cache(ttl=864000)
def get_filename(file_id, /, *, client_id=_DEFAULT_CLIENT):
    cl = client(client_id)
    fobj = cl.files.retrieve(file_id)
    return fobj.filename

## Resolve file_ids of the cited files to filenames, and augment to file_citation annotations.
def resolve_filecitations( msg_response, *, client_id=_DEFAULT_CLIENT ):
    anyref = False
    for a in msg_response.content[0].text.annotations:
        if a.type=='file_citation':
            anyref = True
            clid = {} if client_id==_DEFAULT_CLIENT else {'client_id':client_id}
            a.file_citation.filename = get_filename(a.file_citation.file_id, **clid)
    return anyref

## Augment annotations with quotes of cited files.
def augment_quotes( msg_response, *, client_id=_DEFAULT_CLIENT ):
    if all( hasattr(a.file_citation,'quote') and a.file_citation.quote
            for a in msg_response.content[0].text.annotations 
            if a.type=='file_citation' ):
        return True
    cl = client(client_id)
    tid = msg_response.thread_id
    rid = msg_response.run_id
    anyref = False
    annts = msg_response.content[0].text.annotations
    for rstep in cl.beta.threads.runs.steps.list(
        thread_id = tid,
        run_id = rid,
        include=["step_details.tool_calls[*].file_search.results[*].content"]
    ).data:
        if rstep.type=='tool_calls':
            tool_call = rstep.step_details.tool_calls[0]
            if tool_call.type=='file_search':
                tc_fs_res = tool_call.file_search.results
                for a in annts:
                    if a.type=='file_citation':
                        anyref = True
                        if ( not hasattr(a.file_citation,'quote') or
                             not a.file_citation.quote ):
                            cite = a.text
                            i = cite.index(':')+1
                            j = cite.index('†')
                            ref_id = int(cite[i:j])
                            if ref_id < len(tc_fs_res):
                                a.file_citation.quote = tc_fs_res[ref_id].content[0].text
    return anyref
