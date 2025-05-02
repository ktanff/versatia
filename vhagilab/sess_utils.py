from fastapi import FastAPI, Request

__module_blocks_type = None
__session_wrapper_class = None
__mount_app = None

def base_setup(session_wrapper_class, mount_app, module_blocks_type):
    # session_wrapper_class like grSessionPlatform, that is
    #  a has-a class with SessionPlatform attribute as sp.
    # mount_app like gr.mount_gradio_app
    # module_blocks_type like gr.Blocks
    global __session_wrapper_class, __mount_app, __module_blocks_type
    __session_wrapper_class = session_wrapper_class
    __mount_app = mount_app
    __module_blocks_type = module_blocks_type

__platform = FastAPI()
platform=lambda:__platform

from .SessionPlatform import SessionPlatform
__sps:list[SessionPlatform]=[]
__idxmap:dict[str,int]={}

def signin_kickstart(req:Request):
    # It serves as auth_dependency for Signin block.
    global __sps
    agents=[]
    for sp in __sps:
        agents.append(sp.get_agent(req,True))
    return '|'.join(agents)

airbagging = lambda x,t: ' '+t+' ' if not x else x if isinstance(x,str) else x.target if hasattr(x,'target') else t

def signin_hub(user,passwd,target_path,pipe_delimited_agents):
    # It serves for a login action, e.g login button, in Signin block.
    global __sps,__idxmap
    i = __idxmap.get(target_path)
    if i is None:
        return target_path
    else:
        agnts = pipe_delimited_agents.split("|")
        agnt = agnts[i]
        return airbagging(agnt and __sps[i].signin(user,passwd,agnt), target_path)

@__platform.get('/signout')
def signout(req:Request):   # Signout endpoint
    from starlette.responses import RedirectResponse
    from fastapi import status
    global __sps
    for sp in __sps:
        sp.signout(req) or print(f"Unprivileged signing out: {req.headers}")
    return RedirectResponse(url="/signin/", status_code=status.HTTP_302_FOUND)

def privileged_users(users):
    fltr = None
    if isinstance(users,str):
        if users[0]=='!':
            users=users[1:]
            fltr=lambda _:not(_)
        else:
            fltr=lambda _:_
        if users[0]=='@':
            def decorator(auth_dep):
                def wrapper_auth_dep(req:Request):
                    from .user_credential import get_user_tag
                    ua=auth_dep(req)
                    cred_tag = users[1:]
                    if ua and fltr( get_user_tag(ua[:ua.index('*')],cred_tag) ):
                        return ua
                    else:
                        return None
                return wrapper_auth_dep
            return decorator
        else:
            users=[users]
    if isinstance(users,(list,tuple,set)):
        if "!" in users:
            users.remove("!")
            fltr = lambda _:not(_)
        elif not callable(fltr):
            fltr=lambda _:_
        def decorator(auth_dep):
            def wrapper_auth_dep(req:Request):
                ua=auth_dep(req)
                if ua and fltr( ua[:ua.index('*')] in users ):
                    return ua
                else:
                    return None
            return wrapper_auth_dep
        return decorator
    return lambda _:_

def __mount_blocks(blocks,path,auth_dep=None,prvldg_users=None,/):
    global __platform, __mount_app
    if auth_dep:
        auth_dep=privileged_users(prvldg_users)(auth_dep)
    __platform = __mount_app( __platform, blocks, path=path, auth_dependency=auth_dep, show_api=False)

def mount_signin_blocks(signin_blocks):
    __mount_blocks(signin_blocks,"/signin",signin_kickstart)

def mount_main_blocks(main_blocks,auth=None,privileged_users=None,session_platform=None):
    if session_platform:
        global __sps,__idxmap
        if session_platform in __sps:
            __idxmap[""]=__sps.index(session_platform)
        else:
            __idxmap[""]=len(__sps)
            __sps.append(session_platform)
        auth_dep=session_platform.get_user
    else:
        assert auth==None, "Authentication out of SessionUtils framework not implemented!"
        auth_dep=auth
    __mount_blocks(main_blocks,"",auth_dep,privileged_users)

def __inspect_module(module):
    global __session_wrapper_class,__module_blocks_type
    sp = None
    from inspect import getmembers
    for _, obj in getmembers(module):
        if isinstance(obj, __module_blocks_type):
            blocks = obj
        elif isinstance(obj, __session_wrapper_class):
            sp = obj.sp
    return blocks,sp

def mount_module_blocks(module,path:str,privileged_users:str|None=None):
    blocks,sp = __inspect_module(module)
    if path=="/signin":
        mount_signin_blocks(blocks)
    else:
        global __sps,__idxmap
        try:
            auth_dep = sp.get_user
            if sp in __sps:
                __idxmap[path]=__sps.index(sp)
            else:
                __idxmap[path]=len(__sps)
                __sps.append(sp)
        except AttributeError:
            auth_dep = None
        __mount_blocks(blocks,path,auth_dep,privileged_users)

def run(root_path="",host='127.0.0.1',port=7860, **kwargs):
    from uvicorn import run as _run
    _run(__platform, root_path=root_path, host=host, port=port, access_log = False, **kwargs)
