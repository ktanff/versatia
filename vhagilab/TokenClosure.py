from typing import Any, Callable, Dict, Type
from time import time as now
from math import nan as void
from math import isnan as isvoid
from math import ldexp as _ldexp

drift = lambda n: min(1,_ldexp(n,-16))

class BaseTokenClosureEntity:
    def __init__(self,user:str,agent:Any):
        self.user=user
        self.agnt=agent
        self.tstmp=now()
        self.subt=set()
    def get_time_credit(self) -> float:
        raise NotImplementedError("get_time_credit() has been called via an abstract class!")
    def set_time_credit(self, value:float) -> None:
        raise NotImplementedError("set_time_credit() has been called via an abstract class!")

_void_token = BaseTokenClosureEntity('','')
_void_token.tstmp = 0
_void_token.time_credit = lambda*_:0
_void_cont={'':_void_token}

def SessionBoundTimeCredit(default_time_credit=0, renewal_period=0):
    # Session-bound Time Credit Trait
    def decorator(cls):
        def get_time_credit(self) -> float:
            if not hasattr(self,'granted_at'):
                self.granted_at = 0
            time_credit_age = now() - self.granted_at
            if time_credit_age >= renewal_period:
                self.ttl = default_time_credit
                self.granted_at += time_credit_age
            return self.ttl
        def set_time_credit(self, value:float) -> None:
            self.ttl = value
        cls.get_time_credit = get_time_credit
        cls.set_time_credit = set_time_credit
        return cls
    return decorator

def AgentBoundTimeCredit(default_time_credit=0, renewal_period=0, MEMORY_SOFT_LIM=9000, MEMORY_HARD_LIM=10000):
    # Agent-bound Time Credit Trait
    def decorator(cls):
        cls.__credits = {}
        def get_time_credit(self) -> float:
            _now = now()
            if self.agnt not in cls.__credits:
                if len(cls.__credits) >= MEMORY_SOFT_LIM:
                    era = _now - renewal_period
                    for a,(ttl,granted_at) in list(cls.__credits.items()):
                        if granted_at < era:
                            del cls.__credits[a]
                    if len(cls.__credits) >= MEMORY_HARD_LIM:
                        raise MemoryError()
                cls.__credits[self.agnt] = [default_time_credit,_now]
                return default_time_credit
            time_credit_age = _now - cls.__credits[self.agnt][1]
            if time_credit_age >= renewal_period:
                cls.__credits[self.agnt] = [default_time_credit,_now]
                return default_time_credit
            return cls.__credits[self.agnt][0]
        def set_time_credit(self, value:float) -> None:
            cls.__credits[self.agnt][0] = value
        cls.get_time_credit = get_time_credit
        cls.set_time_credit = set_time_credit
        return cls
    return decorator

def UserBoundTimeCredit(default_time_credit=0, renewal_period=0, MEMORY_SOFT_LIM=9000, MEMORY_HARD_LIM=10000):
    # User-bound Time Credit Trait
    def decorator(cls):
        cls.__credits = {}
        def get_time_credit(self) -> float:
            _now = now()
            if self.user not in cls.__credits:
                if len(cls.__credits) >= MEMORY_SOFT_LIM:
                    era = _now - renewal_period
                    for u,(ttl,granted_at) in list(cls.__credits.items()):
                        if granted_at < era:
                            del cls.__credits[u]
                    if len(cls.__credits) >= MEMORY_HARD_LIM:
                        raise MemoryError()
                cls.__credits[self.user] = [default_time_credit,_now]
                return default_time_credit
            time_credit_age = _now - cls.__credits[self.user][1]
            if time_credit_age >= renewal_period:
                cls.__credits[self.user] = [default_time_credit,_now]
                return default_time_credit
            return cls.__credits[self.user][0]
        def set_time_credit(self, value:float) -> None:
            cls.__credits[self.user][0] = value
        cls.get_time_credit = get_time_credit
        cls.set_time_credit = set_time_credit
        return cls
    return decorator

from enum import Enum
class token_status(Enum):
    EXPIRED=-1
    VOID=0
    ALIVE=1
    def __eq__(self,delta):
        if isinstance(delta,token_status):
            return self._value_==delta._value_
        elif isinstance(delta,str):
            if self._value_==0:
                return delta in ['0','None','nan','']
            else:
                return self._value_==int(delta)
        elif delta is None or isvoid(delta):
            return self._value_==0
        else:
            if delta > 0:
                return self._value_==1
            else:
                return self._value_==-1
