import gradio as _gr

grskipool=(_gr.skip(),)*20

def _glift(x,a):
    if x is None:
        x = a
        arity = 0
    else:
        if isinstance(x,list):
            x.append(a)
        elif isinstance(x,set):
            x.add(a)
        else:
            x = [x,a]
        arity = len(x) - 1
    return x,arity

def _with_request(fn):
    if not callable(fn): return False
    from inspect import signature
    fnsignature = signature(fn)
    for param in fnsignature.parameters.values():
        if param.annotation is _gr.Request:
            return True
    return False

class grSessionPlatform:
    from ..SessionPlatform import SessionPlatform
    def __init__(self,sp:SessionPlatform,on_unload=None):
        self.sp=sp
        self.alivest=_gr.Textbox(value='1',show_label=False,visible=False,interactive=False)
        self.on_unload = on_unload
    
    def user(self,request:_gr.Request):
        return self.sp.trueUser(request.session_hash)
    
    def getSessionTTL(self,request:_gr.Request):
        return self.sp.checkAndExtendTTL(request.session_hash,extend=False)
    
    def loadOnSessionPlatform(self,
                              app:_gr.Blocks,                             
                              on_load_fn=None, *,
                              on_load_inputs=None,
                              on_load_outputs=None,
                              alive_check_every=None
                              ):
        def _grant_session(request:_gr.Request):
            return self.sp.grant_session(request.username,request.session_hash)
        if on_load_fn:
            app.load(_grant_session).success(on_load_fn,on_load_inputs,on_load_outputs)
        else:
            app.load(_grant_session)
        def _end_session(request:_gr.Request):
            if self.on_unload:
                self.on_unload(request)
            self.sp.end_session(request.session_hash)
        app.unload(_end_session)
        if not alive_check_every:
            alive_check_every = max(4,min(self.sp.stale_limit/2,56))
        def _check_alive(request:_gr.Request):
            return self.sp.checkAndExtendTTL(request.session_hash,extend=False).status.value
        _gr.Timer(alive_check_every).tick(fn=_check_alive,outputs=self.alivest)
        def _on_alivest_change(alivest,request:_gr.Request):
            if alivest=='0':
                from ..vhfront_msg import vhfront_msg
                _gr.Warning(vhfront_msg('SESS_EXPIRE'),duration=10)
                #raise _gr.Error(vhfront_msg('SESS_EXPIRE'),duration=10)
                if self.on_unload:
                    self.on_unload(request)
        self.alivest.change(
            fn=_on_alivest_change,
            inputs=self.alivest,
            js="function (alivest){if(alivest=='-1'){window.location.href='/signin/';} return alivest; }"
        )
    
    def signout_by(self,btn:_gr.Button):
        btn.link='/signout'
        @btn.click()
        def _(request:_gr.Request):
            self.sp.checkAndExtendTTL(request.session_hash)
            if self.on_unload:
                self.on_unload(request)
    
    def live_session(self, event, inputs=None, outputs=None, *ev_args, extend=True, **ev_kwargs):
        from ..TokenClosure import token_status
        from ..lambdas import nullfn,lift
        from inspect import isgeneratorfunction
        from ..vhfront_msg import vhfront_msg
        outputs,ret_arity = _glift(outputs,self.alivest)
        def decorator(fn=nullfn):
            with_request = _with_request(fn)
            if isgeneratorfunction(fn):
                def fn_wrapper(request:_gr.Request,*args):
                    alivest = self.sp.checkAndExtendTTL(request.session_hash,extend).status.value
                    if alivest==token_status.ALIVE:
                        res = fn(*args,request) if with_request else fn(*args)
                        for chunk in res:
                            yield lift(chunk,_gr.skip())
                    else:
                        _gr.Warning(vhfront_msg('SESS_EXPIRE'),duration=5)
                        yield lift(grskipool[:ret_arity],alivest)
            else:
                def fn_wrapper(request:_gr.Request,*args):
                    alivest = self.sp.checkAndExtendTTL(request.session_hash,extend).status.value
                    if alivest==token_status.ALIVE:
                        res = fn(*args,request) if with_request else fn(*args)
                        return lift(res,_gr.skip())
                    else:
                        _gr.Warning(vhfront_msg('SESS_EXPIRE'),duration=5)
                        return lift(grskipool[:ret_arity],alivest)
            event(fn_wrapper,inputs,outputs,*ev_args,**ev_kwargs)
        return decorator
    
    def ChatInterfaceOnLiveSession(self,fn,additional_outputs=None,extend=True,**ci_kwargs):
        from ..TokenClosure import token_status
        from ..lambdas import lift
        from inspect import isgeneratorfunction
        from ..vhfront_msg import vhfront_msg
        additional_outputs,ret_arity = _glift(additional_outputs,self.alivest)
        with_request = _with_request(fn)
        if isgeneratorfunction(fn):
            def wrapper(request:_gr.Request,*args): 
                alivest = self.sp.checkAndExtendTTL(request.session_hash,extend).status.value
                if alivest==token_status.ALIVE:
                    res = fn(*args,request) if with_request else fn(*args)
                    for chunk in res:
                        yield lift(chunk,_gr.skip())
                else:
                    _gr.Warning(vhfront_msg('SESS_EXPIRE'),duration=5)
                    yield ' - ',*(_gr.skip(),)*ret_arity,alivest
        else:
            def wrapper(request:_gr.Request,*args): 
                alivest = self.sp.checkAndExtendTTL(request.session_hash,extend).status.value
                if alivest==token_status.ALIVE:
                    res = fn(*args,request) if with_request else fn(*args)
                    return lift(res,_gr.skip())
                else:
                    _gr.Warning(vhfront_msg('SESS_EXPIRE'),duration=5)
                    return ' - ',*(_gr.skip(),)*ret_arity,alivest
        return _gr.ChatInterface(wrapper, additional_outputs=additional_outputs, **ci_kwargs)

    def chatIntegrateOnLiveSession( self, 
                                response_fn,
                                inputbox:_gr.Textbox,
                                chatbox:_gr.Chatbot, *,
                                extend=True,
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
        from ..TokenClosure import token_status
        from ..vhfront_msg import vhfront_msg
        with_request = _with_request(response_fn)
        pre_with_request = _with_request(pre_response)
        post_with_request = _with_request(post_response)
        pre_grskip=grskipool[:2+len(pre_extra_outputs)]
        main_grskip=grskipool[:1+len(extra_outputs)]
        post_grskip=grskipool[:2+len(post_extra_outputs)]
        submit_indic = kwargs.pop('submit_btn',True)
        def startstep(msg,history,request:_gr.Request,*args):
            alivest = self.sp.checkAndExtendTTL(request.session_hash,extend).status.value
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
                alivest = self.sp.checkAndExtendTTL(request.session_hash,extend).status.value
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
                alivest = self.sp.checkAndExtendTTL(request.session_hash,extend).status.value
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
            alivest = self.sp.checkAndExtendTTL(request.session_hash,extend).status.value
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
    
    def __getattr__(self, attr):
        return getattr(self.sp, attr)
