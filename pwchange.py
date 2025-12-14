from vhagilab import app_schema
from vhagilab import gradio_utils as gu
from vhagilab import user_credential
import gradio as gr

def _on_pwchange(cur_pswd,new_pswd,rep_new_pswd,request:gr.Request):
    cur_pswd=cur_pswd.strip()
    new_pswd=new_pswd.strip()
    rep_new_pswd=rep_new_pswd.strip()
    if not cur_pswd:
        return gr.Textbox(placeholder="گذرواژه فعلی نمی‌تواند خالی باشد.",autofocus=True), gr.skip(), gr.skip(), gr.skip()
    elif not new_pswd:
        return gr.skip(), gr.Textbox(placeholder="گذرواژه جدید نمی‌تواند خالی باشد.",autofocus=True), "", gr.skip()
    elif (len(new_pswd)<8 or 
          not( any(c.isdigit() for c in new_pswd) and any(c.isalpha() for c in new_pswd))):
        newpswdconst = "طول گذرواژه جدید حداقل باید ۸ نویسه و ترکیبی از ارقام [0-9] و حروف [a-z] یا [A-Z] باشد."
        gr.Warning(newpswdconst,duration=5)
        return gr.skip(), gr.Textbox("",placeholder=newpswdconst,autofocus=True), "", gr.skip()
    elif any(new_pswd[i]==new_pswd[i+1] and new_pswd[i]==new_pswd[i+2] for i in range(len(new_pswd)-2)):
        newpswdconst = "برای تعریف گذرواژه جدید، یک نویسه را سه بار یا بیشتر پشت سر هم تکرار نکنید"
        gr.Warning(newpswdconst,duration=5)
        return gr.skip(), gr.Textbox("",placeholder=newpswdconst,autofocus=True), "", gr.skip()
    elif new_pswd==cur_pswd:
        newpswdconst = "گذرواژه جدید نمی‌تواند همانند گذرواژه قدیم باشد."
        gr.Warning(newpswdconst,duration=5)
        return gr.skip(), gr.Textbox("",placeholder=newpswdconst,autofocus=True), "", gr.skip()
    elif not rep_new_pswd:
        return gr.skip(), gr.skip(), gr.Textbox(placeholder="گذرواژه جدید را اینجا دوباره بنویسید!",autofocus=True), gr.skip()
    elif rep_new_pswd!=new_pswd:
        return gr.skip(), gr.skip(), gr.Textbox("",placeholder="گذرواژه جدید به درستی بازنویسی نشده است!",autofocus=True), gr.skip()
    else:
        user = gs.user(request)
        try:
            user_credential.chpasswd(user,cur_pswd,new_pswd)
            user_credential.save(app_schema)
            return "","","",""
        except AssertionError:
            gr.Warning("گذرواژه فعلی، صحیح نیست!",duration=5)
            return "",gr.skip(),gr.skip(),gr.skip()

with gr.Blocks(
    head=gu.head(),
    css=gu.css(agradeintbackground=True),
    title=app_schema['TITLE'],
    theme=gu.themeFa(
        app_schema,
        primary_hue="zinc",
        secondary_hue="neutral",
        radius_size="none"
        ),
    fill_height=True,
    fill_width=True
) as pwchange:
    ### Add a session platform to the blocks
    from vhagilab.aSessionPlatform import aSessionPlatform
    with gu.loadSessionPlatformOnBlocks(aSessionPlatform(), pwchange) as gs:
        with gr.Row():
            gr.Column(scale=1,min_width=20)
            with gr.Column(scale=0,min_width=400):
                gr.Markdown("### تغییر گذرواژه")
                with gr.Group():
                    cur_pswd_txtbox=gr.Textbox(label="گذرواژه فعلی",type='password',max_length=60,rtl=False,text_align='right')
                    new_pswd_txtbox=gr.Textbox(label="گذرواژه جدید",type='password',max_length=60,rtl=False,text_align='right')
                    rep_new_pswd_txtbox=gr.Textbox(label="بازنویسی گذرواژه جدید",type='password',max_length=60,rtl=False,text_align='right')
                with gr.Row():
                    ok_btn=gr.Button("تغییر گذرواژه",variant='primary')
                    cancel_btn=gr.Button("انصراف",link="/")
                    done_txtbox=gr.Textbox(" - ",visible=False)
                resetPasswdTimer = gr.Timer(90)
                resetPasswdTimer.tick(lambda p:"" if p else gr.skip(),cur_pswd_txtbox,cur_pswd_txtbox,show_progress='hidden')
                cur_pswd_txtbox.input(lambda p:79+len(p)%10 if p else gr.skip(),cur_pswd_txtbox,resetPasswdTimer,show_progress='hidden')
            gr.Column(scale=1,min_width=20)
        gu.add_tagline()
        from vhagilab.lambdas import nullfn
        ok_btn.click (
            fn = _on_pwchange,
            inputs = [cur_pswd_txtbox,new_pswd_txtbox,rep_new_pswd_txtbox],
            outputs = [cur_pswd_txtbox,new_pswd_txtbox,rep_new_pswd_txtbox,done_txtbox]
            ).success (
                fn = nullfn,
                inputs = done_txtbox,
                js = "function(done){if(done==done.trim()){location.replace('/signout');} }"
            )
