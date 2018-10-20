#!/usr/bin/env python

from setuptools import setup, find_packages

name = "tonyc_utils"
setup(name=name,
      version='1.0',
      description='Various utilities',
      author='Tony Cebzanov',
      author_email='tonycpsu@gmail.com',
      classifiers=[
          'Environment :: Console',
          'Intended Audience :: Developers'
      ],
      packages=find_packages()
)
