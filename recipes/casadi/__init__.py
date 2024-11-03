from os.path import join
from pythonforandroid.util import current_directory, ensure_dir
from pythonforandroid.toolchain import shprint
import sh

from pythonforandroid.recipe import PythonRecipe


class CasadiRecipe(PythonRecipe):
    version = '3.6.6'
    url = 'https://github.com/casadi/casadi/archive/refs/tags/{version}.zip'
    depends = ['python3', 'setuptools', 'numpy', 'swig']
    patches = ['patches/p4a_build.patch', 'patches/build.patch']
    generated_libraries = [
        'libcasadi.so',
    ]
    call_hostpython_via_targetpython = False

    def get_recipe_env(self, arch, **kwargs):
        env = super().get_recipe_env(arch, **kwargs)

        # python_include_root = self.ctx.python_recipe.include_root('arm64-v8a')
        python_include_root = self.ctx.python_recipe.include_root(arch.arch)
        python_link_root = self.ctx.python_recipe.link_root(arch)
        python_link_version = self.ctx.python_recipe.link_version
        python_library = join(python_link_root,
                                  'libpython{}.so'.format(python_link_version))

        cmake_args = [
            '-DANDROID_ABI={}'.format(arch),
            '-DANDROID_NATIVE_API_LEVEL={}'.format(self.ctx.ndk_api),
            '-DCMAKE_TOOLCHAIN_FILE={}'.format(
                join(self.ctx.ndk_dir, 'build', 'cmake',
                'android.toolchain.cmake')),
            '-DPYTHON_INCLUDE_DIR={}'.format(python_include_root),
            '-DPYTHON_LIBRARY={}'.format(python_library),
        ]

        env['CASADI_SETUP_CMAKE_ARGS'] = ';'.join(cmake_args)
        
        return env

    def build_arch(self, arch, **kwargs):
        build_dir = join(self.get_build_dir(arch.arch), 'build')
        ensure_dir(build_dir)

        python_include_root = self.ctx.python_recipe.include_root(arch.arch)

        with current_directory(build_dir):
            env = self.get_recipe_env(arch)

            shprint(sh.cmake,
                    '-DANDROID_ABI={}'.format(arch.arch),
                    '-DANDROID_NATIVE_API_LEVEL={}'.format(self.ctx.ndk_api),
                    '-DCMAKE_TOOLCHAIN_FILE={}'.format(
                        join(self.ctx.ndk_dir, 'build', 'cmake',
                             'android.toolchain.cmake')),
                    '-DWITH_PYTHON3=ON',
                    '-DWITH_PYTHON=ON',
                    '-DSWIG_EXPORT=ON',

                    self.get_build_dir(arch.arch),
                    _env=env)
            shprint(sh.make, 'python_source')
        
        super().build_arch(arch, **kwargs)
        with current_directory(build_dir):
            sh.cp('-a', sh.glob('./lib.*/casadi/lib*.so'),
                    self.ctx.get_libs_dir(arch.arch))



recipe = CasadiRecipe()