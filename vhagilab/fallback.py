_promised_trial = {}

def fallback_rotate(
    fallback_fn,                    # required
    retry_exceptions=(Exception,),  # optional
    *,
    scope=None,
    max_retry=3,
    delay=0.5
):
    """
    Generic fallback retry decorator.

    Parameters
    ----------
    fallback_fn : callable
        Function mapping current trial -> next fallback trial (or None).
        It is assumed that fallback_fn is an unary function that returns a scalar.
        Name and default value for the only one argument of fallback_fn must exactly 
        match to the argument in wrapped function by which the fallback mechanism is articulated.
    retry_exceptions : Exception | tuple[Exception], optional
        Exception types that trigger fallback attempts. Default=(Exception,)
    scope : str | None
        If given, multiple wrapped functions share fallback state under this scope.
    max_retry : int
        Maximum number of recalls (excluding the first call) before giving up. Default=3,
    delay : float
        Sleep between retries (in seconds). Default=0.5
    """
    arity = fallback_fn.__code__.co_argcount + fallback_fn.__code__.co_kwonlyargcount
    if arity != 1:
        raise TypeError(f"{fallback_fn.__name__}() not an unary, it takes {arity} argument(s), while exactly one is expected.")
    fallback_arg = fallback_fn.__code__.co_varnames[0]
    if fallback_fn.__defaults__:
        fallback_default_val = fallback_fn.__defaults__[0]
    elif fallback_fn.__kwdefaults__:
        fallback_default_val = fallback_fn.__kwdefaults__[fallback_arg]
    else:
        fallback_default_val = None
    def decorator(func):
        _scope_promised_trial = _promised_trial.setdefault(scope if scope else func,{})
        def wrapper(*args, _retry_sofar = 0, **kwargs):
            cur_fallback_val = kwargs.setdefault(fallback_arg,fallback_default_val)
            if cur_fallback_val in _scope_promised_trial:
                promised_fallback_val = _scope_promised_trial[cur_fallback_val]
                promised_fallback_val = _scope_promised_trial.get(promised_fallback_val)
                if not promised_fallback_val:
                    del _scope_promised_trial[cur_fallback_val]
                elif promised_fallback_val != cur_fallback_val:
                    kwargs[fallback_arg] = promised_fallback_val
                    try:
                        return func(*args, **kwargs)
                    except retry_exceptions as e:
                        _retry_sofar+=1
                        kwargs[fallback_arg] = cur_fallback_val
                        del _scope_promised_trial[cur_fallback_val]
                        _scope_promised_trial.pop(promised_fallback_val,None)
                        print(f"{e}")
                        print(f"[{func.__name__}] fail with {fallback_arg} = {promised_fallback_val}")
            try:
                result = func(*args, **kwargs)
                if _retry_sofar > 0:
                    _scope_promised_trial[cur_fallback_val] = cur_fallback_val
                    print(f"[{func.__name__}] success with {fallback_arg} = {cur_fallback_val}")
                return result
            except retry_exceptions as e:
                _scope_promised_trial.pop(cur_fallback_val,None)
                print(f"{e}")
                print(f"[{func.__name__}] fail with {fallback_arg} = {cur_fallback_val}")
                if _retry_sofar < max_retry:
                    fallback_val = fallback_fn(cur_fallback_val)
                    if fallback_val:
                        from time import sleep
                        sleep(delay)
                        kwargs[fallback_arg] = fallback_val
                        result = wrapper(*args, _retry_sofar = _retry_sofar+1, **kwargs)
                        _scope_promised_trial[cur_fallback_val] = _scope_promised_trial[fallback_val]
                        return result
                raise RuntimeError(f"Fallback rotation exhausted, after {_retry_sofar} retries on {func.__name__}!") from e
        return wrapper
    return decorator
