
class _Null:
  def __repr__(self):
    return 'Null'
  def __getattr__(self, _):
    return self
  def __eq__(self, other):
    return other is None or isinstance(other, _Null)
  def __bool__(self): return False
  def __hash__(self): return hash(None)

Null = _Null()

def nullable(cls):
    def nullable_func(func):
        def wrapper(self, *a, **kw):
            ret = func(self, *a, **kw)
            if ret is None:
                return Null
            else:
                return ret
        return wrapper

    cls.__getattribute__ = nullable_func(cls.__getattribute__)
    if hasattr(cls, '_getattr_'):
        cls.__getattr__ = nullable_func(cls.__getattr__)
    else:
        cls.__getattr__ = lambda self, attr: Null

    return cls
