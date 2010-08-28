from setuptools import setup, find_packages
import sys, os

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
          'argparse',
          'odict',
      ],
      extras_require={
          'test': [
              'interlude',
          ]
      },
      entry_points={
          # script for everything
          'console_scripts': [
              'mrsd = mrs.developer.console_script:mrsd',
              ],

          'zc.buildout.extension': ['ext = mrs.developer.extensions:load'],

          # unload extension: dump all working_sets info, hookin
          'zc.buildout.unloadextension': ['ext = mrs.developer.extensions:unload'],
          },
      )
