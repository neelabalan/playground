from setuptools import find_packages
from setuptools import setup

setup(
    name='postinstall',
    version='0.1.0',
    url='https://github.com/neelabalan/postinstall',
    long_description=open('README.md').read(),
    author='neelabalan',
    author_email='neelabalan.n@gmail.com',
    python_requires='>=3.7',
    license='MIT',
    package_data={'': ['config.toml']},
    install_requires=['yaspin>=1.1.0', 'toml>=0.10.1'],
    py_modules=['postinstall'],
    keywords='postinstall linux',
    packages=find_packages(),
    entry_points={'console_scripts': ['postinstall = postinstall:main']},
    setup_requires=['wheel'],
)
