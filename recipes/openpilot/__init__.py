from os.path import join
from pythonforandroid.util import current_directory, ensure_dir
from pythonforandroid.toolchain import shprint
import sh

from pythonforandroid.recipe import IncludedFilesBehaviour, Recipe


class OpenPilotRecipe(IncludedFilesBehaviour, Recipe):
    version = 'stable'
    src_filename = "../../src"

    call_hostpython_via_targetpython = False
    depends = ['capnp', 'zmq']

    def build_arch(self, arch):
        python_major = self.ctx.python_recipe.version[0]
        python_include_root = self.ctx.python_recipe.include_root(arch.arch)
        python_site_packages = self.ctx.get_site_packages_dir(arch)
        python_link_root = self.ctx.python_recipe.link_root(arch.arch)
        python_link_version = self.ctx.python_recipe.link_version
        python_library = join(python_link_root,
                                'libpython{}.so'.format(python_link_version))

        zmq_dir = Recipe.get_recipe("libzmq", self.ctx).get_build_dir(arch.arch)
        zmq_include_root = join(zmq_dir, "include")

        capnp_dir = Recipe.get_recipe("capnp", self.ctx).get_build_dir(arch.arch)
        capnp_include_root = join(capnp_dir, "c++", "src")


        with current_directory(self.get_build_dir(arch.arch)):

            cpp = sh.Command(arch.clang_exe_cxx)

            shprint(sh.cythonize, 'openpilot/common/params_pyx.pyx', _env=self.get_recipe_env(arch))
            shprint(cpp,
                '-o', 'openpilot/common/params_pyx.so',
                '--target={}'.format(arch.target),
                '-std=c++1z', '-fPIC', '-O2', '-shared',
                'openpilot/common/params_pyx.cpp',
                'openpilot/common/params.cc',
                'openpilot/common/util.cc',
                'openpilot/common/swaglog.cc',
                'third_party/json11/json11.cpp',
                '-Iopenpilot',
                '-I.',
                '-I{}'.format(python_include_root),
                '-L{}'.format(python_link_root),
                '-I{}'.format(zmq_include_root),
                '-I{}'.format(capnp_include_root),
                '-L{}'.format(self.ctx.get_libs_dir(arch.arch)),
                '-lpython{}'.format(python_link_version),
                '-lcapnp',
                '-lzmq',
                _env=self.get_recipe_env(arch))
            # shprint(sh.cp, '-a', 'opendbc', self.ctx.get_python_install_dir(arch.arch))
            # shprint(sh.cp, '-a', 'opendbc/can/libdbc.so', self.ctx.get_libs_dir(arch.arch))
            import os
            os.exit(1)


recipe = OpenPilotRecipe()