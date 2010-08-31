from setuptools import setup, find_packages
import os
import sys

version = '0.1'
shortdesc = "Mrs. Developer"
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.txt')).read()

setup(name='mrs.developer',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Buildout",
          "Topic :: Software Development :: Libraries :: Python Modules",
      ], # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Florian Friesdorf',
      author_email='flo@chaoflow.net',
      url='http://github.com/chaoflow/mrs.developer',
      license='General Public Licence',
      packages = find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['mrs'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # we currently ship our own argparse
          #'argparse',
          'odict',
      ],
      extras_require={
          'test': [
              'plone.testing',
              'manuel',
          ]
      },
      entry_points={
          # script for everything
          'console_scripts': [
              'mrsd = mrs.developer.console_script:mrsd',
              ],
          # inject our development eggs
          'zc.buildout.extension': ['ext = mrs.developer.extensions:load'],
          # run mrsd hookin to hook into generated scripts
          'zc.buildout.unloadextension': ['ext = mrs.developer.extensions:unload'],
          'mrs.developer.commands': [
              'init = mrs.developer.mrsd:Init',
              'stock = mrs.developer.mrsd:Stock',
              'customize = mrs.developer.mrsd:Customize',
              'paths = mrs.developer.mrsd:Paths',
              'hookin = mrs.developer.mrsd:Hookin',
              'unhook = mrs.developer.mrsd:Unhook',
              'develop = mrs.developer.develop:Develop',
              'checkout = mrs.developer.develop:Checkout',
              'test = mrs.developer.mrsd:Test',
          ]
      },
      )
