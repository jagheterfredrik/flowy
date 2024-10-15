from pythonforandroid.recipe import Recipe
from pythonforandroid.logger import shprint
from pythonforandroid.util import current_directory
from os.path import join, basename
import sh


class CapnpRecipe(Recipe):
    version = 'v1.0.1'
    url = 'git+https://github.com/capnproto/capnproto.git'
    patches = ['path.patch']

    def get_recipe_env(self, arch, **kwargs):
        env = super().get_recipe_env(arch)
        env['ANDROID_NDK_ROOT'] = self.ctx.ndk_dir
        env['NDK_VERSION'] = 'android-ndk-r25b'
        env['PATH'] = '{}:{}'.format(self.ctx.ndk.llvm_prebuilt_dir, env['PATH'])
        return env

    def build_arch(self, arch):
        env = self.get_recipe_env(arch)

        curdir = join(self.get_build_dir(arch.arch), "c++")

        with current_directory(curdir):
            bash = sh.Command('bash')
            shprint(sh.autoreconf, '-i', _env=env)
            shprint(bash,
                './configure',
                '--host=arm-linux-androideabi',
                'CC={}-clang'.format(arch.target),
                'CXX={}-clang++'.format(arch.target),
                '--with-external-capnp',
                '--without-fibers',
                'CXXFLAGS=-fPIC -fPIE -shared -mno-outline-atomics',
                'LIBS=-ldl',
                _env=env)
            shprint(sh.make, _env=env)
            with current_directory(join(curdir, '.libs')):
                for lib in sh.glob("lib*-1.0.1.so"):
                    shprint(sh.ln, '-sf', lib, lib.replace('-1.0.1', ''))
                    shprint(sh.cp, '-a', lib, lib.replace('-1.0.1', ''), self.ctx.get_libs_dir(arch.arch))


recipe = CapnpRecipe()