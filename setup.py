import setuptools as setup


def find_packages():
    return ['top'] + ['top.'+p for p in setup.find_packages('top')]


setup.setup(
    name='top',
    version='0.0.1',
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
