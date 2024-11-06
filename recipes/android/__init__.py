from pythonforandroid.recipe import CythonRecipe
from pythonforandroid.toolchain import current_directory, shprint
import sh
import os
from os.path import exists, join

class AndroidRecipe(CythonRecipe):
    version = 'master'
    url = 'https://github.com/kivy/python-for-android/archive/refs/heads/master.zip'
    name = 'android'
    depends = ['sdl2', 'pyjnius']
    python_depends = []

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['LDFLAGS'] = env.get('LDFLAGS', '') + ' -L{}'.format(
            self.ctx.get_libs_dir(arch.arch))
        return env

    def build_arch(self, arch):
        super().build_arch(arch)
        # Copier les fichiers nécessaires
        with current_directory(self.get_build_dir(arch.arch)):
            # Créer le répertoire de destination s'il n'existe pas
            build_dir = join('build', 'lib.linux-x86_64-2.7', 'android')
            if not exists(build_dir):
                os.makedirs(build_dir)
            
            # Copier les fichiers Python nécessaires
            src_dir = join(self.get_build_dir(arch.arch), 'pythonforandroid', 'recipes', 'android', 'src')
            if exists(src_dir):
                for py_file in ['android.py', '_android.pyx', '_android_jni.h']:
                    src_file = join(src_dir, py_file)
                    if exists(src_file):
                        shprint(sh.cp, src_file, build_dir)

recipe = AndroidRecipe()