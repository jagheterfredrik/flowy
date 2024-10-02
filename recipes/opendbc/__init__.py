from os.path import join
from pythonforandroid.util import current_directory, ensure_dir
from pythonforandroid.toolchain import shprint
import sh
from pythonforandroid.recipe import IncludedFilesBehaviour, PythonRecipe

class OpendbcRecipe(IncludedFilesBehaviour, PythonRecipe):
    src_filename = "../../../openpilot/opendbc_repo"
    need_stl_shared = True
    patches = ['build.patch']
    depends = ['python3', 'panda', 'libusb1', 'libusb', 'tqdm', 'crcmod', 'numpy==v1.26.4']

    def build_arch(self, arch):
        python_major = self.ctx.python_recipe.version[0]
        python_include_root = self.ctx.python_recipe.include_root(arch.arch)
        python_site_packages = self.ctx.get_site_packages_dir(arch)
        python_link_root = self.ctx.python_recipe.link_root(arch.arch)
        python_link_version = self.ctx.python_recipe.link_version
        python_library = join(python_link_root,
                                'libpython{}.so'.format(python_link_version))
        with current_directory(self.get_build_dir(arch.arch)):
            # shprint(sh.scons, '--minimal', _env=self.get_recipe_env(arch))
            print('wtf!?')
            print(arch.clang_exe_cxx)
            print(arch.target)

            cpp = sh.Command(arch.clang_exe_cxx)

            shprint(cpp,
                '-o', 'opendbc/can/libdbc.so',
                '--target={}'.format(arch.target),
                '-std=c++1z', '-fPIC', '-O2', '-shared',
                'opendbc/can/dbc.cc',
                'opendbc/can/parser.cc',
                'opendbc/can/packer.cc',
                'opendbc/can/common.cc',
                '-I.',
                '-DDBC_FILE_PATH="/sdcard"',
                _env=self.get_recipe_env(arch))
            shprint(sh.cythonize, 'opendbc/can/packer_pyx.pyx', _env=self.get_recipe_env(arch))
            shprint(sh.cythonize, 'opendbc/can/parser_pyx.pyx', _env=self.get_recipe_env(arch))
            shprint(cpp,
                '-o', 'opendbc/can/packer_pyx.so',
                '--target={}'.format(arch.target),
                '-std=c++1z', '-fPIC', '-O2', '-shared',
                'opendbc/can/packer_pyx.cpp',
                'opendbc/can/packer.cc',
                '-I.',
                '-I{}'.format(python_include_root),
                '-L{}'.format(python_link_root),
                '-lpython{}'.format(python_link_version),
                '-Lopendbc/can',
                '-ldbc',
                _env=self.get_recipe_env(arch))
            shprint(cpp,
                '-o', 'opendbc/can/parser_pyx.so',
                '--target={}'.format(arch.target),
                '-std=c++1z', '-fPIC', '-O2', '-shared',
                'opendbc/can/parser_pyx.cpp',
                'opendbc/can/parser.cc',
                '-I.',
                '-I{}'.format(python_include_root),
                '-L{}'.format(python_link_root),
                '-lpython{}'.format(python_link_version),
                '-Lopendbc/can',
                '-ldbc',
                _env=self.get_recipe_env(arch))
            shprint(sh.cp, '-a', 'opendbc', self.ctx.get_python_install_dir(arch.arch))
            shprint(sh.cp, '-a', 'opendbc/can/libdbc.so', self.ctx.get_libs_dir(arch.arch))


recipe = OpendbcRecipe()