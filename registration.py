lim_reg={}
last_lim_reg_purge=0

from vhagilab import app_schema
from vhagilab import gradio_utils as gu
from vhagilab import user_registration
import gradio as gr
from time import time

def gen_audits(rec):
    status=rec['status']+1
    visitdate=int(time())
    return {'status':status,'visitdate':visitdate}
user_registration.set_audits(gen_audits)
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
) as register:
    with gr.Row():
        gr.Column(scale=1,min_width=20)
        with gr.Column(scale=2,min_width=400):
            gr.HTML('<center><img src="http://example.com/banner-320x132.gif" alt="EXAMPLE.COM" width="360"/></center>')
            synop=gr.Markdown('## ثبت نام اولیه',rtl=True)
            with gr.Row():
                name=gr.Textbox(label="نام",rtl=True,max_length=40)
                surname=gr.Textbox(label="نام خانوادگی",rtl=True,max_length=60)
            with gr.Row():
                email=gr.Textbox(label="رایانامه",max_length=60,text_align='right',scale=7)
                mobile=gr.Textbox(label="شماره همراه",max_length=12,scale=5)
                gu.force_digitonly(mobile)
                natid=gr.Textbox(label="شناسه ملی",max_length=11,scale=5)
                gu.force_digitonly(natid)
            reg_btn=gr.Button("ارسال",variant='primary')
        gr.Column(scale=1,min_width=20)
    gu.add_tagline()
    relaxatb = lambda inptext: (gr.update(info=' ',autofocus=False),'## ثبت نام اولیه')
    name.blur(relaxatb,name,[name,synop],show_progress=False)
    surname.blur(relaxatb,surname,[surname,synop],show_progress=False)
    email.blur(relaxatb,email,[email,synop],show_progress=False)
    mobile.blur(relaxatb,mobile,[mobile,synop],show_progress=False)
    natid.blur(relaxatb,natid,[natid,synop],show_progress=False)
    @reg_btn.click(
        inputs=[name,surname,email,mobile,natid],
        outputs=[synop,reg_btn,name,surname,email,mobile,natid]
    )
    def on_register(name,surname,email,mobile,natid,request:gr.Request):
        rsynop = rreg_btn = rname = rsurname = remail = rmobile = rnatid = gr.skip()
        if not name:
            rsynop = '*<span style="color:#FF5040">نام نباید خالی باشد.</span>*'
            rname = gr.update(info='نام نباید خالی باشد',autofocus=True)
        elif not surname:
            rsynop = '*<span style="color:#FF5040">نام خانوادگی نباید خالی باشد.</span>*'
            rsurname = gr.update(info='نام خانوادگی نباید خالی باشد',autofocus=True)
        elif not natid:
            rsynop = '*<span style="color:#FF5040">شناسه ملی نباید خالی باشد.</span>*'
            rnatid = gr.update(info='شناسه ملی نباید خالی باشد',autofocus=True)
        elif not mobile and not email:
            rsynop = '*<span style="color:#FF5040">شماره همراه یا رایانامه را وارد کنید.</span>*'
        elif mobile and (not mobile.isdigit() or int('0'+mobile[:-9])!=9):
            rsynop = '*<span style="color:#FF5040">شماره همراه، صحیح نیست.</span>*'
            rmobile = gr.update(info='شماره همراه صحیح وارد کنید',autofocus=True)
        elif email and (not user_registration.is_valid_email(email)):
            rsynop = '*<span style="color:#FF5040">رایانامه، صحیح نیست.</span>*'
            remail = gr.update(info='رایانامه صحیح وارد کنید',autofocus=True)
        elif not natid.isdigit() or len(natid)!=10:
            rsynop = '*<span style="color:#FF5040">شناسه ملی، صحیح نیست.</span>*'
            rnatid = gr.update(info='شناسه ملی صحیح وارد کنید',autofocus=True)
        else:
            global lim_reg,last_lim_reg_purge
            _now = time()
            era = _now-86400
            if len(lim_reg)>=1000 and last_lim_reg_purge<_now-3600:
                last_lim_reg_purge=_now
                for k,v in list(lim_reg.items()):
                    if v[2]<era:
                        del lim_reg[k]
            client_ip = request.client.host
            nreg,lastreg = lim_reg.get(client_ip,(0,0))
            delta = era-lastreg
            if len(lim_reg)<1000 and (nreg<5 or 0<delta):
                user_registration.add(
                    {
                    'name':name,
                    'surname':surname,
                    'email':email,
                    'mobile':mobile,
                    'natid':natid,
                    'status':0,
                    'visitdate':int(time())
                    }
                )
                rsynop = '## ثبت نام با موفقیت انجام شد.'
                gr.Info("\u202Bنام کاربری و گذرواژه از طریق ایمیل یا پیامک برای شما فرستاده می‌شود.",duration=8)
                from time import sleep
                sleep(2)
                gr.Info("حساب کاربری شما، پس از بررسی و تأیید، فعال خواهد شد",duration=10)
                if delta>0:
                    lim_reg[client_ip]=(1,time())
                else:
                    lim_reg[client_ip]=(nreg+1,lastreg)
            elif len(lim_reg)>=1000:
                gr.Warning("ثبت نام موقتا بسته است. ۲۴ ساعت دیگر مجدد تلاش کنید.",duration=10)
            else:
                gr.Warning("حداکثر ۵ ثبت‌نام در هر ۲۴ ساعت، از یک پایانه امکانپذیر است.",duration=15)
            rreg_btn = gr.Button('بازگشت',link='/')
            rname = rsurname = remail = rmobile = rnatid = gr.update(interactive=False)
        return rsynop,rreg_btn,rname,rsurname,remail,rmobile,rnatid            
