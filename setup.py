
from setuptools import setup

setup(
    name='setuptools_zig',
    version="0.2.1",
    author_email='a.van.der.neut@ruamel.eu',
    description='A setuptools extension, for building cpython extensions with Zig.',
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    url='https://sourceforge.net/p/setuptools-zig/code/ref/default/',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    python_requires='>=3',
    py_modules=['setuptools_zig'],
    keywords='',
    entry_points={"distutils.setup_keywords": ['build_zig=setuptools_zig:setup_build_zig']},
)
