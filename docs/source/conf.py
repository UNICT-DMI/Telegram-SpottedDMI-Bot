# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))  # path to the actual project root folder

# -- Project information -----------------------------------------------------

project = "Spotted dmi bot"
copyright = "2021, Tend, drendog, alepiaz, Helias"
author = "Tend, drendog, alepiaz, Helias"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",  # to run doctests
    "sphinx.ext.napoleon",  # to use NumPy and Google style docstrings
    "sphinx.ext.githubpages",  # generates the .nojekyll file
    "sphinx.ext.viewcode",  # add source code links to the documentation
    "sphinx_rtd_dark_mode",  # dark mode for ReadTheDocs
    "sphinx_autodoc_typehints",  # improves the type hinting
    "sphinx.ext.viewcode",  # add source code links to the documentation
    "sphinx.ext.coverage",  # add coverage links to the documentation
    "sphinx.ext.intersphinx",  # add external mapping to other documentation
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"  # [optional, to use the far superior Read the Docs theme]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = [
    "css/dark.css",
]

html_logo = "_static/img/spotted-logo.jpg"

# -- Extension configuration -------------------------------------------------

# Configuration of "sphinx_autodoc_typehints"
typehints_use_rtype = False
typehints_defaults = "comma"

# -- External mapping --------------------------------------------------------
python_version = ".".join(map(str, sys.version_info[0:2]))
intersphinx_mapping = {
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
    "python": ("https://docs.python.org/" + python_version, None),
    "matplotlib": ("https://matplotlib.org", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "sklearn": ("https://scikit-learn.org/stable", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    "setuptools": ("https://setuptools.pypa.io/en/stable/", None),
    "pyscaffold": ("https://pyscaffold.org/en/stable", None),
}
