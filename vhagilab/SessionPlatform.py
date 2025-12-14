from fastapi import FastAPI, Request
from .TokenClosure import *

class SessionPlatform(AuthTokenClosure):
    def __init__(self, atc:AuthTokenClosure):
        super().__init__(**atc.__dict__)
    
    def get_agent(self,request:Request,fallback=False):
        raise NotImplementedError("get_agent() has been called via an abstract class!")
    
    def get_user(self,req:Request):
        agnt = self.get_agent(req)
        if agnt:
            user = self.lastActiveUser(agnt)
            if user and self.isSignedin(user,agnt):
                return f"{user}*{agnt}"
        return None
    
    def relieve_agent(self,req:Request):
        agnt = self.get_agent(req)
        super().cleanup(agnt)
        return agnt
    
    def grant_session(self,username,session_hash):
        user,agnt=username.split('*')
        self.setSub(user,agnt,session_hash)
    
    def end_session(self,session_hash):
        self.getTTLandAttend(session_hash)
        self.endSub(session_hash)
    
    #__excludedkeys__ = SessionPlatform(AuthTokenClosure(TimeCreditTokenClosure(TokenClosure(0),BaseTokenClosureEntity),lambda*_:False)).__dict__.keys()
    __excludedkeys__ = ['stale_limit','cont','subc','MAX_AGENT_SOFT_LIM','MAX_AGENT_HARD_LIM','MAX_USER_SOFT_LIM','MAX_USER_HARD_LIM','MAX_SESS_SOFT_LIM','MAX_SESS_HARD_LIM','authnz','__tc','__tctc']
    def __eq__(self,other):
        return ( isinstance(other,self.__class__) and 
                 all(getattr(other,attr)==value 
                     for attr,value in self.__dict__.items()
                     if attr not in self.__excludedkeys__) )
###

class CookieSessionPlatform(SessionPlatform):
    def __init__(self,
                 atc:AuthTokenClosure, *,
                 platform:FastAPI,
                 APP_SESSION_ERA:str="tc-10002.01",
                 SESSION_SCRT_KEY:str|None=None,
                 **kwargs):
        super().__init__(atc)
        self.platform=platform
        self.app_era=APP_SESSION_ERA
        if not SESSION_SCRT_KEY:
            from .token import safe_rand
            SESSION_SCRT_KEY=safe_rand(20)
        from starlette.middleware.sessions import SessionMiddleware
        if 'SSL_KEYFILE' in kwargs and 'SSL_CERTFILE' in kwargs:
            platform.add_middleware(
                SessionMiddleware,
                secret_key=SESSION_SCRT_KEY,
                max_age=3456000,
                same_site='none',
                https_only=True
            )
        else:
            platform.add_middleware(
                SessionMiddleware,
                secret_key=SESSION_SCRT_KEY,
                max_age=3456000
            )
    
    def get_agent(self,request:Request,fallback=False):
        agnt = request.session.get(self.app_era)
        if not agnt and fallback: # TODO: an internal tc is required to keep agent*__root__ tokens, ttl=max_age which attend_True once meet here
            from .token import safe_rand
            agnt = safe_rand()
        request.session[self.app_era]=agnt
        return agnt
###

class IPSessionPlatform(SessionPlatform):
    def __init__(self, atc:AuthTokenClosure):
        super().__init__(atc)
    
    def get_agent(self,request:Request,fallback=False):
        return request.client.host
###

#class BearerSessionPlatform(SessionPlatform):
#    def __init__(self, atc:AuthTokenClosure, **kwargs):
#        super().__init__(atc)
#        # TDOD: ...
#    ##
#    def get_agent(self,request:Request,fallback=False):
#        # TDOD: ...
###
