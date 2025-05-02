def make_safe(t:str) -> str:
    if len(t)<11:
        t=safe_rand()
    else:
        t=t.replace('+','_').replace('/','_')
        if t[0] =='_': t='H'+t[1:]
        if t[-1]=='_': t=t[:-1]+'T'
        if t[0] in '0123456789': t='zidtqpxhon'[int(t[0])]+t[1:]
    return t

def safe_rand(l:int=11) -> str:
    from os import urandom
    from base64 import b64encode
    l=max(11,l)
    t=b64encode(urandom(3*l//4)).decode('utf-8')
    t=t[:l]
    return make_safe(t)
