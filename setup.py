import setuptools as setup


def get_version_and_cmdclass(pkg_path):
    """
    Load version.py module without importing the whole package.
    Template code from miniver
    """
    import os
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location('version', os.path.join(pkg_path, '_version.py'))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__version__, module.get_cmdclass(pkg_path)


def find_packages():
    return ['top'] + ['top.'+p for p in setup.find_packages('top')]


version, cmdclass = get_version_and_cmdclass(r'top')
setup.setup(
    name='top',
    version=version,
    cmdclass=cmdclass,
    author='0phoff',
    description='TOPCraft: Top Notch Python Debugging Tools',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/0phoff/topcraft',

    packages=find_packages(),
    install_requires=[
        'memory_profiler',
    ],
)
