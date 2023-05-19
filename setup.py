from setuptools import setup, find_packages

setup(name='wolf', version='1.1.0', description='', author='sedelpeuch', author_email='sebastien@delpeuch.net', packages=find_packages(),
      install_requires=[  # List your project dependencies here
      ], entry_points={'console_scripts': ['wolf = wolf.__main__:main']},
      classifiers=['Development Status :: 3 - Alpha', 'License :: OSI Approved :: GPL3 License', 'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.8', 'Programming Language :: Python :: 3.9', ], )
