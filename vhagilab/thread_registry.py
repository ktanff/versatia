MAX_ONMEMORY_THREAD_KEYS = 1000
MAX_THREAD_PER_KEY = 50

_thread_registry={}

def safe_filename(key:str):
    from base64 import urlsafe_b64encode
    return urlsafe_b64encode(key.encode()).decode().rstrip("=")

def dump_thread_registry():
    global _thread_registry
    from os.path import exists
    from os import makedirs
    if not exists("threads"):
        makedirs("threads")
    for key,ts in _thread_registry.items():
        thrd_filename = f"threads/{safe_filename(key)}"
        with open(thrd_filename,'w') as thrd_file:
            thrd_file.write('\n'.join(ts))

def _unlink_threads(key:str):
    global _thread_registry
    _thread_registry.pop(key,None)
    thrd_filename = f"threads/{safe_filename(key)}"
    from os import remove
    try:
        remove(thrd_filename)
    except FileNotFoundError:
        print(f"Error: file '{thrd_filename}' not found!")

def get_threads(key:str):
    global _thread_registry
    if key not in _thread_registry:
        thrd_filename = f"threads/{safe_filename(key)}"
        try:
            with open(thrd_filename) as thrd_file:
                _thread_registry[key] = [thrd.strip() for thrd in thrd_file]
        except FileNotFoundError:
            _thread_registry[key] = []
        if len(_thread_registry) > MAX_ONMEMORY_THREAD_KEYS:
            from os.path import exists
            from os import makedirs
            if not exists("threads"):
                makedirs("threads")
            for stale in _thread_registry: break
            stale_thrd_filename = f"threads/{safe_filename(stale)}"
            with open(stale_thrd_filename,'w') as stale_thrd_file:
                stale_thrd_file.write('\n'.join(_thread_registry[stale]))
            del _thread_registry[stale]
    return _thread_registry[key]

def add_thread(key:str, thrd:str):
    global _thread_registry
    ts = _thread_registry.get(key,get_threads(key))
    if len(ts) < MAX_THREAD_PER_KEY:
        ts.append(thrd)
        return True
    return False

def del_thread(key:str, thrd:str):
    global _thread_registry
    ts = _thread_registry.get(key,get_threads(key))
    try:
        ts.remove(thrd)
        if ts==[]:
            _unlink_threads(key)
    except ValueError:
        print(f"Error: {key} does not have any thread {thrd} !")

def eager_add_thread(key:str, thrd:str):
    global _thread_registry
    ts = _thread_registry.get(key,get_threads(key))
    if not ts:
        from os.path import exists
        from os import makedirs
        if not exists("threads"):
            makedirs("threads")
    if len(ts) < MAX_THREAD_PER_KEY:
        ts.append(thrd)
        thrd_filename = f"threads/{safe_filename(key)}"
        with open(thrd_filename,'a') as thrd_file:
            thrd_file.write(thrd+'\n')
        return True
    return False

def eager_del_thread(key:str, thrd:str):
    global _thread_registry
    ts = _thread_registry.get(key,get_threads(key))
    try:
        ts.remove(thrd)
        if ts==[]:
            _unlink_threads(key)
        else:
            thrd_filename = f"threads/{safe_filename(key)}"
            with open(thrd_filename,'w') as thrd_file:
                thrd_file.write('\n'.join(ts))
    except ValueError:
        print(f"Error: {key} does not have any thread {thrd} !")
