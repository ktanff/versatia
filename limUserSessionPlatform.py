from vhagilab import app_schema, user_credential
from vhagilab.SessionPlatform import *
from vhagilab.vhfront_msg import vhfront_msg as __vhfront_msg
from vhagilab.sess_utils import platform as __platform

import gradio as gr

@UserBoundTimeCredit( app_schema['DEFAULT_TIME_CREDIT'], app_schema['TIME_CREDIT_RENEWAL'] )
class limUserTokenEntity(BaseTokenClosureEntity): pass

# Authorized for a DEFAULT_TIME_CREDIT seconds session per TIME_CREDIT_RENEWAL, for limited users.
def limu_authnz(user,passwd,agent):
    if user_credential.auth(user,passwd):
        if limUserTokenEntity(user,agent).get_time_credit() <= 0:
            gr.Warning(vhfront_msg('SPECIAL_GUEST_LIMIT'),duration=5)
            return False
        return True
    else:
        gr.Warning(vhfront_msg('USER_PASS_INCORRECT'),duration=5) 
        return False

sp=CookieSessionPlatform (
    AuthTokenClosure (
        TimeCreditTokenClosure (
            TokenClosure( stale_limit = app_schema['STALE_LIMIT'] ),
            limUserTokenEntity
        ),
        authnz = limu_authnz
    ),
    platform = __platform(),
    **app_schema
)
