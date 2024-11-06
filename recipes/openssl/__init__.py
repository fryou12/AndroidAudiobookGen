from pythonforandroid.recipe import Recipe
from pythonforandroid.logger import shprint
from os.path import join, exists
import sh
from contextlib import contextmanager
import os

class OpenSSLRecipe(Recipe):
    version = '1.1.1w'
    url = 'https://www.openssl.org/source/openssl-{version}.tar.gz'
    depends = []

    def should_build(self, arch):
        return not self.has_libs(arch, 'libssl.so.1.1', 'libcrypto.so.1.1')

    @contextmanager
    def cd(self, directory):
        current = os.getcwd()
        try:
            os.chdir(directory)
            yield
        finally:
            os.chdir(current)

    def get_include_dirs(self, arch):
        build_dir = self.get_build_dir(arch.arch)
        return [build_dir, join(build_dir, 'include')]

    def get_library_dirs(self, arch):
        build_dir = self.get_build_dir(arch.arch)
        return [join(build_dir, 'lib')]

    def include_flags(self, arch):
        return ' -I'.join([''] + self.get_include_dirs(arch))

    def link_dirs_flags(self, arch):
        return ' -L'.join([''] + self.get_library_dirs(arch))

    def link_libs_flags(self):
        return ' -lssl -lcrypto'

    def build_arch(self, arch):
        env = self.get_recipe_env(arch)
        env['ANDROID_NDK_HOME'] = self.ctx.ndk_dir
        env['PATH'] = f"{env['PATH']}:{self.ctx.ndk_dir}/toolchains/llvm/prebuilt/darwin-x86_64/bin"
        
        build_dir = self.get_build_dir(arch.arch)
        with self.cd(build_dir):
            # Configure
            configure_args = [
                'android-arm64',
                f'-D__ANDROID_API__={self.ctx.ndk_api}',
                f'--prefix={build_dir}',
                'shared',  # Build shared libraries
                'no-ssl2',
                'no-ssl3',
                'no-comp',
                'no-hw',
                'no-engine'
            ]
            shprint(sh.Command('./Configure'), *configure_args, _env=env)
            
            # Build
            shprint(sh.make, _env=env)
            
            # Create lib directory if it doesn't exist
            lib_dir = join(build_dir, 'lib')
            if not exists(lib_dir):
                os.makedirs(lib_dir)
            
            # Copy the shared libraries with their original names
            libs_dir = self.ctx.get_libs_dir(arch.arch)
            shprint(sh.cp, 'libssl.so.1.1', join(libs_dir, 'libssl.so.1.1'))
            shprint(sh.cp, 'libcrypto.so.1.1', join(libs_dir, 'libcrypto.so.1.1'))
            
            # Create symlinks
            with self.cd(libs_dir):
                shprint(sh.ln, '-sf', 'libssl.so.1.1', 'libssl.so')
                shprint(sh.ln, '-sf', 'libcrypto.so.1.1', 'libcrypto.so')

recipe = OpenSSLRecipe()