_admin_email = ''
_email_pass = ''
_email_server = ''
_email_server_port = 465
_notif_template = '''کاربر گرامی %USER%

به سامانه %TITLE% خوش آمدید.
اکنون می‌توانید با استفاده از اطلاعات کاربری زیر به سامانه %URL% دسترسی داشته باشید.
نام کاربری: %USERNAME%
گذرواژه: %PASSWORD%

لطفا پس از اولین ورود، گذرواژه خود را تغییر دهید و از افشای آن به دیگران خودداری کنید.
'''

def template():
    global _notif_template
    return _notif_template

def xorcrypt(msg:bytes,scrt:bytes):
    enc=[]
    i=0; l=len(scrt)
    for a in msg:
        enc.append(a^scrt[i])
        i=(i+1)%l
    return bytes(enc)

def setup(config_file):
    global _admin_email, _email_pass, _email_server, _email_server_port, _notif_template
    with open(config_file+'.json',encoding='utf-8') as file:
        import json
        from base64 import b64decode
        config = json.load(file)
        _admin_email = config['ADMIN_EMAIL']
        _email_pass = xorcrypt( 
            b64decode( config['EMAIL_PASS'].encode('utf-8') ),
            config['ADMIN_EMAIL'].encode('utf-8')
        )
        _email_server = config['EMAIL_SRV']
        _email_server_port = config['PORT']
        _notif_template = config.get('TEMPLATE','@notif_template_en.txt')
        if _notif_template[0]=='@':
            try:
                with open(_notif_template[1:], 'r', encoding='utf-8') as notif_template_file:
                    _notif_template = notif_template_file.read()
            except FileNotFoundError:
                pass

def _sendmail(user_email,subject,body):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    message = MIMEMultipart()
    message['From'] = _admin_email
    message['To'] = user_email
    message['Subject'] = subject
    # Add Right-to-left conversion tags, RLM for proper embedding
    body = '\u202B'+body.replace('\n','\n\u202B')
    message.attach(MIMEText(body, 'plain'))
    try:
        if _email_server_port in [25,587]:
            with smtplib.SMTP(_email_server, _email_server_port, timeout=20) as server:
                server.starttls()
                server.login(_admin_email, _email_pass)
                server.sendmail(_admin_email, user_email, message.as_string())
        elif _email_server_port==465:
            with smtplib.SMTP_SSL(_email_server, 465, timeout=20) as server:
                server.login(_admin_email, _email_pass)
                server.sendmail(_admin_email, user_email, message.as_string())
        else:
          raise Exception("Unsupported SMTP port")
    except Exception as e:
        print(f"Error occurred on sending email: {e}")

def notify(user,msg,via=['email','sms']):
    from .user_credential import get_user_tag
    user_email = get_user_tag(user,'email')
    if user_email and via=='email' or isinstance(via,list) and 'email' in via:
        if isinstance(msg,str):
            subject="Notification for "+user
            body=msg
        else:
            subject=msg['subject']
            body=msg['body']
        _sendmail(user_email,subject,body)
        print(f"Email notification to {user_email} sent.\n{msg}")
    user_mobile = get_user_tag(user,'mobile')
    if user_mobile and via=='sms' or isinstance(via,list) and 'sms' in via:
        if isinstance(msg,dict):
            msg=msg['subject']+'\n'+msg['body']
        print(f"Sms notification to {user_mobile} sent.\n{msg}")
