from os.path import join
from pythonforandroid.util import current_directory, ensure_dir
from pythonforandroid.toolchain import shprint
import sh
from pythonforandroid.recipe import IncludedFilesBehaviour, PythonRecipe

class PandaRecipe(IncludedFilesBehaviour, PythonRecipe):
    src_filename = "../../../openpilot/panda"
    depends = ['python3', 'libusb1', 'libusb', 'tqdm']
    hostpython_prerequisites = ['setuptools']
    call_hostpython_via_targetpython = False

recipe = PandaRecipe()