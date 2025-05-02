_credentials={}
__credential_settings_error = "Illegal credential format: either a {username:[password,tags]} dictionary, or a @-prepended filename of a file containing such a dictionary is permitted."

def auth(user,passwd):
    import bcrypt
    from .user_registration import audit
    return (user in _credentials and 
        bcrypt.checkpw(passwd.encode('utf-8'), _credentials[user][0].encode('utf-8')) and 
        audit(_credentials[user][1]))

def is_valid_username(u):
    if u[0]=='_': return False
    if u[-1]=='_': return False
    if not u.isidentifier(): return False
    from keyword import iskeyword
    if iskeyword(u): return False
    js_reserved_words_but_py={
        'long','float','char','enum','debugger','extends','package','abstract','native','case',
        'function','throw','public','default','goto','switch','double','eval','private','short',
        'final','volatile','int','arguments','do','delete','true','new','boolean','protected',
        'catch','throws','instanceof','transient','byte','synchronized','let','false','null',
        'const','super','interface'
    }
    if u in js_reserved_words_but_py: return False
    return True

def __chpasswd(user,passwd):
    assert user in _credentials, f"No user as {user} exists."
    import bcrypt
    salt = bcrypt.gensalt()
    hashpw = bcrypt.hashpw(passwd.encode('utf-8'),salt)
    hashpw = hashpw.decode('utf-8')
    _credentials[user][0]=hashpw
    _credentials['*']=None

def chpasswd(user,cur_passwd,new_passwd):
    assert auth(user,cur_passwd), f"Faild authentication! Current password is incorrect or no user as {user} exists."
    __chpasswd(user,new_passwd)

def register(user,passwd):
    assert is_valid_username(user), f"Invalid username: {user}"
    assert user not in _credentials, f"Error! Previously registered user, {user}."
    _credentials[user]=['',{}]
    __chpasswd(user,passwd)

def get_user_tags(user):
    return list(_credentials.get(user,[None,{}])[1].keys())

def get_user_tag(user,tag,default=None):
    return _credentials.get(user,[None,{}])[1].get(tag,default)

def del_user_tag(user,tag):
    assert user in _credentials, f"Error! {user} not registered!"
    if tag in _credentials[user][1]:
        del _credentials[user][1][tag]
        _credentials['*']=None

def set_user_tag(user,tag,value=True):
    if not value: return del_user_tag(user,tag)
    assert user in _credentials, f"Error! {user} not registered!"
    _credentials[user][1][tag]=value
    _credentials['*']=None

def clear_user_tags(user):
    assert user in _credentials, f"Error! {user} not registered!"
    if _credentials[user][1] is not {}:
        _credentials[user][1]={}
        _credentials['*']=None

def set_user_tags(user,tags):
    assert user in _credentials, f"Error! {user} not registered!"
    for t in list(tags.keys()):
        if tags[t] is None:
            del tags[t]
    if tags is not {}:
        _credentials[user][1]=tags
        _credentials['*']=None

def add_user_tags(user,tags):
    assert user in _credentials, f"{user} not registered!"
    for t in list(tags.keys()):
        if tags[t] is None:
            del tags[t]
            if t in _credentials[user][1]:
                del _credentials[user][1][t]
                _credentials['*']=None
    if tags is not {}:
        _credentials[user][1]|=tags
        _credentials['*']=None

import json

def load(app_schema):
    global _credentials
    _credentials = app_schema['CREDENTIALS']
    if type(_credentials) is str:
        assert _credentials[0]=='@', __credential_settings_error
        with open(_credentials[1:]+'.json',encoding='utf-8') as _credentials_file:
            _credentials = json.load(_credentials_file)
    for u in _credentials:
        assert is_valid_username(u), f"Invalid username: {u}"

def save(app_schema):
    if '*' in _credentials:
        _credentials.pop('*')
        old_credentials = app_schema['CREDENTIALS']
        if type(old_credentials) is str:
            assert old_credentials[0]=='@', __credential_settings_error
            with open(old_credentials[1:]+'.json','w',encoding='utf-8') as _credentials_file:
                json.dump(_credentials,_credentials_file,indent=3,ensure_ascii=False)
        else:
            app_schema['CREDENTIALS'] = _credentials
            with open('app_schema.json','w',encoding='utf-8') as _app_schema_file:
                json.dump(app_schema,_app_schema_file,indent=3,ensure_ascii=False)

def deluser(user):
    if user in _credentials:
        del _credentials[user]
        _credentials['*']=None

def cli():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--adduser", dest="username", type=str, help="Add user.")
    parser.add_argument("-p", "--passwrod", dest="username_to_change_password", type=str, help="Change password.")
    parser.add_argument("-r", "--deluser", dest="username_to_be_deleted", type=str, help="Delete user.")
    parser.add_argument("-t", "--tag", dest="username_to_set_tag", type=str, help="Set tag for user.")
    args = parser.parse_args()
    if args.username:
        passwd=input("Password: ")
        register(args.username,passwd)
        print(f"{args.username} is successfully added.")
        return True
    if args.username_to_change_password:
        assert args.username_to_change_password in _credentials, f"No {args.username_to_change_password} exists."
        new_passwd=input("New password: ")
        __chpasswd(args.username_to_change_password,new_passwd)
        print(f"Password for {args.username_to_change_password} is successfully changed.")
        return True
    if args.username_to_be_deleted:
        deluser(args.username_to_be_deleted)
        print(f"{args.username_to_be_deleted} is successfully deleted.")
        return True
    if args.username_to_set_tag:
        tag=input("tag: ").strip('"\'')
        val=input("value: ")
        tags=json.loads('{'+f'"{tag}":{val}'+'}')
        add_user_tags(args.username_to_set_tag,tags)
        print(f"{tag} for {args.username_to_set_tag} is set to {val}.")
        return True
    return False
