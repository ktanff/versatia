import gradio as _gr

from typing import Any, Callable

from ..sess_utils import *
from .grSessionPlatform import _grSessionPlatform

base_setup (
    session_wrapper_class = _grSessionPlatform,
    mount_app = _gr.mount_gradio_app,
    module_blocks_type = _gr.Blocks
)

def login_by(btn: _gr.Button,
             signin_hub: Callable[[str,str,str,Any],bool|Any],
             user: _gr.Textbox,
             passwd: _gr.Textbox, *,
             preauthfn: Callable|None=None,
             preauthinputs = None,
             preauthoutputs = None,
             login_target: _gr.Textbox|None=None
            ):
    # signin_hub(user:str, passwd:str, target_path:str, pipe_delimited_agents:Any) -> bool|Any
    # if user is authenticated and authorized to access to target_path, then 
    #  returned target_path is the same as input target_path,
    # elsewhere, i.e user is not authenticated or is not authorized to access to target_path,
    #  then the returned target_path must be airbagged by extra spaces. 
    if login_target is None:
        login_target = _gr.Textbox(value="",show_label=False,visible=False,interactive=False)
    def _signinhub(user,passwd,target,req:_gr.Request):
        return signin_hub(user,passwd,target,req.username)
    if preauthfn:
        ev = btn.click(preauthfn,preauthinputs,preauthoutputs
                      ).success(_signinhub,[user,passwd,login_target],login_target)
    else:
        ev = btn.click(_signinhub,[user,passwd,login_target],login_target)
    ev.success(lambda _:"",login_target,login_target,
               js="function(target){if(target==target.trim()){location.replace(target+'/');} }"
              )

def otherlogin_by(btn:_gr.Button):
    from ..lambdas import nullfn
    btn.click(nullfn,btn,js="function (btn){window.open('/signin/','_blank').focus(); return btn; }")

def _with_request(fn):
    if not callable(fn): return False
    from inspect import signature
    fnsignature = signature(fn)
    for param in fnsignature.parameters.values():
        if param.annotation is _gr.Request:
            return True
    return False

def chatIntegrate( response_fn,
                   inputbox:_gr.Textbox,
                   chatbox:_gr.Chatbot, *,
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
    with_request = _with_request(response_fn)
    pre_with_request = _with_request(pre_response)
    post_with_request = _with_request(post_response)
    submit_indic = kwargs.pop('submit_btn',True)
    def startstep(msg,history,request:_gr.Request,*args):
        history.append({'role':'user','content':msg})
        rest_output=[]
        if callable(pre_response):
            if pre_with_request: args=(*args,request)
            output=pre_response(history,*args)
            if pre_extra_outputs:
                output,*rest_output = output
            if output!=_gr.skip():
                history=output
        return _gr.update(value="",submit_btn=False,stop_btn=True),history,*rest_output
    from inspect import isgeneratorfunction
    if isgeneratorfunction(response_fn):
        def mainstep(history,request:_gr.Request,*args):
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
        def mainstep(history,request:_gr.Request,*args):
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
    def endstep(history,request:_gr.Request,*args):
        history_and_outputs=[_gr.skip()]
        if callable(post_response):
            if post_with_request: args=(*args,request)
            history_and_outputs=post_response(history,*args)
        return _gr.update(submit_btn=submit_indic,stop_btn=False),*history_and_outputs
    inputbox.submit( startstep,
                     [inputbox,chatbox]+pre_extra_inputs,
                     [inputbox,chatbox]+pre_extra_outputs,
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

