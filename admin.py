from vhagilab import app_schema
from vhagilab import gradio_utils as gu
from vhagilab import user_registration, user_credential, notif_utils, fa2en_digits
from vhagilab.calendars_conversion import *
import gradio as gr

_save_busy = set()

def regulare_save(sess):
    global _save_busy
    if sess in _save_busy:
        return False
    else:
        _save_busy.add(sess)
        from time import sleep
        sleep(3.6)
        user_credential.save(app_schema)
        user_registration.save('natid')
        from vhagilab.thread_registry import dump_thread_registry
        dump_thread_registry()
        from vhagilab.cache import cache_dump
        cache_dump()
        _save_busy.remove(sess)
        return True

def format_visitdate(tstmp):
    from datetime import datetime
    dt=datetime.fromtimestamp(tstmp)
    y,m,d,_=gregorian2jalali(dt)
    return f"{y}/{m}/{d} {dt.hour}:{dt.minute}".translate(en2fa_translation)

with gr.Blocks(
    head=gu.head(),
    css=gu.css(table_safestyle=True),
    title=app_schema['TITLE'],
    theme=gu.themeFa(
        app_schema,
        primary_hue="zinc",
        secondary_hue="neutral",
        radius_size="none"
        ),
    fill_height=True,
    fill_width=True
) as admin:
    ### Add a session platform to the blocks
    from vhagilab.aSessionPlatform import aSessionPlatform
    gs = gu.grSessionPlatform(aSessionPlatform())
    ###
    with gr.Row():
        gr.Column(scale=1,min_width=20)
        with gr.Column(scale=6,min_width=600):
            synop=gr.Markdown('## مدیریت کاربران',rtl=True)
            reg_list= gr.Dataframe(
                [[]],
                label='Registration List',
                headers=['نام خانوادگی','نام','رایانامه','شماره همراه','شناسه ملی','تأیید',' ','آخرین بازدید'],
                column_widths=['22%','13%','18%','14%','11%','9%','%3','10%'],
                type='array',
                min_width=700,
                max_height=700,
                interactive=False,
                show_label=False
            )
            with gr.Row():
                save_btn = gr.Button('ذخیره')
                reload_btn = gr.Button('بازنشانی')
                ret_btn = gr.Button('بازگشت',link='/')
                gs.live_session(ret_btn.click)()
        gr.Column(scale=1,min_width=20)
    gu.add_tagline()
    @save_btn.click()
    def _on_save(request:gr.Request):
        gr.Info("در حال ذخیره‌سازی ...",duration=4)
        if regulare_save(request.session_hash):
            gr.Info("ذخیره‌سازی انجام شد.",duration=4)
    @reload_btn.click(outputs=reg_list)
    def on_reload_btn(request:gr.Request):
        global _save_busy
        gr.Info("در حال بازنشانی ...",duration=4)
        sess = request.session_hash
        if sess not in _save_busy:
            _save_busy.add(sess)
            from time import sleep
            sleep(3.6)
            user_credential.load(app_schema)
            user_registration.load()
            gr.Info("بازنشانی انجام شد.",duration=4)
            _save_busy.remove(sess)
            return init_admin(request)
        else:
            return gr.skip()
    def init_admin(request:gr.Request):
        regulare_save(request.session_hash)
        status = lambda s: '◻' if not s else '≣' if s==1 else '◼'
        rglist = [ [ r['surname'], r['name'], r['email'], r['mobile'], r['natid'], 
                    status(r['status']), '🗑', format_visitdate(r['visitdate']) ] for r in user_registration.rows() if r['status']>=0 ]
        if not rglist: rglist = [ list(' '*8) ]
        return gr.Dataframe (
            value=rglist,
            row_count=(len(rglist),'fixed'),
            col_count=(len(rglist[0]),'fixed')
        )
    ### Load app on the session platform
    gs.loadOnSessionPlatform(admin,init_admin,on_load_outputs=reg_list)
    @reg_list.select(inputs=reg_list,outputs=reg_list)
    def on_select_reg_list(rglist, evt:gr.SelectData, request:gr.Request):
        [i,j]=evt.index
        r=rglist[i]
        if j==6: # delete
            user_registration.set_status(r[4],'status',-1)
            del rglist[i]
            return rglist
        elif j==5: # check
            user='i'+fa2en_digits(r[4])
            if evt.value!='◻':
                user_registration.set_status(r[4],'status',0)
                user_credential.set_user_tag(user,'blocked')
                r[j]='◻'
                gr.Warning(f"عضویت {r[1]} {r[0]} {r[4]} لغو شد.",duration=5)
            else:
                reg_complete_notif = {}
                from random import randint
                passwd=str(randint(111201,999809))
                if user_credential.get_user_tag(user,'blocked'):
                    user_credential.del_user_tag(user,'blocked')
                    user_credential.__chpasswd(user,passwd)
                    reg_complete_notif['subject']= 'تغییر گذرواژه/فعال شدن دوباره دسترسی به سامانه '+app_schema['TITLE']
                else:
                    user_credential.register(user,passwd)
                    reg_complete_notif['subject']= 'تأیید ثبت نام در سامانه '+app_schema['TITLE']
                rec=dict(zip(['surname','name','email','mobile','natid'],r))
                user_credential.set_user_tags(user,rec)
                user_registration.set_status(r[4],'status',1)                    
                r[j]='≣'
                url = str(request.request.base_url)
                url = url[url.index("://")+3:]
                notif_template = notif_utils.template()
                reg_complete_notif['body']=notif_template.replace('%TITLE%', app_schema['TITLE']
                                                        ).replace('%URL%', url # 'agilab.sbu.ac.ir:/app/'
                                                        ).replace('%USER%', r[1]+' '+r[0]
                                                        ).replace('%USERNAME%', r[4]
                                                        ).replace('%PASSWORD%', passwd
                                                        )
                notif_utils.notify(user,reg_complete_notif)
            return rglist
        else:
            return gr.skip()
