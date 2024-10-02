from os.path import join
from pythonforandroid.util import current_directory, ensure_dir
from pythonforandroid.toolchain import shprint
import sh
from pythonforandroid.recipe import IncludedFilesBehaviour, PythonRecipe, CompiledComponentsPythonRecipe

class LateralMpcLibRecipe2():#IncludedFilesBehaviour, PythonRecipe):
    version = 'stable'
    src_filename = "../../lateral_mpc_lib2"
    name = 'lateral_mpc_lib'

    depends = ['casadi', 'acados', 'numpy']

    call_hostpython_via_targetpython = False
    install_in_hostpython = True

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)


        env['LD_LIBRARY_PATH'] = self.ctx.get_libs_dir(arch.arch)

        return env

    def build_arch(self, arch):
        # super().build_arch(arch)
        with current_directory(self.get_build_dir(arch)):
            shprint(sh.make, 'shared_lib', _env=self.get_recipe_env(arch))

class LateralMpcLibRecipe(IncludedFilesBehaviour, CompiledComponentsPythonRecipe):
    version = 'stable'
    src_filename = "../../lateral_mpc_lib_gen2"
    name = 'lateral_mpc_lib'

    depends = ['casadi', 'acados', 'numpy']
    call_hostpython_via_targetpython = False

    def build_arch(self, arch):
    #     super().build_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            sh.cp('-a', 'acados_ocp_solver_pyx.so', '/home/ubuntu/Developer/p4a2/.buildozer/android/platform/build-arm64-v8a/build/python-installs/oscservice/arm64-v8a/')
            # sh.cp('-a', sh.glob('lib*.so'.format(arch.arch)),
            #         self.ctx.get_libs_dir(arch.arch))


recipe = LateralMpcLibRecipe()