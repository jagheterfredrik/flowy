from os.path import join
from pythonforandroid.util import current_directory, ensure_dir
from pythonforandroid.toolchain import shprint
import sh
from pythonforandroid.recipe import PythonRecipe, Recipe, IncludedFilesBehaviour

class MsgqRecipe(IncludedFilesBehaviour, PythonRecipe):
    # url = 'git+https://github.com/commaai/msgq.git'
    src_filename = "../../../openpilot/msgq_repo"
    depends = ['python3', 'libzmq', 'pycapnp']
    # patches = ['zmq.patch']

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

        with current_directory(self.get_build_dir(arch.arch)):
            # shprint(sh.scons, '--minimal', _env=self.get_recipe_env(arch))
            cpp = sh.Command(arch.clang_exe_cxx)

            shprint(cpp,
                '-o', 'libmsgq.so',
                '--target={}'.format(arch.target),
                '-std=c++1z', '-fPIC', '-O2', '-shared',
                'msgq/ipc.cc',
                'msgq/event.cc',
                'msgq/impl_zmq.cc',
                'msgq/impl_msgq.cc',
                'msgq/impl_fake.cc',
                'msgq/msgq.cc',
                '-I.',
                '-I{}'.format(zmq_include_root),
                # '-L{}'.format(self.ctx.get_libs_dir(arch.arch)),
                # '-lzmq',
                _env=self.get_recipe_env(arch))
            shprint(sh.cython, 'msgq/ipc_pyx.pyx', '--cplus', _env=self.get_recipe_env(arch))
            shprint(cpp,
                '-o', 'ipc_pyx.pyx.so',
                '--target={}'.format(arch.target),
                '-std=c++1z', '-fPIC', '-O2',
                '-shared',
                'msgq/ipc_pyx.cpp',
                'msgq/ipc.cc',
                '-I.',
                '-I{}'.format(python_include_root),
                '-L{}'.format(python_link_root),
                '-lpython{}'.format(python_link_version),
                '-I{}'.format(zmq_include_root),
                '-L.',
                '-lmsgq',
                '-L{}'.format(self.ctx.get_libs_dir(arch.arch)),
                '-lzmq',
                _env=self.get_recipe_env(arch))
            module_dir = join(self.ctx.get_python_install_dir(arch.arch), 'msgq')
            ensure_dir(module_dir)
            shprint(sh.cp, '-a', 'ipc_pyx.pyx.so', module_dir)
            shprint(sh.cp, '-a', 'msgq/__init__.py', module_dir)
            shprint(sh.cp, '-a', 'libmsgq.so', self.ctx.get_libs_dir(arch.arch))


recipe = MsgqRecipe()