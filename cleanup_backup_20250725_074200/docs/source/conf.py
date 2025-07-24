# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import json
sys.path.insert(0, os.path.abspath('../..'))

project = 'VisionAI-ClipsMaster'
copyright = '2024, VisionAI Team'
author = 'VisionAI Team'

# Load version from version configuration
try:
    with open('../../configs/docs_version.json', 'r', encoding='utf-8') as f:
        version_data = json.load(f)
        release = version_data['current_version']
except (FileNotFoundError, json.JSONDecodeError, KeyError):
    release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx_autodoc_typehints',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = []

language = 'zh_CN'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Add JavaScript and CSS files for version selector
html_js_files = [
    'version_selector.js',
]
html_css_files = [
    'version_selector.css',
]

# Version info
html_context = {
    'current_version': release,
    'version_info': '/configs/docs_version.json',
}

# -- Extension configuration -------------------------------------------------
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_typehints_format = 'short'

# -- Intersphinx configuration ---------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'PIL': ('https://pillow.readthedocs.io/en/stable/', None),
}

# -- Napoleon settings -----------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None
