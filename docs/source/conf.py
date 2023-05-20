#! /usr/bin/env python
# Configuration file for the Sphinx documentation builder.

# -- Project information
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../../core/wolf_core/'))


project = 'Wolf'
copyright = '2023, EirLab Community'
author = 'sedelpeuch'

version = '1.1'

# -- General configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.autosummary', 'sphinx.ext.intersphinx', 'myst_parser', ]

intersphinx_mapping = {'python': ('https://docs.python.org/2/', None), 'sphinx': ('https://www.sphinx-doc.org/en/master/', None), }
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'
html_logo = '../img/logo.png'

# -- Options for EPUB output
epub_show_urls = 'footnote'
master_doc = 'index'
os.environ['DISPLAY'] = ':0'

