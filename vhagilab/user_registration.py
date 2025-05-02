def is_valid_email(email):
    import re
    regex = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex,email)

def email2validusername(username):
    return username.replace('.','').replace('+','_').replace('-','_').replace('%','_').replace('@','_a_')

_reg_schema={}
__key=None
_audit_tags=lambda rec:{'status':1}
def set_audits(gen_audits):
    global _audit_tags
    _audit_tags=gen_audits

def load():
    import json
    global _reg_schema,__key
    _reg_schema={}
    with open('registrations.json',encoding='utf-8') as reg_schema_file:
        for r in json.load(reg_schema_file):
            if not __key:
                __key = r
            elif isinstance(r,dict):
                if __key not in r:
                    print(f"Discard a registery without key field \"{__key}\", [{r}]")
                else:
                    _reg_schema[r[__key]] = r

def save(key=None):
    from json import dump
    global _reg_schema,__key
    if not __key:
        __key=key
    if __key:
        with open('registrations.json','w',encoding='utf-8') as reg_schema_file:
            dump([__key,*_reg_schema.values()],reg_schema_file,indent=3,ensure_ascii=False)

def add(rec):
    if __key in rec:
        from json import loads, dumps
        _reg_schema[rec[__key]]=loads(dumps(rec))

def rows():
    from json import loads, dumps
    for r in _reg_schema.values():
        yield loads(dumps(r))

def set_status(key,state_tag,state_val):
    if key in _reg_schema:
        _reg_schema[key][state_tag]=state_val

def audit(rec):
    global _audit_tags
    if __key in rec:
        key=rec[__key]
        if key in _reg_schema:
            rec = _reg_schema[key]
            try:
                for tag,val in _audit_tags(rec).items():
                    rec[tag]=val
            except Exception as e:
                print(f"User audit is failed: [{rec}] ",e)
                return False
    return True
