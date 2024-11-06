from pythonforandroid.recipe import CompiledComponentsPythonRecipe

class CryptographyRecipe(CompiledComponentsPythonRecipe):
    version = '3.4.7'
    url = 'https://github.com/pyca/cryptography/archive/refs/tags/{version}.tar.gz'
    depends = ['openssl', 'cffi', 'setuptools']
    call_hostpython_via_targetpython = False
    install_in_hostpython = True

    def get_recipe_env(self, arch=None, with_flags_in_cc=True):
        env = super().get_recipe_env(arch, with_flags_in_cc)
        openssl_recipe = self.get_recipe('openssl', self.ctx)
        env['CFLAGS'] += ' -I' + openssl_recipe.get_build_dir(arch.arch)
        env['LDFLAGS'] += ' -L' + openssl_recipe.get_build_dir(arch.arch)
        return env

recipe = CryptographyRecipe() 