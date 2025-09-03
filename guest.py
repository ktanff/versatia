import guestSessionPlatform
from vhagilab import app_schema
from vhagilab import gradio_utils as gu
from vhagilab.vhfront_msg import vhfront_msg
from vhagilab import *
import gradio as gr

ORGANIZATION = app_schema['ORGANIZATION']
CASE = app_schema['CASE']
guest_thread = {}

def tid(request:gr.Request):
    global guest_thread
    sess = request.session_hash
    t = guest_thread.get(sess,None)
    if not t:
        user = gs.user(request)
        thrd = create_thread(ORGANIZATION,CASE,user)
        show_json(thrd)
        t = guest_thread[sess] = thrd.id
    return t

def init_guest(request:gr.Request):
    guest_asst_info = assistant_info()
    user = gs.user(request)
    info = f"`{ORGANIZATION} - {CASE}  -- {user} :: {guest_asst_info}`  \n---"
    return info, gr.Chatbot(label=ftruncstr(guest_asst_info[5:],50),type='messages')

def ichat_fn(msg, history, request:gr.Request):
    if msg:
        response = ichat(tid(request),msg, model_id="BASIC_MODEL")
        if resolve_filecitations(response):
            return format_citations(response,"مآخذ:")
        return response.content[0].text.value
    else: return ""

def schat_fn(msg, history, request:gr.Request):
    if msg:
        for progmsg in schat(tid(request),msg, model_id="BASIC_MODEL"):
            yield progmsg.content[0].text.value
        try:
            progmsg
        except Exception:
            raise gr.Error(vhfront_msg('SRV_NOT_RESPONSE'))
        if resolve_filecitations(progmsg):
            yield format_citations(progmsg,"مآخذ:")
    else: yield ""

def pchat_fn(msg, history, request:gr.Request):
    if msg:
        i=0
        for progmsg in pchat(tid(request),msg, model_id="BASIC_MODEL"):
            if progmsg.status=="in_progress":
                i=(i+1)%5
                if i==1: blinking=' >>'
                if i==4: blinking=' __'
                yield progmsg.content[0].text.value+blinking
            else:
                yield progmsg.content[0].text.value
        try:
            progmsg
        except Exception:
            raise gr.Error(vhfront_msg('SRV_NOT_RESPONSE'))
        if resolve_filecitations(progmsg):
            yield format_citations(progmsg,"مآخذ:")
    else: yield ""

def guest_unload(request:gr.Request):
    global guest_thread
    t = guest_thread.pop(request.session_hash,None)
    if t:
        client().beta.threads.delete(t)

with gr.Blocks(
    head=gu.head(),
    css=gu.css(),
    title=app_schema['TITLE'],
    theme=gu.themeFa(
        app_schema,
        primary_hue="zinc",
        secondary_hue="neutral",
        radius_size="none"
        ),
    fill_height=True,
    fill_width=True
) as guest:
    ### Add a session platform to the blocks
    # Guest has a special session platform
    gs = gu.grSessionPlatform(guestSessionPlatform.sp,on_unload=guest_unload,)
    ###
    with gr.Row(): #max_height=1000
        with gr.Column(scale=5,min_width=400):
            chatbox = gr.Chatbot(
                scale=1,
                min_height=400,
                height='83vh',
                type='messages',
                rtl = True,
                show_copy_all_button = True,
                label = '---',
                avatar_images = ("user.ico","ai.ico")
            )
            inputbox = gr.Textbox(
                rtl = True,
                lines = 1,
                max_lines = 3,
                #scale=0,
                autofocus = True,
                show_label = False,
                submit_btn = "◁",
                placeholder = "اینجا تایپ کنید ..."
            )
        with gr.Column(scale=1,min_width=280,variant='compact') as sidepanel:
            info = gr.Markdown(label="Signature",show_label=True,container=True,min_height=40,max_height=70)
            previewpane = gr.Markdown(
                show_label=False,
                show_copy_button=False,
                container=True,
                height='67vh',
                min_height=150
            )
            with gr.Accordion("::: : ::: : ::: : ::: : ::: : ::: : ::: : ::: : ::: : :::",open=True) as acrdn:
                gs.signout_by(gr.Button("خروج"))
    gu.add_tagline()
    ### Load app on the session platform
    gs.loadOnSessionPlatform( guest,init_guest,
                              on_load_outputs=[info,chatbox],
                              alive_check_every=10
                            )
    gs.chatIntegrateOnLiveSession(pchat_fn,inputbox,chatbox,submit_btn="◁")
    @gs.live_session(acrdn.expand,outputs=previewpane,show_progress=False)
    def _adjust_shrink_pane():
        return gr.update(height='67vh')
    @gs.live_session(acrdn.collapse,outputs=previewpane,show_progress=False)
    def _adjust_expand_pane():
        return gr.update(height='73vh')
    @gs.live_session( chatbox.clear, inputbox, chatbox, show_progress=False,
                      js="(x) => confirm('از حذف این رشته گفتگو، اطمینان دارید؟')"
                    )
    def _on_clear(confirmed, request:gr.Request):
        global guest_thread
        sess=request.session_hash
        t = guest_thread.get(sess,None)
        if t:
            if confirmed=="True":
                guest_thread[sess]=None
                client().beta.threads.delete(t)
                return []
            else:
                gr.Info("حذف رشته، لغو شد ✓")
                history = flip_thread(t,1)
                return history
        else:
            return gr.skip()
