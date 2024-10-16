from os.path import join, dirname, exists
from pythonforandroid.util import current_directory, ensure_dir
from pythonforandroid.recipe import Recipe
from pythonforandroid.toolchain import shprint
import sh


class AcadosRecipe(Recipe):
    version = 'v0.2.2'
    url = 'git+https://github.com/acados/acados.git'
    generated_libraries = [
        'acados/libacados.so',
        'external/blasfeo/libblasfeo.so',
        'external/qpoases/lib/libqpOASES_e.so',
        'external/hpipm/libhpipm.so',
    ]

    def build_arch(self, arch, **kwargs):        
        build_dir = join(self.get_build_dir(arch.arch), 'build')
        ensure_dir(build_dir)
        with current_directory(build_dir):
            env = self.get_recipe_env(arch)

            shprint(sh.cmake,
                    '-DANDROID_ABI={}'.format(arch.arch),
                    '-DANDROID_NATIVE_API_LEVEL={}'.format(self.ctx.ndk_api),
                    '-DCMAKE_TOOLCHAIN_FILE={}'.format(
                        join(self.ctx.ndk_dir, 'build', 'cmake',
                             'android.toolchain.cmake')),
                    '-DCMAKE_ASM_FLAGS=-DOS_LINUX',
                    '-DACADOS_WITH_QPOASES=ON',
                    '-UBLASFEO_TARGET',
                    '-DBLASFEO_TARGET=ARMV8A_ARM_CORTEX_A57',

                    '..',
                    _env=env)
            shprint(sh.make)
            
            sh.cp('-a', *self.generated_libraries, self.ctx.get_libs_dir(arch.arch))

recipe = AcadosRecipe()