from pythonforandroid.recipe import BootstrapNDKRecipe
from pythonforandroid.toolchain import current_directory, shprint
import sh
from os.path import exists, join

class SDL2TTFRecipe(BootstrapNDKRecipe):
    version = '2.0.15'
    url = 'https://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-{version}.tar.gz'
    name = 'sdl2_ttf'
    depends = ['sdl2', 'freetype']

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        freetype_recipe = self.get_recipe('freetype', self.ctx)
        env['CFLAGS'] = env.get('CFLAGS', '') + ' -I{}'.format(
            join(freetype_recipe.get_build_dir(arch.arch), 'include', 'freetype2'))
        env['LDFLAGS'] = env.get('LDFLAGS', '') + ' -L{}'.format(
            join(freetype_recipe.get_build_dir(arch.arch), 'lib'))
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
                   '--with-freetype-prefix=' + self.get_recipe('freetype', self.ctx).get_build_dir(arch.arch),
                   _env=env)
            shprint(sh.make, _env=env)
            shprint(sh.make, 'install', _env=env)
            shprint(sh.cp,
                   join(self.get_build_dir(arch.arch), 'lib', 'libSDL2_ttf.so'),
                   self.ctx.get_libs_dir(arch.arch))

recipe = SDL2TTFRecipe()