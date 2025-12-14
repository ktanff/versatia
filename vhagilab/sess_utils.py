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
        sp.relieve_agent(req) or print(f"Unprivileged signing out: {req.headers}")
    return RedirectResponse(url="/signin/", status_code=status.HTTP_302_FOUND)

def privileged_users(user_patterns,permissive=True):
    if not user_patterns:
        return (lambda _:_) if permissive else (lambda _:(lambda _:None))
    elif user_patterns[0]=='!' and len(user_patterns)==1:
        return (lambda _:(lambda _:None)) if permissive else (lambda _:_)
    if isinstance(user_patterns, str):
        if user_patterns[0]=='!':
            return privileged_users( user_patterns[1:].split(','), False )
        else:
            return privileged_users( user_patterns.split(','), True )
    assert isinstance(user_patterns, list), f"Expected 'user_patterns' to be a list, got {type(user_patterns)}"
    while '' in user_patterns: user_patterns.remove('')
    if "!" in user_patterns:
        user_patterns.remove("!")
        return privileged_users( user_patterns, False )
    def decorator(auth_dep):
        def wrapper_auth_dep(req:Request):
            ua=auth_dep(req)
            if not ua: return ua
            from .user_credential import get_user_tag
            usr=ua[:ua.index('*')]
            for ptrn in user_patterns:
                if ( ptrn[0]=='@' and get_user_tag(usr,ptrn[1:])
                    or usr is ptrn ):
                        return ua if permissive else None
            else:
                return None if permissive else ua
        return wrapper_auth_dep
    return decorator

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
