""" Install atomapi """
from setuptools import setup, find_packages

setup(
    name='atomapi',
    version='0.0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    scripts=[],

    install_requires=[
        "requests>=2.0.0",
        "bs4==0.0.1",
    ],

    zip_safe=False,
    description='Python library for interacting with AtoM archives',
    author='Daniel Lovegrove',
    author_email='Daniel.Lovegrove@umanitoba.ca',
    license='MIT',
)
