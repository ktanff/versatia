from typing import Any, Callable
from .SessionPlatform import *
from math import inf

@SessionBoundTimeCredit(inf)
class SessionTokenEntity(BaseTokenClosureEntity): pass

__aSessPltfm:CookieSessionPlatform = None

def aSessionPlatform():
    global __aSessPltfm
    return __aSessPltfm

def setup( authnz:Callable[[str,str,Any],bool|Any] ):
    global __aSessPltfm
    from .sess_utils import platform
    from . import app_schema
    __aSessPltfm = CookieSessionPlatform (
                        AuthTokenClosure (
                            TimeCreditTokenClosure (
                                TokenClosure (
                                    stale_limit = app_schema['STALE_LIMIT']
                                ),
                                SessionTokenEntity
                            ),
                            authnz = authnz
                        ),
                        platform = platform(),
                        **app_schema
                    )
