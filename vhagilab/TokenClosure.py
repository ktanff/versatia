from typing import Any, Callable
from time import time as now
from math import isinf as _isinf
from math import inf as _inf
from math import ldexp as _ldexp

thresproj = lambda t,x: -t if -t <= x <= 0 else t if 0 < x < t else x
drift = lambda n: min(1,_ldexp(n,-16))

class TokenClosureEntity:
    def __init__(self,user:str,agent:Any,ttl:int|None=None):
        self.user=user
        self.agnt=agent
        self.tstmp=now()
        self.subt=set()
        if ttl: self.ttl=thresproj(3,ttl)
    def __str__(self):
        return f"{self.__dict__}"

_void_token = TokenClosureEntity(None,None)
_void_token.tstmp = 0
_void_token.ttl = 0
_void_cont={' #':_void_token}

from enum import Enum
class token_status(Enum):
    STALE=-1
    EXPIRED=0
    ALIVE=1
    def __eq__(self,delta):
        if isinstance(delta,token_status):
            return self._value_==delta._value_
        else:
            if delta>0:
                return self._value_==1
            elif _isinf(delta):
                return self._value_==-1
            else:
                return self._value_==0
class ttl_delta(float):
    @property
    def status(self):
        if self>0:
            return token_status.ALIVE
        elif _isinf(self):
            return token_status.STALE
        else:
            return token_status.EXPIRED

class TokenClosure:
    def __init__(self, default_ttl: int, stale_limit: int, cont: dict={}, subc: dict={}):
        # Set two time limits (in second);
        # - default_ttl (aka inactive_limit): set default for TTL, the time duration 
        # after that a contract is vanished.
        # - stale_limit: set default for Stale time, the time after expiration a
        # contract keep in memory, so that any termination around could be done,
        # gracefully.
        self.default_ttl=thresproj(5,default_ttl)
        self.stale_limit=max(5,stale_limit)
        self.cont=cont
        self.subc=subc
    
    def isSignedin(self, user:str, agent:Any) -> bool:
        # Test whether the user-agent contract is existent and not expired.
        return ( user in self.cont.get(agent,_void_cont) and
                self._checkAndExtendTTL(self.cont[agent][user],False) > 0 )
    
    def trueUser(self, subtoken: str) -> str | None:
        # Tell who is **the true user** of a subcontract.
        return self.subc.get(subtoken,_void_token).user
    
    def lastActiveUser(self, agent:Any) -> str | None:
        # Return the last active user for an agent. The contract might be expired,
        # you check it.
        return max(self.cont.get(agent,_void_cont).values(),
                   key = lambda t:t.tstmp).user
    
    def signin(self, authnz:Callable[[str,str,Any],bool|Any], user:str, passwd:str, agent:Any, ttl:int|None=None) -> bool|Any:
        # Authenticating/Authorizing user, sign a contract between user and agent.
        x = authnz(user,passwd,agent)
        if x:
            if agent not in self.cont:
                self.cont[agent]={}
            agentload = len(self.cont[agent])
            if user not in self.cont[agent]:
                if x is not True:
                    if isinstance(x,int):
                        ttl = x
                    elif hasattr(x,'ttl'):
                        ttl = x.ttl
                t = TokenClosureEntity(user,agent,ttl)
                t.tstmp += drift(agentload)
                self.cont[agent][user] = t
            else:
                self.cont[agent][user].tstmp = now() + drift(agentload)
        return x
    
    def makeFixedTerm(self, user:str, agent:Any):
        # Make the user-agent contract fixed-term, so that no extension won't be applied.
        t = self.cont.get(agent,_void_cont).get(user,_void_token)
        t.ttl = - abs ( getattr(t,'ttl',self.default_ttl) )
    
    def signout(self, user:str, agent:Any):
        # Sign out the user-agent contract.
        self.cont.get(agent,_void_cont).get(user,_void_token).tstmp = 0
        self.cleanupStaleTokens(agent)
    
    def _checkAndExtendTTL(self,t,ext):
        _now = now()
        ttl = getattr(t,'ttl',self.default_ttl)
        delta = t.tstmp + abs(ttl) - _now
        if delta + self.stale_limit < 0:
            delta=-_inf
            if t.agnt:
                del self.cont[t.agnt][t.user]
                if self.cont[t.agnt]=={}:
                    del self.cont[t.agnt]
            for sub in t.subt:
                del self.subc[sub]
        elif ext and delta > 0 :
            t.tstmp = _now
            if ttl < 0:
                ext = -delta
            if not( ext is True or ext==ttl ):
                t.ttl = ext
        return ttl_delta(delta)
    
    def checkAndExtendTTL(self, subtoken:str, extend:int|bool=True) -> ttl_delta|int:
        # Extend ttl for a token, only if it has not been already expired.  
        # The token (a signed contract between a user and an agent) is checked
        # and extended only via the given subtoken.
        # It returns the remaining ttl if delta > -stale_limit, else returns False.
        # Set extend=False or 0, if you wnat just read the ttl.
        # Leave extend un-assigned, it extends by default_ttl.
        return self._checkAndExtendTTL(self.subc.get(subtoken,_void_token),max(False,extend))
    
    def setSub(self, user:str, agent:Any, subtoken:str) -> str:
        # Set a subtoken (`session_hash`) for a user-agent contract.
        # A footprint is made on the class states, only if the subtoken has not
        # previously associated to any other user.
        t = self.cont.get(agent,_void_cont).get(user,_void_token)
        if self._checkAndExtendTTL(t,False) > 0:
            t.subt.add(subtoken)
            self.subc[subtoken] = t
            return t.user
        else:
            return None
    
    def endSub(self,subtoken:str) -> str:
        # End a subtoken (`session_hash`) and retract all the associated footprints
        # from the class state.
        if subtoken in self.subc:
            t = self.subc[subtoken]
            self.cont[t.agnt][t.user].subt.remove(subtoken)
            del self.subc[subtoken]
            return t.user
        else:
            return None
    
    def cleanupStaleTokens(self,agent:Any):
        # Clean up all the footprints remaining on class states while their 
        # associated contracts are made by the given agent but expired.
        if agent=='*':
            agents = list(self.cont.keys())
        elif agent in self.cont:
            agents=[agent]
        else:
            agents=[]
        for agent in agents:
            era = now() - self.stale_limit
            for u,t in list(self.cont[agent].items()):
                ttl = getattr(t,'ttl',self.default_ttl)
                if t.tstmp + abs(ttl) < era:
                    del self.cont[agent][u]
                    if self.cont[agent]=={}:
                        del self.cont[agent]
                    for sub in t.subt:
                        del self.subc[sub]

class AuthTokenClosure(TokenClosure):
    def __init__(self, __tc:TokenClosure, authnz:Callable[[str,str,Any],bool|Any], **kwargs):
        super().__init__(**__tc.__dict__)
        self.authnz=authnz
        self.__tc=__tc
    def signin(self, user:str, passwd:str, agent:Any, ttl:int|None=None) -> bool|Any:
        return super().signin(self.authnz,user,passwd,agent,ttl)
