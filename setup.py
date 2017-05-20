""" happy-worker, the worker model lib.
See examples folder for usage and dbcreate tool.
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='happy-worker',
    url='https://github.com/owlin/happy-worker',
    version='0.9.5',
    license='3-clause BSD',
    author='Bart van Halder',
    author_email='bart@owlin.com',

    description='Worker model implementation on RethinkDB',
    long_description=long_description,

    # defaults from sample, not sure if needed
    # if anyone would like to help out, python packages aren't my strongpoint
    classifiers=[],
    keywords='',

    packages=find_packages(),  # magic

    install_requires=['rethinkdb', 'psutil'],

    extras_require={},

    package_data={},

    data_files=[],

    entry_points={},
)
