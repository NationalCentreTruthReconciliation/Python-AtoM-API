from setuptools import setup, find_packages

with open('README.md', 'r') as file_handle:
    long_description = file_handle.read()

setup(
    name='atomapi',
    version='0.0.1',
    author='Daniel Lovegrove',
    author_email='d.lovegrove11@gmail.com',
    description='Grab data from Atom API with Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/danloveg/atom-api-python',
    license='MIT',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    scripts=[],
    install_requires=[
        "requests>=2.0.0",
        "bs4==0.0.1",
    ],
    python_requires='>=3.6',
)
