from vhagilab import aSessionPlatform, user_credential
from vhagilab.vhfront_msg import vhfront_msg
import gradio as gr

def authnz(usr,psw,agn):
    x = user_credential.auth(usr,psw)
    x or gr.Warning(vhfront_msg('USER_PASS_INCORRECT'),duration=5)
    return x

aSessionPlatform.setup(authnz)
