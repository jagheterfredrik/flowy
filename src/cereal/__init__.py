# pylint: skip-file
import os
import capnp

CEREAL_PATH = "cereal"
capnp.remove_import_hook()

OP_CAPNP = os.environ.get("OP_CAPNP", False)

if not OP_CAPNP:
    log = capnp.load(os.path.join(CEREAL_PATH, "log.capnp"))
    car = capnp.load(os.path.join(CEREAL_PATH, "car.capnp"))
else:
    log = capnp.load(os.path.join(CEREAL_PATH, "op", "log.capnp"))
    car = capnp.load(os.path.join(CEREAL_PATH, "op", "car.capnp"))

