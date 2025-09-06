def gentrait(func):
    def wrapper(*args, **kwargs):
        return ( yield from func(*args, **kwargs) )
    return wrapper

def ngentrait(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        for _ in result:
            yield from _
        return result
    return wrapper
