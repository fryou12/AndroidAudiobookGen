from pythonforandroid.recipe import BootstrapNDKRecipe
from pythonforandroid.toolchain import current_directory, shprint, info
import sh
import os
from os.path import exists, join

class SDL2Recipe(BootstrapNDKRecipe):
    version = '2.28.5'
    url = 'https://github.com/libsdl-org/SDL/releases/download/release-{version}/SDL2-{version}.tar.gz'
    name = 'sdl2'
    dir_name = 'SDL2-{version}'

    def get_build_dir(self, arch):
        return join(self.ctx.build_dir, self.dir_name.format(version=self.version))

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['CFLAGS'] = env.get('CFLAGS', '') + f' -I{self.get_build_dir(arch)}/include'
        return env

    def build_arch(self, arch):
        env = self.get_recipe_env(arch)
        build_dir = self.get_build_dir(arch)
        
        if not exists(build_dir):
            os.makedirs(build_dir)
        
        info('Downloading SDL2')
        self.download_if_necessary()
        
        with current_directory(build_dir):
            filename = self.url.format(version=self.version).split('/')[-1]
            archive_path = join(self.ctx.packages_path, self.name, filename)
            if exists(archive_path):
                info(f'Extracting {filename}')
                shprint(sh.tar, 'xf', archive_path, '--strip-components=1')

            # Créer le fichier d'en-tête des stubs Android
            os.makedirs('src/core/android', exist_ok=True)
            android_stubs_h = join('src/core/android', 'SDL_android_stubs.h')
            with open(android_stubs_h, 'w') as f:
                f.write('''
#ifndef SDL_ANDROID_STUBS_H
#define SDL_ANDROID_STUBS_H
#include <SDL_config.h>
#include <SDL_stdinc.h>

int Android_OnPadDown(int device_id, int keycode);
int Android_OnPadUp(int device_id, int keycode);
void Android_OnJoy(int device_id, int axis, float value);
void Android_OnHat(int device_id, int hat_id, int x, int y);
int Android_AddJoystick(int device_id, const char* name, const char* desc, int vendor_id, int product_id, SDL_bool is_accelerometer, int button_mask, int naxes, int axis_mask, int nhats, int nballs);
int Android_RemoveJoystick(int device_id);
int Android_AddHaptic(int device_id, const char* name);
int Android_RemoveHaptic(int device_id);

#endif /* SDL_ANDROID_STUBS_H */
''')

            # Créer le fichier d'implémentation des stubs Android
            android_stubs_c = join('src/core/android', 'SDL_android_stubs.c')
            with open(android_stubs_c, 'w') as f:
                f.write('''
#include "SDL_android_stubs.h"

int Android_OnPadDown(int device_id, int keycode) { return 0; }
int Android_OnPadUp(int device_id, int keycode) { return 0; }
void Android_OnJoy(int device_id, int axis, float value) {}
void Android_OnHat(int device_id, int hat_id, int x, int y) {}
int Android_AddJoystick(int device_id, const char* name, const char* desc, int vendor_id, int product_id, SDL_bool is_accelerometer, int button_mask, int naxes, int axis_mask, int nhats, int nballs) { return 0; }
int Android_RemoveJoystick(int device_id) { return 0; }
int Android_AddHaptic(int device_id, const char* name) { return 0; }
int Android_RemoveHaptic(int device_id) { return 0; }
''')

            if exists('configure'):
                info('Configuring SDL2')
                shprint(sh.Command('./configure'),
                       '--host=' + arch.command_prefix,
                       '--prefix=' + build_dir,
                       '--enable-shared',
                       '--disable-static',
                       '--disable-hidapi',
                       '--disable-joystick',
                       '--disable-haptic',
                       '--disable-opensles',
                       '--disable-audio',
                       _env=env)
                
                info('Building SDL2')
                shprint(sh.make, _env=env)
                shprint(sh.make, 'install', _env=env)
            else:
                info('Configure script not found')
                raise Exception('Configure script not found')

recipe = SDL2Recipe()