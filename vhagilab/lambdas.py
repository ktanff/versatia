nullfn = lambda *_:None
truefn = lambda *_:True
idntfn = lambda *_:_ if len(_)!=1 else _[0]
popufn = lambda fill,arity: None if not arity else fill if arity==1 else (fill,)*arity
lift = lambda a,b:b if a is None else (*a,b) if isinstance(a,tuple) else (a,b)
fa2en_digits = lambda s:f"{int(s):0{len(s)}}"
