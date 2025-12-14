from vhagilab import user_credential
from vhagilab.SessionPlatform import *
from vhagilab.vhfront_msg import vhfront_msg
import gradio as gr

@AgentBoundTimeCredit(300,7200)
class GuestTokenEntity(BaseTokenClosureEntity): pass

# Authorized for a fixed-term 5 minuts session per 2 houres, per IP.
def authnz(user,passwd,agent):
    if user_credential.auth(user,passwd):
        if GuestTokenEntity(user,agent).get_time_credit() <= 0:
            gr.Warning(vhfront_msg('GUEST_LIMIT'),duration=5)
            return False
        return True
    else:
        gr.Warning(vhfront_msg('USER_PASS_INCORRECT'),duration=5) 
        return False

sp=IPSessionPlatform (
    AuthTokenClosure (
        TimeCreditTokenClosure (
            TokenClosure(),
            GuestTokenEntity
        ),
        authnz = authnz
    )
)
