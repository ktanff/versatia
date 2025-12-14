nullfn = lambda *_:None
truefn = lambda *_:True
idntfn = lambda *_:_ if len(_)!=1 else _[0]
popufn = lambda fill,arity: None if not arity else fill if arity==1 else (fill,)*arity
fa2en_digits = lambda s:f"{int(s):0{len(s)}}"

from random import choice as _choice
ezspl_randpasswd = lambda n:''.join(_choice('1234569abcdfghkprstwxyz') for _ in range(n))

def ftruncstr(s,upto):
    if len(s)<=upto:
        return s
    else:
        for c in s[upto::-1]:
            if c in "\t- .:;,_()[]": break
            upto-=1
        return s[:upto]+"..."
