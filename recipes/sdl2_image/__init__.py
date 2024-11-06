from pythonforandroid.recipe import BootstrapNDKRecipe
from pythonforandroid.toolchain import current_directory, shprint
import sh
from os.path import exists, join

class SDL2ImageRecipe(BootstrapNDKRecipe):
    version = '2.0.5'
    url = 'https://www.libsdl.org/projects/SDL_image/release/SDL2_image-{version}.tar.gz'
    name = 'sdl2_image'
    depends = ['sdl2']

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['CFLAGS'] = env.get('CFLAGS', '') + ' -I{}'.format(
            self.get_build_dir(arch.arch))
        return env

    def build_arch(self, arch):
        env = self.get_recipe_env(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            if exists('Makefile'):
                shprint(sh.make, 'clean', _env=env)
            shprint(sh.Command('./configure'),
                   '--host=' + arch.command_prefix,
                   '--prefix=' + self.get_build_dir(arch.arch),
                   '--enable-shared',
                   '--disable-static',
                   '--disable-png-shared',
                   '--disable-jpg-shared',
                   '--disable-tif-shared',
                   '--disable-webp-shared',
                   _env=env)
            shprint(sh.make, _env=env)
            shprint(sh.make, 'install', _env=env)
            shprint(sh.cp,
                   join(self.get_build_dir(arch.arch), 'lib', 'libSDL2_image.so'),
                   self.ctx.get_libs_dir(arch.arch))

recipe = SDL2ImageRecipe() 