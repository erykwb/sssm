# -*- coding: utf-8 -*-

import sys
import os
from datetime import date


# -- General configuration ------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode'
]
needs_sphinx = '1.3'
source_suffix = '.rst'
master_doc = 'index'
project = 'sssm Module'
copyright = '2016, Florenz Hollebrandse'
release = '1.0.0'
version = '1.0'
pygments_style = 'sphinx'
autodoc_member_order = 'bysource'

# -- Options for HTML output ----------------------------------------------

import sphinx_rtd_theme
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_static_path = ['_static']
html_last_updated_fmt = '%d/%m/%Y'
html_show_sphinx = False
htmlhelp_basename = 'doc'
