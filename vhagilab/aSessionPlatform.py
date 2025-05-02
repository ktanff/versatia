from typing import Any, Callable
from .SessionPlatform import *

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
                            TokenClosure (
                                default_ttl = app_schema['INACTIVE_LIMIT'],
                                stale_limit = app_schema['STALE_LIMIT']
                            ),
                            authnz = authnz
                        ),
                        platform = platform(),
                        **app_schema
                    )
