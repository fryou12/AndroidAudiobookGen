from pythonforandroid.recipe import CythonRecipe
from pythonforandroid.toolchain import current_directory, shprint
from os.path import exists, join
import sh
import glob

class KivyRecipe(CythonRecipe):
    version = '2.2.1'
    url = 'https://github.com/kivy/kivy/archive/{version}.zip'
    name = 'kivy'

    depends = ['sdl2', 'sdl2_image', 'sdl2_mixer', 'sdl2_ttf', 'pyjnius']
    python_depends = ['certifi']

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        
        # Add SDL2 paths
        env['USE_SDL2'] = '1'
        env['KIVY_DEPS_ROOT'] = self.ctx.get_site_packages_dir(arch)
        env['KIVY_SDL2_PATH'] = ':'.join([
            join(self.ctx.bootstrap.build_dir, 'jni', 'SDL', 'include'),
            join(self.ctx.bootstrap.build_dir, 'jni', 'SDL2_image'),
            join(self.ctx.bootstrap.build_dir, 'jni', 'SDL2_mixer'),
            join(self.ctx.bootstrap.build_dir, 'jni', 'SDL2_ttf'),
        ])

        # Add compilation flags
        env['CFLAGS'] = f"{env.get('CFLAGS', '')} -I{self.ctx.bootstrap.build_dir}/jni/SDL/include"
        env['LDFLAGS'] = f"{env.get('LDFLAGS', '')} -L{self.ctx.bootstrap.build_dir}/libs/{arch.arch}"

        return env

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        if exists(join(self.get_build_dir(arch.arch), '.patched')):
            print('Kivy already patched, skipping')
            return

        # Apply any patches if needed
        self.apply_patches(arch)
        
        # Create config.h
        with current_directory(self.get_build_dir(arch.arch)):
            with open('kivy/include/config.h', 'w') as f:
                f.write('#define KIVY_SDL2 1\n')
                f.write('#define KIVY_DLL 1\n')
                f.write('#define KIVY_GL_BACKEND_SDL2 1\n')

        shprint(sh.touch, join(self.get_build_dir(arch.arch), '.patched'))

    def build_arch(self, arch):
        # Ensure SDL2 is built first
        sdl2_recipe = self.get_recipe('sdl2', self.ctx)
        sdl2_recipe.build_arch(arch)
        
        super().build_arch(arch)

recipe = KivyRecipe() 