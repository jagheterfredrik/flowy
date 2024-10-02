from pythonforandroid.recipe import Recipe
from pythonforandroid.logger import shprint
from pythonforandroid.util import current_directory
from os.path import join
import sh


class LibZMQRecipe(Recipe):
    version = '4.3.5'
    url = 'https://github.com/zeromq/libzmq/releases/download/v{version}/zeromq-{version}.zip'
    depends = []
    built_libraries = {'libzmq.so': 'src/.libs'}
    need_stl_shared = True

    def get_recipe_env(self, arch, **kwargs):
        env = super().get_recipe_env(arch)
        env['ANDROID_NDK_ROOT'] = self.ctx.ndk_dir
        env['NDK_VERSION'] = 'android-ndk-r25b'
        return env

    def build_arch(self, arch):
        env = self.get_recipe_env(arch)

        curdir = join(self.get_build_dir(arch.arch), "builds", "android")

        with current_directory(curdir):
            bash = sh.Command('bash')
            shprint(
                bash, "build.sh", "arm64",
                _env=env)
            sh.cp('-a', "prefix/arm64/lib/libzmq.so", self.ctx.get_libs_dir(arch.arch))


recipe = LibZMQRecipe()