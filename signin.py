from vhagilab import user_credential,fa2en_digits,app_schema
from vhagilab import gradio_utils as gu
import gradio as gr

def _on_login(username,password,target_path):
    user=username.strip()
    pswd=password.strip()
    if not user:
        return gr.Textbox(placeholder="نام کاربری نمی‌تواند خالی باشد",autofocus=True), gr.skip(), gr.skip()
    elif not pswd and user!='guest':
        return gr.skip(), gr.Textbox(placeholder="گذر واژه نمی‌تواند خالی باشد",autofocus=True), gr.skip()
    else:
        if user.isdigit():
            user='i'+fa2en_digits(user)
        if user_credential.get_user_tag(user,'blocked'):
            gr.Warning(f"حساب کاربری {username} مسدود است.",duration=5)
            return '','',' - '
        else:
            if user_credential.get_user_tag(user,'guest'):
                target_path = '/guest' 
            elif user_credential.get_user_tag(user,'special_guest'):
                target_path = '/special_guest' 
            if user==username:
                user=gr.skip()
            if pswd==password:
                pswd=gr.skip()
            return user,pswd,target_path

def _on_guest_login():
    user="guest"
    pswd=""
    if user_credential.get_user_tag(user,'blocked'):
        gr.Warning(f"حساب کاربری {user} مسدود است.",duration=5)
        return '','',' - '
    else:
        target_path = '/guest' 
    return user,pswd,target_path

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
) as signin:
    with gr.Row():
        target_path=gr.Textbox(value="",show_label=False,visible=False,interactive=False)
        gr.Column(scale=1,min_width=20)
        with gr.Column(scale=0,min_width=400):
            #gr.Markdown("### دستیار ...  \n## آزمایشگاه هوش مصنوعی جامع",rtl=True)
            gr.HTML('<center><img src="http://example.com/banner-320x132.gif" alt="EXAMPLE.COM" width="360"/></center>')
            gr.Markdown("## دستیار آموزشی",rtl=True)
            with gr.Group():
                username_txtbox=gr.Textbox(label="نام کاربری",max_length=60,rtl=False,text_align='right')
                password_txtbox=gr.Textbox(label="گذرواژه",type='password',max_length=60,rtl=False,text_align='right')
            login_btn=gr.Button("ورود",variant='primary')
            gr.Markdown("---  \n  \n---")
            with gr.Row():
                gr.Button("ثبت نام", link="/register/", scale=3)
                guest_btn=gr.Button("ورود مهمان", scale=1)
            gr.Markdown("---")
            resetPasswdTimer = gr.Timer(30)
            resetPasswdTimer.tick(lambda p:"" if p else gr.skip(),password_txtbox,password_txtbox,show_progress='hidden')
            password_txtbox.input(lambda p:19+len(p)%10 if p else gr.skip(),password_txtbox,resetPasswdTimer,show_progress='hidden')
            # gu.login_by( login_btn, lambda u,p,_:user_credential.auth(u,p), ...
            gu.login_by(login_btn,gu.signin_hub,username_txtbox,password_txtbox,
                        preauthfn=_on_login,
                        preauthinputs=[username_txtbox,password_txtbox,target_path],
                        preauthoutputs=[username_txtbox,password_txtbox,target_path],
                        login_target=target_path)
            gu.login_by(guest_btn,gu.signin_hub,username_txtbox,password_txtbox,
                        preauthfn=_on_guest_login,
                        preauthinputs=[],
                        preauthoutputs=[username_txtbox,password_txtbox,target_path],
                        login_target=target_path)
        gr.Column(scale=1,min_width=20)
    gu.add_tagline()
