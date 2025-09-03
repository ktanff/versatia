from vhagilab import app_schema
from vhagilab import gradio_utils as gu
from vhagilab.vhfront_msg import vhfront_msg
from vhagilab import *
from time import sleep
import gradio as gr

ORGANIZATION = app_schema['ORGANIZATION']
CASE = app_schema['CASE']
app_thread={}
TEMP_THREAD_LABEL="         [ موقت ]"
citeUxModes=['آماده-بسته','بازدرخواست','همیشه باز']
toneModes = list(persona['TONES'])
botChoices = list(persona['BOTS'].items())

def per_thread_instruction(user):
    per_thread_inst = persona['PER_THREAD_INST']
    per_thread_inst = per_thread_inst.replace('%ORGANIZATION%',persona['ORGANIZATION']
                                    ).replace('%CASE%',persona['CASE']
                                    ).replace('%SUBJECT%',persona['SUBJECT']
                                    ).replace('%USER%',user
                                    ).replace('%NOTE%',persona['NOTE']
                                    )
    return per_thread_inst

def per_day_instruction():
    per_day_inst = persona['PER_DAY_INST']
    per_day_inst = per_day_inst.replace('%TODAY%',today_date_line())
    return per_day_inst

def tone_instruction(tone_mode):
    tm = toneModes[tone_mode]
    tone_inst = "از این به بعد، برای لحن و حالت بیان پاسخ‌های خود، از دستور زیر پیروی کن: \n **Output Tone Instruction:**\n" + persona['TONES'][tm]
    return tone_inst

