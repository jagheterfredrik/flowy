from openpilot.common.params_pyx import Params as InternalParams, ParamKeyType, UnknownKeyName
assert Params
assert ParamKeyType
assert UnknownKeyName

class Params(InternalParams):
  def __new__(cls, d='./', **kwargs):
    return super().__new__(cls, d, **kwargs)

if __name__ == "__main__":
  import sys

  params = Params()
  key = sys.argv[1]
  assert params.check_key(key), f"unknown param: {key}"

  if len(sys.argv) == 3:
    val = sys.argv[2]
    print(f"SET: {key} = {val}")
    params.put(key, val)
  elif len(sys.argv) == 2:
    print(f"GET: {key} = {params.get(key)}")
