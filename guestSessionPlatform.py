from vhagilab import user_credential
from vhagilab.SessionPlatform import *
from vhagilab.vhfront_msg import vhfront_msg
import gradio as gr

# A TokenClosure with default fixed-term 5 minuts tokens
__guest_tc = TokenClosure(default_ttl= -300 , stale_limit=10) 

def guest_authnz(user,passwd,agent):
    if __guest_tc.isSignedin('_shadow',agent):
        gr.Warning(vhfront_msg('GUEST_LIMIT'),duration=5)
        return False
    else:
        if user_credential.auth(user,passwd):
            # A shadow remains 2 houres to prevent multiple guest loggins
            __guest_tc.signin(lambda *_:True,'_shadow','',agent,ttl=7200)
            return True
        else:
            gr.Warning(vhfront_msg('USER_PASS_INCORRECT'),duration=5) 
            return False

sp=IPSessionPlatform (
    AuthTokenClosure (
        __guest_tc,
        authnz = guest_authnz
    )
)
