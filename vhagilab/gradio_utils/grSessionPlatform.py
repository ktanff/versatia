from ..SessionPlatform import SessionPlatform
from ..TokenClosure import token_status
from gradio.blocks import Blocks as _gr_Blocks
import gradio as _gr

grskipool=(_gr.skip(),)*100

def glift(a,b):
    if not a:
        return b,0
    elif type(a) in (list,tuple):
        if len(a)==1:
            return [*a,b],1
        else:
            return [*a,b],len(a)
    else:
        return [a,b],1

def _lift(n):
    match n:
        case 0:
            return (lambda x,y:y)
        case 1:
            return (lambda x,y:(x,y))
        case _:
            return (lambda x,y:(*x,y))


def _with_request(fn):
    if not callable(fn): return False
    from inspect import signature
    fnsignature = signature(fn)
    for param in fnsignature.parameters.values():
        if param.annotation is _gr.Request:
            return True
    return False

_grace_signout_js = (
    "function (alivest) {"
    f" if(alivest=={token_status.VOID.value})"
    " { location.replace('/signout'); } "
    f" if(alivest=={token_status.EXPIRED.value})"
    " { setTimeout(() => { location.replace('/signout'); }, 9500);}"
    " return alivest; }"
)

class _grSessionPlatform:
    def __init__(self, sp:SessionPlatform, app:_gr_Blocks, *, alive_check_every=None):
        self.sp=sp
        self.app=app
        # Matterialize some hidden components
        self.alivest=_gr.Textbox (
            value=token_status.ALIVE.value,
            show_label=False,
            visible=False,
            interactive=False
        )
        if not alive_check_every:
            alive_check_every = min(max(4,sp.stale_limit/2),56)
        else:
            alive_check_every = max(4,alive_check_every)
        # Callback for Timer tick event
        @_gr.Timer(alive_check_every).tick(outputs=self.alivest)
        def _check_alive(request:_gr.Request):
            return self.sp.getTTLandAttend(request.session_hash,attend=False).status.value
        # Callback for the Alive State change event
        @self.alivest.change(inputs=self.alivest, js=_grace_signout_js)
        def _on_alivest_change(alivest,request:_gr.Request):
            if alivest==token_status.EXPIRED:
                from ..vhfront_msg import vhfront_msg
                _gr.Warning(vhfront_msg('SESS_EXPIRE'),duration=9)
        self._loaded = None
    
    def __enter__(self):
        def _grant_session(request:_gr.Request):
            if request.username:
                self.sp.grant_session(request.username,request.session_hash)
                return token_status.ALIVE.value
            else:
                return token_status.VOID.value
        self._loaded = self.app.load(_grant_session,outputs=self.alivest)
        return self
    
    def __exit__(self, exception_type, exception_value, traceback):
        def _end_session(request:_gr.Request,*_):
            self.sp.end_session(request.session_hash)
        self.app.unload(_end_session)
    
    def user(self,request:_gr.Request):
        return self.sp.trueUser(request.session_hash)
    
    def getSessionTTL(self,request:_gr.Request):
        return self.sp.getTTLandAttend(request.session_hash,attend=False)
    
    def signout_by(self,btn:_gr.Button):
        @btn.click(outputs=self.alivest)
        def _on_signout_by(request:_gr.Request):
            self.sp.signout(request.session_hash)
            return token_status.VOID.value
    
    def live_session(self, event, inputs=None, outputs=None, *ev_args, attend=True, **ev_kwargs):
        from ..lambdas import nullfn
        from inspect import isgeneratorfunction
        from ..vhfront_msg import vhfront_msg
        outputs,ret_arity = glift(outputs,self.alivest)
        lift = _lift(ret_arity)
        def decorator(fn=nullfn):
            with_request = _with_request(fn)
            if isgeneratorfunction(fn):
                def fn_wrapper(request:_gr.Request,*args):
                    alivest = self.sp.getTTLandAttend(request.session_hash,attend).status.value
                    if alivest==token_status.ALIVE:
                        res = fn(*args,request) if with_request else fn(*args)
                        for chunk in res:
                            yield lift(chunk,_gr.skip())
                    else:
                        _gr.Warning(vhfront_msg('SESS_EXPIRE'),duration=5)
                        yield lift(grskipool[:ret_arity],alivest)
            else:
                def fn_wrapper(request:_gr.Request,*args):
                    alivest = self.sp.getTTLandAttend(request.session_hash,attend).status.value
                    if alivest==token_status.ALIVE:
                        res = fn(*args,request) if with_request else fn(*args)
                        return lift(res,_gr.skip())
                    else:
                        _gr.Warning(vhfront_msg('SESS_EXPIRE'),duration=5)
                        return lift(grskipool[:ret_arity],alivest)
            event(fn_wrapper,inputs,outputs,*ev_args,**ev_kwargs)
        return decorator
    
    def ChatInterfaceOnLiveSession(self,fn,additional_outputs=None,attend=True,**ci_kwargs):
        from inspect import isgeneratorfunction
        from ..vhfront_msg import vhfront_msg
        additional_outputs,ret_arity = glift(additional_outputs,self.alivest)
        lift = _lift(ret_arity+1)
        with_request = _with_request(fn)
        if isgeneratorfunction(fn):
            def wrapper(request:_gr.Request,*args): 
                alivest = self.sp.getTTLandAttend(request.session_hash,attend).status.value
                if alivest==token_status.ALIVE:
                    res = fn(*args,request) if with_request else fn(*args)
                    for chunk in res:
                        yield lift(chunk,_gr.skip())
                else:
                    _gr.Warning(vhfront_msg('SESS_EXPIRE'),duration=5)
                    yield ' - ',*grskipool[:ret_arity],alivest
        else:
            def wrapper(request:_gr.Request,*args): 
                alivest = self.sp.getTTLandAttend(request.session_hash,attend).status.value
                if alivest==token_status.ALIVE:
                    res = fn(*args,request) if with_request else fn(*args)
                    return lift(res,_gr.skip())
                else:
                    _gr.Warning(vhfront_msg('SESS_EXPIRE'),duration=5)
                    return ' - ',*grskipool[:ret_arity],alivest
        return _gr.ChatInterface(wrapper, additional_outputs=additional_outputs, **ci_kwargs)
    
    def chatIntegrateOnLiveSession( self, 
                                response_fn,
                                inputbox:_gr.Textbox,
                                chatbox:_gr.Chatbot, *,
                                attend=True,
                                extra_inputs=[],
                                extra_outputs=[],
                                pre_response=None,
                                pre_extra_inputs=[],
                                pre_extra_outputs=[],
                                post_response=None,
                                post_extra_inputs=[],
                                post_extra_outputs=[],
                                **kwargs
                              ):
        from ..vhfront_msg import vhfront_msg
        with_request = _with_request(response_fn)
        pre_with_request = _with_request(pre_response)
        post_with_request = _with_request(post_response)
        pre_grskip=grskipool[:2+len(pre_extra_outputs)]
        main_grskip=grskipool[:1+len(extra_outputs)]
        post_grskip=grskipool[:2+len(post_extra_outputs)]
        submit_indic = kwargs.pop('submit_btn',True)
        def startstep(msg,history,request:_gr.Request,*args):
            alivest = self.sp.getTTLandAttend(request.session_hash,attend).status.value
            if alivest==token_status.ALIVE:
                history.append({'role':'user','content':msg})
                rest_output=[]
                if callable(pre_response):
                    if pre_with_request: args=(*args,request)
                    output=pre_response(history,*args)
                    if pre_extra_outputs:
                        output,*rest_output = output
                    if output!=_gr.skip():
                        history=output
                return _gr.update(value="",submit_btn=False,stop_btn=True),history,*rest_output,_gr.skip()
            else:
                return *pre_grskip,alivest
        from inspect import isgeneratorfunction
        if isgeneratorfunction(response_fn):
            def mainstep(history,request:_gr.Request,*args):
                alivest = self.sp.getTTLandAttend(request.session_hash,attend).status.value
                if alivest==token_status.ALIVE:
                    msg=history[-1]['content']
                    if with_request: args=(*args,request)
                    obj = {'role':'assistant','content':None}
                    history.append(obj)
                    for rsp in response_fn(msg,history,*args):
                        if extra_outputs:
                            obj['content'],*rest_output = rsp
                            yield history,*rest_output
                        else:
                            obj['content']=rsp
                            yield history
                else:
                    yield main_grskip if extra_outputs else _gr.skip()
        else:
            def mainstep(history,request:_gr.Request,*args):
                alivest = self.sp.getTTLandAttend(request.session_hash,attend).status.value
                if alivest==token_status.ALIVE:
                    msg=history[-1]['content']
                    if with_request: args=(*args,request)
                    obj = {'role':'assistant','content':None}
                    history.append(obj)
                    rsp=response_fn(msg,history,*args)
                    if extra_outputs:
                        obj['content'],*rest_output = rsp
                        return history,*rest_output
                    else:
                        obj['content']=rsp
                        return history
                else:
                    return main_grskip if extra_outputs else _gr.skip()
        def endstep(history,request:_gr.Request,*args):
            alivest = self.sp.getTTLandAttend(request.session_hash,attend).status.value
            if alivest==token_status.ALIVE:
                history_and_outputs=[_gr.skip()]
                if callable(post_response):
                    if post_with_request: args=(*args,request)
                    history_and_outputs=post_response(history,*args)
                return _gr.update(submit_btn=submit_indic,stop_btn=False),*history_and_outputs
            else:
                _gr.Warning(vhfront_msg('SESS_EXPIRE'),duration=5)
                return post_grskip
        inputbox.submit( startstep,
                         [inputbox,chatbox]+pre_extra_inputs,
                         [inputbox,chatbox]+pre_extra_outputs+[self.alivest],
                         **kwargs
                       ).then( mainstep,
                               [chatbox]+extra_inputs,
                               [chatbox]+extra_outputs,
                               **kwargs
                       ).then( endstep,
                               [chatbox]+post_extra_inputs,
                               [inputbox,chatbox]+post_extra_outputs,
                               **kwargs
                             )
    # A function handle to the grSessionPlatform load callback
    @property
    def loaded(self):
        return self._loaded
    # Attribute Delegation as a SessionPlatform object
    def __getattr__(self, attr):
        return getattr(self.sp, attr)

def loadSessionPlatformOnBlocks( sp:SessionPlatform , app:_gr_Blocks, *, alive_check_every=None ):
    ## Usage template:
    # from vhagilab import gradio_utils as gu 
    # with _gr.Blocks() as demo:
    #     with gu.loadSessionPlatformOnBlocks( aSessionPlatform(), demo ) as gs:
    #         ## Optional, register session-depended on_load_callback fn
    #         # gs.loaded.success( session_required_on_load_fn, inputs, outputs )
    #         ## Session-independed callback functions are registered via demo.load, yet.
    #         # demo.load( other_on_load_fn, inputs, outputs )
    #         ## Code any thing as coded in Gradio conventions ...
    #         # ...
    #         # ...
    #         ## Optional, register unload callback fn
    #         # demo.unload( fn )
    return _grSessionPlatform(sp,app,alive_check_every=alive_check_every)