class ttl_delta(float):
    @property
    def status(self):
        if isvoid(self):
            return token_status.VOID
        elif self>0:
            return token_status.ALIVE
        else:
            return token_status.EXPIRED

from .vhfront_msg import vhfront_msg
class ExceedMaxAgentError(MemoryError):
    def __init__():
        super().__init__(vhfront_msg('EXCEED_MAX_AGENT_LIM_ERR'))
class ExceedMaxUserError(MemoryError):
    def __init__():
        super().__init__(vhfront_msg('EXCEED_MAX_USER_LIM_ERR'))
class ExceedMaxSessionError(MemoryError):
    def __init__():
        super().__init__(vhfront_msg('EXCEED_MAX_SESS_LIM_ERR'))

class TokenClosure:
    universe=[]
    def __init__(self,
                 stale_limit: int | None = None, 
                 voidAfter: int | None = None, 
                 cont: Dict[Any, Dict[str, BaseTokenClosureEntity]] | None = None, 
                 subc: Dict[Any, BaseTokenClosureEntity] | None = None,
                 MAX_AGENT_SOFT_LIM: int=100_000,
                 MAX_AGENT_HARD_LIM: int=110_000,
                 MAX_USER_SOFT_LIM: int=32,
                 MAX_USER_HARD_LIM: int=40,
                 MAX_SESS_SOFT_LIM: int=16,
                 MAX_SESS_HARD_LIM: int=20, **_):
        # - stale_limit: a time duration constant (in seconds).
        #   Sessions expire when no interactions occur within the stale time window.
        # - voidAfter: the time duration after which every unattended session, 
        #   includig expired sessions, will be vanished, that means the allocated
        #   memory will be free. It does not play any role on session expiration logis,
        #   but acts as a memory allocation side-effect, only,
        voidAfter=min(max(10,voidAfter or 654321),3456000)
        self.stale_limit=min(max(1,stale_limit or voidAfter-5),voidAfter-5)
        self.voidAfter=voidAfter
        self.cont=cont or {}
        self.subc=subc or {}
        self.MAX_AGENT_SOFT_LIM = MAX_AGENT_SOFT_LIM
        self.MAX_AGENT_HARD_LIM = MAX_AGENT_HARD_LIM
        self.MAX_USER_SOFT_LIM = MAX_USER_SOFT_LIM
        self.MAX_USER_HARD_LIM = MAX_USER_HARD_LIM
        self.MAX_SESS_SOFT_LIM = MAX_SESS_SOFT_LIM
        self.MAX_SESS_HARD_LIM = MAX_SESS_HARD_LIM
        TokenClosure.universe.append(self)
    
    def __del__(self):
        try:
            TokenClosure.universe.remove(self)
        except Exception() as e:
            print(e)
    
    def __repr__(self):
        repr=[]
        prev_tceclsname = None
        for a in self.cont:
            for u in self.cont[a]:
                tceclsname = self.cont[a][u].__class__.__name__
                if tceclsname != prev_tceclsname:
                    repr.append('['+tceclsname+']')
                    prev_tceclsname = tceclsname
                repr.append(f'{self.cont[a][u].__dict__} @{self.cont[a][u].get_time_credit()}')
            repr.append("==+==")
        return '\n'.join(repr)
    
    def _universe_dump():
        for tc in TokenClosure.universe:
            if tc.cont or tc.subc:
                print(tc)
                print()
    
    def isSignedin(self, user:str, agent:Any) -> bool:
        # Test whether the user-agent contract is existent and is alive.
        return ( user in self.cont.get(agent,_void_cont) and
                self._TTLandAttend(self.cont[agent][user],False) > 0 )
    
    def trueUser(self, subtoken: str) -> str | None:
        # Tell who is **the true user** of a subcontract.
        return self.subc.get(subtoken,_void_token).user
    
    def lastActiveUser(self, agent:Any) -> str | None:
        # Return the last active user for an agent.
        # The contract might be expired, you should check it.
        return max(self.cont.get(agent,_void_cont).values(),
                   key = lambda t:t.tstmp).user
    
    def signin(self, authnz: Callable[[str, str, Any], bool | Any], 
               user: str, passwd: str, agent: Any,
               token_entity_class: Type[BaseTokenClosureEntity] = BaseTokenClosureEntity) -> bool | Any:
        # Authenticating/Authorizing user, sign a contract between user and agent.
        x = authnz(user,passwd,agent)
        if x:
            if agent not in self.cont:
                if len(self.cont) >= self.MAX_AGENT_SOFT_LIM:
                    self.cleanup()
                    if len(self.cont) >= self.MAX_AGENT_HARD_LIM:
                        raise ExceedMaxAgentError()
                self.cont[agent] = {}
            agentload = len(self.cont[agent])
            if user not in self.cont[agent]:
                if agentload >= self.MAX_USER_SOFT_LIM:
                    self.cleanup(agent)
                    agentload = len(self.cont[agent])
                    if agentload >= self.MAX_USER_HARD_LIM:
                        raise ExceedMaxUserError()
                t = token_entity_class(user,agent)
                t.tstmp += drift(agentload)
                self.cont[agent][user] = t
            else:
                t = self.cont[agent][user]
                t.tstmp = now() + drift(agentload) 
            if x is not True:
                if isinstance(x,int) or isinstance(x,float):
                    t.set_time_credit(x)
                elif hasattr(x,'ttl'):
                    t.set_time_credit(x.ttl)
        return x
    
    def signout(self, subtoken:str):
        # Sign out the user-agent contract, given a sub-contract token
        self.subc.get(subtoken,_void_token).tstmp = 0
    
    def _TTLandAttend(self,t:BaseTokenClosureEntity,attend:bool):
        if t.tstmp == 0:
            return void
        time_credit = t.get_time_credit()
        if time_credit <=0:
            return time_credit
        elapsed =  now() - t.tstmp
        ttl = time_credit - elapsed
        if ttl > 0:
            stalettl = self.stale_limit - elapsed
            if stalettl > 0:
                if attend:
                    t.tstmp += elapsed
                else:
                    return ttl
            else:
                ttl = stalettl
        t.set_time_credit(ttl)
        return ttl
    
    def getTTLandAttend(self, subtoken:str, attend:bool=True) -> ttl_delta|float:
        # The token (a signed contract between a user and an agent) is checked
        # via the given subtoken. It returns the remaining ttl.
        # Let attend=False, if you wnat just read the ttl.
        # Leave attend un-assigned, or set it by True, it makes fresh the token.
        return ttl_delta(self._TTLandAttend(self.subc.get(subtoken,_void_token),attend))
    
    def setSub(self, user:str, agent:Any, subtoken:str) -> str:
        # Set a subcontract (`session_hash`) for a user-agent contract.
        # A footprint is made on the class states, only if the subcontract has not
        # previously associated to any other user.
        t = self.cont.get(agent,_void_cont).get(user,_void_token)
        if self._TTLandAttend(t,False) > 0:
            if len(t.subt) >= self.MAX_SESS_SOFT_LIM:
                self.cleanup(t.agnt)
                if len(t.subt) >= self.MAX_SESS_HARD_LIM:
                    raise ExceedMaxSessionError()
            t.subt.add(subtoken)
            self.subc[subtoken] = t
            return t.user
        else:
            return None
    
    def endSub(self,subtoken:str) -> str:
        # End a subcontractn (`session_hash`) and retract all the associated footprints
        # from the class state.
        if subtoken in self.subc:
            t = self.subc[subtoken]
            self.cont[t.agnt][t.user].subt.remove(subtoken)
            del self.subc[subtoken]
            return t.user
        else:
            return None
    
    def cleanup(self, agent:Any|None=None):
        # Clean up all the footprints remaining on class states if their 
        # associated tokens are expired.
        if agent:
            if agent in self.cont:
                agents=[agent]
            else:
                agents=[]
        else:
            agents=list(self.cont.keys())
        era = now() - self.voidAfter
        for agent in agents:
            for u,t in list(self.cont[agent].items()):
                if t.tstmp <= era:
                    for sub in t.subt:
                        del self.subc[sub]
                    del self.cont[agent][u]
                    if self.cont[agent]=={}:
                        del self.cont[agent]

class TimeCreditTokenClosure(TokenClosure):
    def __init__(self, __tc:TokenClosure, token_entity_class:Type[BaseTokenClosureEntity], **_):
        super().__init__(**__tc.__dict__)
        self.token_entity_class=token_entity_class
        self.__tc=__tc
    def signin(self, authnz: Callable[[str, str, Any], bool | Any], user:str, passwd:str, agent:Any) -> bool|Any:
        return super().signin(authnz,user,passwd,agent,self.token_entity_class)

class AuthTokenClosure(TimeCreditTokenClosure):
    def __init__(self, __tctc:TimeCreditTokenClosure, authnz:Callable[[str,str,Any],bool|Any], **_):
        super().__init__(**__tctc.__dict__)
        self.authnz=authnz
        self.__tctc=__tctc
    def signin(self, user:str, passwd:str, agent:Any) -> bool|Any:
        return super().signin(self.authnz,user,passwd,agent)
