#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

from tern import Version

def _read_long_desc():
    with open("README.md") as fp:
        return fp.read()

def _get_requirements():

    with open("requirements.txt") as fp:
        return [requirement for requirement in fp]

setup(
  name="tern",
  version=Version,
  author="VMWare Inc",
  author_email="FIXME@FIXWHAT.THEEMAIL",
  url="https://github.com/vmware/tern/",
  description=("An inspection tool to find the metadata of the packages" 
    " installed in a container image"),
  long_description=_read_long_desc(),
  license="BSD-2.0",
  keywords="Distribution, Container, Cloud-Native",
  classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Natural Language :: English',
    'Operating System :: POSIX',
    'Operating System :: POSIX :: Linux',
    'Operating System :: MacOS :: MacOS X',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: Implementation :: CPython',
    'Topic :: Software Development'
  ],
  include_package_data=True,
  packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
  install_requires=_get_requirements(),
  test_suite="tests.runtests",
  entry_points={
    "console_scripts": ["tern = tern.__main__:main"]
  },
)
