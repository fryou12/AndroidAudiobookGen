from pythonforandroid.recipe import BootstrapNDKRecipe
from pythonforandroid.toolchain import current_directory, shprint
import sh
from os.path import exists, join

class SDL2MixerRecipe(BootstrapNDKRecipe):
    version = '2.0.4'
    url = 'https://www.libsdl.org/projects/SDL_mixer/release/SDL2_mixer-{version}.tar.gz'
    name = 'sdl2_mixer'
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
                   '--disable-music-mp3-mad-gpl',
                   '--disable-music-mod',
                   '--disable-music-ogg',
                   '--disable-music-flac',
                   '--disable-music-mp3-mpg123',
                   _env=env)
            shprint(sh.make, _env=env)
            shprint(sh.make, 'install', _env=env)
            shprint(sh.cp,
                   join(self.get_build_dir(arch.arch), 'lib', 'libSDL2_mixer.so'),
                   self.ctx.get_libs_dir(arch.arch))

recipe = SDL2MixerRecipe() 