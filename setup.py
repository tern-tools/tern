#!/usr/bin/env python
from setuptools import setup, find_packages

version = "0.2.0"

def _read_long_desc():
    with open("README.md") as fp:
        return fp.read()

setup(
  name="tern",
  version=version,
  author="VMWare Inc",
  author_email="FIXME@FIXWHAT.THEEMAIL",
  url="https://github.com/vmware/tern/",
  description=("An inspection tool to find the metadata of the packages" 
    " installed in a container image"),
  long_description=_read_long_desc()
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
  packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests",
      "debian"]),
  install_requires=["pyyaml"],
  test_suite="tests.runtests",
  entry_points={
    "console_scripts": ["tern = tern.__init__.py:main"]
  },
)
