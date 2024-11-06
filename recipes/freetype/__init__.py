from pythonforandroid.recipe import Recipe
from pythonforandroid.toolchain import current_directory, shprint
import sh
from os.path import exists, join

class FreetypeRecipe(Recipe):
    version = '2.10.4'
    url = 'https://download.savannah.gnu.org/releases/freetype/freetype-{version}.tar.gz'
    name = 'freetype'
    depends = []

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['CFLAGS'] = ' -O3'
        return env

    def build_arch(self, arch):
        env = self.get_recipe_env(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            if exists('Makefile'):
                shprint(sh.make, 'clean', _env=env)
            shprint(sh.Command('./configure'),
                   '--host=' + arch.command_prefix,
                   '--prefix=' + self.get_build_dir(arch.arch),
                   '--without-harfbuzz',
                   '--with-png=no',
                   '--with-zlib=no',
                   '--enable-static=no',
                   '--enable-shared=yes',
                   _env=env)
            shprint(sh.make, _env=env)
            shprint(sh.make, 'install', _env=env)
            shprint(sh.cp,
                   join(self.get_build_dir(arch.arch), 'lib', 'libfreetype.so'),
                   self.ctx.get_libs_dir(arch.arch))

recipe = FreetypeRecipe() 