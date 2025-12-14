from vhagilab import app_schema
from vhagilab import gradio_utils as gu
from vhagilab import user_registration, user_credential, notif_utils, fa2en_digits, ezspl_randpasswd
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
    with gu.loadSessionPlatformOnBlocks(aSessionPlatform(), admin) as gs:
        with gr.Row():
            gr.Column(scale=1,min_width=20)
            with gr.Column(scale=6,min_width=600):
                synop=gr.Markdown('## مدیریت کاربران',rtl=True)
                reg_list= gr.Dataframe(
                    [[]],
                    label='Registration List',
                    headers=['نام خانوادگی','نام','رایانامه','شماره همراه','نام کاربری','تأیید',' ','آخرین بازدید'],
                    column_widths=['18%','16%','16%','11%','11%','7%','%7','14%'],
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
            rglist = [ [ 'Special Guest' if r.get('special_guest') else r['surname'], r['name'], r['email'], r['mobile'], r['natid'], 
                        status(r['status']), '-' if r.get('special_guest') else '🗑', format_visitdate(r['visitdate']) ] for r in user_registration.rows() if r['status']>=0 ]
            if not rglist: rglist = [ list(' '*8) ]
            return gr.Dataframe (
                value=rglist,
                row_count=(len(rglist),'fixed'),
                col_count=(len(rglist[0]),'fixed')
            )
        ### Load callback
        gs.loaded.success(init_admin,outputs=reg_list)
        @reg_list.select(inputs=reg_list,outputs=reg_list)
        def on_select_reg_list(rglist, evt:gr.SelectData, request:gr.Request):
            [i,j]=evt.index
            r=rglist[i]
            if j==6: # delete
                if r[j]=='🗑':
                    user_registration.set_status(r[4],'status',-1)
                    del rglist[i]
                return rglist
            elif j==5: # check
                special_guest = r[6]=='-'
                if special_guest:
                    user = r[4]
                else:
                    user='i'+fa2en_digits(r[4])
                if evt.value!='◻':
                    user_registration.set_status(r[4],'status',0)
                    user_credential.set_user_tag(user,'blocked')
                    r[j]='◻'
                    gr.Warning(f"عضویت {r[1]} {r[0]} {r[4]} لغو شد.",duration=5)
                else:
                    passwd=ezspl_randpasswd(6)
                    reg_complete_notif = {}
                    if user_credential.get_user_tag(user,'blocked'):
                        user_credential.del_user_tag(user,'blocked')
                        user_credential.__chpasswd(user,passwd)
                        reg_complete_notif['subject']= 'تغییر گذرواژه/فعال شدن دوباره دسترسی به سامانه '+app_schema['TITLE']
                    else:
                        user_credential.register(user,passwd)
                        reg_complete_notif['subject']= 'تأیید ثبت نام در سامانه '+app_schema['TITLE']
                    rec=dict(zip(['surname','name','email','mobile','natid'],r))
                    if special_guest:
                        rec['special_guest']=True
                    user_credential.set_user_tags(user,rec)
                    user_registration.set_status(r[4],'status',1)                    
                    r[j]='≣'
                    gr.Warning(f"عضویت {r[1]} {r[0]} {r[4]} فعال شد.",duration=5)
                    if special_guest:
                        gr.Warning(f"گذرواژه برای {r[1]}:  {passwd}",duration=20)
                    else:
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
                        gr.Warning(f"گذرواژه جدید برای {r[1]} {r[0]} به {r[2]} ایمیل شد.",duration=7)
                return rglist
            else:
                return gr.skip()
