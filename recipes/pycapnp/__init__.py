from os.path import join
from pythonforandroid.util import current_directory, ensure_dir
from pythonforandroid.toolchain import shprint
import sh

from pythonforandroid.recipe import PythonRecipe, Recipe


class PycapnpRecipe(PythonRecipe):
    url = 'git+https://github.com/capnproto/pycapnp.git'
    version = 'v2.0.0'
    depends = ['python3', 'capnp']
    hostpython_prerequisites = ['setuptools', 'cython==0.29.37']
    call_hostpython_via_targetpython = False
    patches = ['build.patch']


    def get_recipe_env(self, arch, **kwargs):
        env = super().get_recipe_env(arch)
        capnp_dir = Recipe.get_recipe("capnp", self.ctx).get_build_dir(arch.arch)
        env['CXXFLAGS'] += ' -I{}/c++/src/'.format(capnp_dir)
        env['CXXFLAGS'] += ' -L{}/c++/.libs/'.format(capnp_dir)
        return env

recipe = PycapnpRecipe()