
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

    cls.__getattribute_ = nullable_func(cls._getattribute_)
    return cls

def normal_nullable(func):
  def nullable_func(self, *a, **kw):
      ret = func(self, *a, **kw)
      if ret is None:
         return Null
      else:
         return ret

  return nullable_func

def make_nullable(the_type: type):
   the_type.__getattribute__ = normal_nullable(the_type.__getattribute__)
