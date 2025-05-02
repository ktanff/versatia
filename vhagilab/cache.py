_cache_era='000'
_cache={}

def set_cache_era(era):
    global _cache_era
    _cache_era=era

def cache_dump():
    from os.path import exists
    from os import makedirs
    if not exists("cache"):
        makedirs("cache")
    from json import dump
    for fn in _cache:
        cache_file_name = f"cache/{fn.__name__}-{_cache_era}.json"
        with open(cache_file_name,'w',encoding='utf-8') as cache_file:
            dump_fallback = _cache[fn][None][1]
            dump(_cache[fn],cache_file,ensure_ascii=False,default=dump_fallback)

def cache(n=1000,*,ttl=7200,alpha=0.05,ena0=100,dump_fallback=None,load_fallback=None):
    def decor(fn):
        global _cache
        from time import time
        if fn not in _cache:
            _cache[fn]={None:(time(),dump_fallback)}
            from os.path import exists
            cache_file_name = f"cache/{fn.__name__}-{_cache_era}.json"
            if exists(cache_file_name):
                from json import load
                with open(cache_file_name,encoding='utf-8') as cache_file:
                    _cache[fn] = load(cache_file,object_hook=load_fallback)
        c=_cache[fn]
        def wrapper(*args,__FRESH=False,**kwargs):
            now = round(time()-c[None][0],2)
            is_hacked=('__HACK' in kwargs)
            if is_hacked:
                y = kwargs.pop('__HACK')
            ky = str(args)[1:-1] + str(kwargs)[1:-1]
            if __FRESH or (ky not in c):
                while len(c)>=n:
                    max_ena = max(c.values())
                    thrshld = 0.99*max_ena[0]
                    for k,v in list(c.items()):
                        if v[0]>=thrshld:
                            del c[k]
                            if len(c)<n: break
                v=c[ky]=[ena0,now,now,y if is_hacked else fn(*args,**kwargs)]
            else:
                v=c[ky]
                if v[1] + ttl < now:
                    v[-1]=fn(*args)
                    v[1]=now
                delta= now - v[2]
                v[0]+= alpha*(delta-v[0])
                v[2]= now
            return v[-1]
        return wrapper
    return decor