def tid(request:gr.Request,tone_mode=0,asst_id=''):
    from time import time as _now
    tday = int((_now()+12600)//86400)
    global app_thread
    sess = request.session_hash
    t = app_thread.get(sess,None)
    if not t:
        user = gs.user(request)
        thrd = create_thread(ORGANIZATION,CASE,user)
        show_json(thrd)
        t = app_thread[sess] = thrd.id
        set_thread_tag(t,"day",tday)
        if tone_mode:
            set_thread_tag(t,"tone",tone_mode)
        tinst = f"{per_thread_instruction(user)}  \n  \n{per_day_instruction()}  \n  \n{tone_instruction(tone_mode)}"
        ichat(t,tinst,closed=True,verbose=True)
        sleep(2)
        if asst_id:
            set_thread_tag(t,"bot",asst_id)
    else:
        ## Refresh the per-day tag and the closed-msg instruction
        if int( get_thread_tag(t,"day") ) != tday:
            set_thread_tag(t,"day",tday)
            ichat(t,per_day_instruction(),closed=True,verbose=True)
            sleep(2)
        ## Refresh tone tag and the closed-msg instruction
        cur_tone_mode = int( get_thread_tag(t,"tone",0) )
        if tone_mode != cur_tone_mode:
            set_thread_tag(t,"tone",tone_mode)
            ichat(t,tone_instruction(tone_mode),closed=True)
            sleep(2)
        ## Set bot
        cur_bot = get_thread_tag(t,"bot")
        if asst_id != cur_bot:
            set_thread_tag(t,"bot",asst_id)        
    return t

def load_choices(user,default=None):
    choices = [ ( '         '+get_thread_tag(t,"title"), t ) for t in get_threads(user) ]
    if default:
        choices.append(default)
    return choices[::-1]

def init_app(request:gr.Request):
    asst_info = assistant_info(botChoices[0][1])
    user = gs.user(request)
    # clientmate_user= request.username
    # browser = request.headers['user-agent']
    # client_ip = request.client.host
    info = f"`{ORGANIZATION} - {CASE}  -- {user} :: {asst_info}`  \n---"
    citeuxmode = user_credential.get_user_tag(user,'CiteUxMode',0)
    return ( gr.update(visible=True) if user_credential.get_user_tag(user,'admin') else gr.skip(),
             info,
             gr.Chatbot(label=ftruncstr(asst_info[5:],45),type='messages'),
             citeUxModes[citeuxmode],
             gr.Dropdown(choices=load_choices(user,(TEMP_THREAD_LABEL,"")),value="")
           )

def ichat_fn(msg, history, tone_mode, asst_id, request:gr.Request):
    if msg:
        sess = request.session_hash
        response = ichat(tid(request,tone_mode,asst_id),msg,asst_id)
        if resolve_filecitations(response):
            user = gs.user(request)
            citeuxmode = user_credential.get_user_tag(user,'CiteUxMode',0)
            if citeuxmode!=1:
                augment_quotes(response)
            return format_citations(response,"مآخذ:",details_open=(citeuxmode==2))
        return response.content[0].text.value
    return ""

def schat_fn(msg, history, tone_mode, asst_id, request:gr.Request):
    if msg:
        sess = request.session_hash
        for progmsg in schat(tid(request,tone_mode,asst_id),msg,asst_id):
            yield progmsg.content[0].text.value
        try:
            if resolve_filecitations(progmsg):
                user = gs.user(request)
                citeuxmode = user_credential.get_user_tag(user,'CiteUxMode',0)
                if citeuxmode!=1:
                    augment_quotes(progmsg)
                yield format_citations(progmsg,"مآخذ:",details_open=(citeuxmode==2))
        except Exception:
            raise gr.Error(vhfront_msg('SRV_NOT_RESPONSE'))
    else: yield ""

def pchat_fn(msg, history, tone_mode, asst_id, request:gr.Request):
    if msg:
        sess = request.session_hash
        i=0
        for progmsg in pchat(tid(request,tone_mode,asst_id),msg,asst_id):
            if progmsg.status=="in_progress":
                i=(i+1)%5
                if i==1: blinking=' >>'
                if i==4: blinking=' __'
                yield progmsg.content[0].text.value+blinking
            else:
                yield progmsg.content[0].text.value
        try:
            if resolve_filecitations(progmsg):
                user = gs.user(request)
                citeuxmode = user_credential.get_user_tag(user,'CiteUxMode',0)
                if citeuxmode!=1:
                    augment_quotes(progmsg)
                yield format_citations(progmsg,"مآخذ:",details_open=(citeuxmode==2))
        except Exception:
            raise gr.Error(vhfront_msg('SRV_NOT_RESPONSE'))
    else: yield ""

def app_unload(request:gr.Request):
    global app_thread
    sess = request.session_hash
    t = app_thread.pop(sess,None)
    if t and get_thread_tag(t,"title")=="Temp":
        client().beta.threads.delete(t)

def promote_thread(history, chsn_thrd, request:gr.Request):
    if not chsn_thrd and len(history)>6:
        global app_thread
        sess = request.session_hash
        t = app_thread[sess]
        assert get_thread_tag(t,"title")=="Temp", f"Illegal interaction trace; {request}"
        title_rsp = ichat( t,
                           "یک عنوان سه کلمه‌ای مناسب برای رشته گفتگوی حاضر پیشنهاد بده و به انتهای آن، تاریخ امروز در تقویم شمسی را به صورت عددی روز-ماه بچسبان.",
                           asst_id = 'MENTOR_ASST', closed=True, verbose=True )
        sleep(2)
        set_thread_tag(t, "title", title_rsp.content[0].text.value.strip('"'))
        # undo_chat(t,closed=True) is not required yet, because msg and resp are "closed"!
        u = gs.user(request)
        add_thread(u,t)
        return gr.skip(),gr.Dropdown(choices=load_choices(u),value=t)
    else:
        return gr.skip(),gr.skip()

def on_clear(confirmed, request:gr.Request):
    global app_thread
    sess=request.session_hash
    t = app_thread.get(sess,None)
    if t:
        u = gs.user(request)
        if confirmed=="True":
            app_thread[sess]=None
            title = get_thread_tag(t,"title")
            client().beta.threads.delete(t)
            if title=="Temp":
                return gr.skip(),[]
            else:
                del_thread(u,t)
                return gr.Dropdown(choices=load_choices(u,(TEMP_THREAD_LABEL,"")),value=""),[]
        else:
            gr.Info("حذف رشته، لغو شد ✓")
            history = flip_thread(t,user_credential.get_user_tag(u,'CiteUxMode',0))
            return gr.skip(), history
    else:
        return gr.skip(),gr.skip()

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
) as app:
    ### Add a session platform to the blocks
    from vhagilab.aSessionPlatform import aSessionPlatform
    gs = gu.grSessionPlatform(aSessionPlatform(),on_unload=app_unload)
    ###
    with gr.Row(): #max_height=1000
        with gr.Column(scale=5,min_width=400):
            chatbox = gr.Chatbot(
                scale=1,
                min_height=400,
                height='83vh',
                type='messages',
                rtl = True,
                show_copy_button = False, 
                show_copy_all_button = True,
                label = '===',
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
            new_btn = gr.Button("رشته جدید",variant='primary')
            with gr.Group():
                with gr.Row():
                    gr.Textbox("رشته جاری",show_label=False,rtl=True,min_width=80,scale=6,interactive=False,container=False)
                    clear_btn = gr.ClearButton(value='',icon="wastepaper-basket.ico",size='lm',scale=1,min_width=20)
                chosen_thread = gr.Dropdown (
                    label='تغییر رشته جاری',
                    show_label=False,
                    multiselect=False,
                    container=False
                )
            previewpane = gr.Markdown(
                show_label=False,
                show_copy_button=False,
                container=True,
                height='52vh',
                min_height=50
            )
            with gr.Accordion (
                "::: : ::: : ::: : ::: : ::: : ::: : ::: : ::: : ::: : :::",
                open=False
            ) as acrdn:
                toneMode = gr.Radio (
                    toneModes,
                    value=toneModes[0],                    
                    type='index',
                    label='بیان',
                    show_label=True,
                    container=True
                )
                chosen_bot = gr.Dropdown (
                    choices=botChoices,
                    value=botChoices[0][1],
                    label='دستیار',
                    show_label=True,
                    multiselect=False,
                    container=True
                )
                citeUxMode = gr.Radio (
                    citeUxModes,
                    type='index',
                    label='نمایش مآخذ',
                    show_label=True,
                    container=True
                )
                #gu.otherlogin_by(gr.Button("Login as other user"))
                gr.Button("تغییر گذرواژه",link='./pwchange/')
                admin_btn = gr.Button("مدیریت کاربران",visible=False,link="./admin/")
                gs.signout_by(gr.Button("خروج"))
    gu.add_tagline()
    ### Load app on the session platform
    gs.loadOnSessionPlatform (
        app,
        init_app,
        on_load_outputs=[admin_btn,info,chatbox,citeUxMode,chosen_thread]
    )
    gs.chatIntegrateOnLiveSession( pchat_fn,inputbox,chatbox,
                                   extra_inputs=[toneMode,chosen_bot],
                                   pre_response=promote_thread,
                                   pre_extra_inputs=[chosen_thread],
                                   pre_extra_outputs=[chosen_thread],
                                   submit_btn="◁"
                                 )
    @gs.live_session(acrdn.expand,outputs=[previewpane,info],show_progress=False)
    def _adjust_shrink_pane(request:gr.Request):
        user = gs.user(request)
        if user_credential.get_user_tag(user,'admin'):
            return gr.update(visible=False),gr.update(visible=False)
        else:
            return gr.update(visible=False),gr.skip()
        #s='8vh' if user_credential.get_user_tag(user,'admin') else '10vh'
        #return gr.update(height=s)
    @gs.live_session(acrdn.collapse,outputs=[previewpane,info],show_progress=False)
    def _adjust_expand_pane(request:gr.Request):
        user = gs.user(request)
        if user_credential.get_user_tag(user,'admin'):
            return gr.update(visible=True),gr.update(visible=True)
        else:
            return gr.update(visible=True),gr.skip()
        #return gr.update(height='52vh')
    @gs.live_session(citeUxMode.input,citeUxMode,None,show_progress=False)
    def _setCiteUxMode(mode, request:gr.Request):
        user = gs.user(request)
        user_credential.set_user_tag(user,'CiteUxMode',mode)
    @gs.live_session(inputbox.stop,None,inputbox,show_progress=False)
    def _cancel_run(request:gr.Request):
        cancel_run(app_thread[request.session_hash])
        return gr.update(submit_btn="◁",stop_btn=False)
    @gs.live_session(chatbox.retry,[chatbox,toneMode,chosen_bot],chatbox,show_progress=False)
    def _chat_retry(history,tone_mode,asst_id,request:gr.Request):
        global app_thread
        sess = request.session_hash
        t = app_thread[sess]
        user = gs.user(request)        
        if ( user_credential.get_user_tag(user,'CiteUxMode',0)==1 and
             "</details>" not in history[-1]['content'] and
             "مآخذ:" in history[-1]['content'] ):
            lastresp = last_message(t)
            if augment_quotes(lastresp):
                history[-1]['content'] = format_citations(lastresp,"مآخذ:",details_open=True)
                yield history
                return
        undo_chat(t)
        sleep(2)
        for m in pchat_fn(history[-2]['content'],history[:-2],tone_mode,asst_id,request):
            history[-1]['content']=m
            yield history
    @gs.live_session(chatbox.undo,chatbox,[inputbox,chosen_thread,chatbox],show_progress=False)
    def _chat_undo(history,request:gr.Request):
        global app_thread
        sess = request.session_hash
        undo_chat(app_thread[sess])
        if len(history) > 2:
            return history[-2]['content'],gr.skip(),history[:-2]
        else:
            return "",*on_clear('True',request)
    @gs.live_session(new_btn.click,chosen_thread,[chosen_thread,chatbox])
    def _new_thread(chsn_thrd, request:gr.Request):
        global app_thread
        sess = request.session_hash
        t = app_thread.get(sess,None)
        app_thread[sess]=None
        if t:
            if chsn_thrd:
                u = gs.user(request)
                return gr.Dropdown(choices=load_choices(u,(TEMP_THREAD_LABEL,"")),value=""),[]
            else:
                assert get_thread_tag(t,"title")=="Temp", f"Illegal interaction trace; {request}"
                client().beta.threads.delete(t)
                return gr.skip(),[]
        return gr.skip(), gr.skip()
    @gs.live_session(chosen_thread.select,chosen_thread,[chosen_thread,toneMode,chosen_bot,chatbox])
    def _on_change_thread(chsn_thrd,request:gr.Request):
        assert chsn_thrd, f"Illegal interaction trace; {request}"
        global app_thread
        sess = request.session_hash
        t = app_thread.get(sess,None)
        if t and get_thread_tag(t,"title")=="Temp":
            client().beta.threads.delete(t)
        app_thread[sess]=chsn_thrd
        u = gs.user(request)
        history = flip_thread(chsn_thrd,user_credential.get_user_tag(u,'CiteUxMode',0))
        tone_mode = int(get_thread_tag(chsn_thrd,"tone",0))
        chsn_bot = get_thread_tag(chsn_thrd,"bot")
        if chsn_bot not in persona['BOTS'].values():
            chsn_bot=botChoices[0][1]
        return gr.Dropdown(choices=load_choices(u),value=chsn_thrd),toneModes[tone_mode],chsn_bot,history
    @gs.live_session(chosen_bot.change,chosen_bot,[info,chatbox],show_progress=False)
    def _on_change_bot(chsn_bot,request:gr.Request):
        asst_info = assistant_info(chsn_bot)
        user = gs.user(request)
        info_line = f"`{ORGANIZATION} - {CASE}  -- {user} :: {asst_info}`  \n---"
        return info_line, gr.update(label=asst_info[5:43])
    gs.live_session( chatbox.clear, inputbox, [chosen_thread,chatbox], show_progress=False,
                      js="(x) => confirm('از حذف این رشته گفتگو، اطمینان دارید؟')"
                    ) (on_clear)
    gs.live_session( clear_btn.click, inputbox, [chosen_thread,chatbox], show_progress=False,
                      js="(x) => confirm('از حذف این رشته گفتگو، اطمینان دارید؟')"
                    ) (on_clear)
    
