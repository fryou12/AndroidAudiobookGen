from pythonforandroid.recipe import CompiledComponentsPythonRecipe

class CffiRecipe(CompiledComponentsPythonRecipe):
    name = 'cffi'
    version = '1.14.6'
    url = 'https://files.pythonhosted.org/packages/2e/92/87bb61538d7e60da8a7ec247dc048f7671afe17016cd0008b3b710012804/cffi-1.14.6.tar.gz'
    depends = ['setuptools', 'pycparser', 'libffi']
    call_hostpython_via_targetpython = False
    install_in_hostpython = True

recipe = CffiRecipe() 