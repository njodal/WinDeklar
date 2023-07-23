from setuptools import setup, find_packages

setup(
    name='WinDeklar',
    version='0.3.0',
    description='Create winforms in an easy, declarative way. Specially suited for Robotics applications.',
    author='Nicolas Jodal',
    author_email='jnj@genexus.com',
    packages=find_packages(),
    install_requires=[
        # list your package dependencies here, for example:
        'numpy >= 1.15.0'
        'PyQt5~=5.14.1'
        'matplotlib~=3.5.2'
        'PyYAML~=5.3.1'
    ],
)
