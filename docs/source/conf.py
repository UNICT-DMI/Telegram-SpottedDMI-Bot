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
import shutil
import sys

sys.path.insert(0, os.path.abspath("../.."))  # path to the actual project root folder


# -- Custom roles ------------------------------------------------------------
def paramref_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    """Custom role for paramref (used in python-telegram-bot docstrings)"""
    from docutils import nodes

    node = nodes.literal(rawtext, text, **options or {})
    return [node], []


def tg_const_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    """Custom role for tg-const (used in python-telegram-bot docstrings)"""
    from docutils import nodes

    # Create a reference to telegram.constants
    node = nodes.literal(rawtext, text, **options or {})
    return [node], []


def wiki_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    """Custom role for wiki (used in python-telegram-bot docstrings)"""
    from docutils import nodes

    # Create a reference node for wiki links
    node = nodes.literal(rawtext, text, **options or {})
    return [node], []


def setup(app):
    """Setup function for Sphinx"""
    app.add_role("paramref", paramref_role)
    app.add_role("tg-const", tg_const_role)
    app.add_role("wiki", wiki_role)


# -- Project information -----------------------------------------------------

project = "Spotted dmi bot"
copyright = "2021, UNICT Devs"
author = "Tend, drendog, alepiaz, Helias, Herbrant, LightDestory, TaToTanWeb"

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
    "m2r2",  # to convert markdown to rst
    "sphinxcontrib.mermaid",  # to render mermaid diagrams
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "../../venv",
    "../../.venv",
    "../../build",
    "../../htmlcov",
    "**/.git",
    "**/__pycache__",
    "**/*.pyc",
]

# Ignore checking these specific broken links from external libraries
# These anchors don't exist in the Telegram documentation anymore
linkcheck_ignore = [
    r"https://core\.telegram\.org/stickers#animation-requirements",
    r"https://core\.telegram\.org/stickers#video-requirements",
    r"https://github\.com/python-telegram-bot/python-telegram-bot/wiki/Frequently-Asked-Questions#what-do-the-per_-settings-in-conversationhandler-do",
]

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

# -- Options for autodoc -----------------------------------------------------
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "imported-members": False,  # Don't document imported members like Application
}

# Skip documenting members that are imported from other modules
autodoc_inherit_docstrings = False

# -- Configuration of "sphinx_autodoc_typehints" -----------------------------
typehints_use_rtype = False
typehints_defaults = "comma"

# Suppress warnings about forward references in type annotations and docutils warnings from external libraries
suppress_warnings = [
    "sphinx_autodoc_typehints.forward_reference",
    "docutils.parsers.rst",  # Suppress RST parsing warnings from external libraries
    "app.add_node",  # Suppress node addition warnings
]

# Additional configuration to reduce noise from external library docstrings
autodoc_warningiserror = False
nitpicky = False

# -- Run sphinx-apidoc -------------------------------------------------------
# This hack is necessary since RTD does not issue `sphinx-apidoc` before running
# `sphinx-build -b html . _build/html`. See Issue:
# https://github.com/readthedocs/readthedocs.org/issues/1139
# DON'T FORGET: Check the box "Install your project inside a virtualenv using
# setup.py install" in the RTD Advanced Settings.
# Additionally it helps us to avoid running apidoc manually

try:  # for Sphinx >= 1.7
    from sphinx.ext import apidoc
except ImportError:
    from sphinx import apidoc

output_dir = os.path.join(os.path.dirname(__file__), "api")
module_dir = os.path.join(os.path.dirname(__file__), "../../src/spotted")

# Preserve the inclusions directory before removing api directory
inclusions_dir = os.path.join(output_dir, "inclusions")
inclusions_backup = None
if os.path.exists(inclusions_dir):
    import tempfile

    inclusions_backup = tempfile.mkdtemp()
    shutil.copytree(inclusions_dir, os.path.join(inclusions_backup, "inclusions"))

try:
    shutil.rmtree(output_dir)
except FileNotFoundError:
    pass

try:
    import sphinx

    cmd_line = f"sphinx-apidoc --implicit-namespaces -t templates -f -o {output_dir} {module_dir}"

    args = cmd_line.split(" ")
    if tuple(sphinx.__version__.split(".")) >= ("1", "7"):
        # This is a rudimentary parse_version to avoid external dependencies
        args = args[1:]

    apidoc.main(args)

    # Restore the inclusions directory after apidoc runs
    if inclusions_backup and os.path.exists(os.path.join(inclusions_backup, "inclusions")):
        shutil.copytree(os.path.join(inclusions_backup, "inclusions"), inclusions_dir)
        shutil.rmtree(inclusions_backup)
    elif not os.path.exists(inclusions_dir):
        # Create inclusions directory and application_run_tip.rst if they don't exist
        os.makedirs(inclusions_dir, exist_ok=True)
        with open(os.path.join(inclusions_dir, "application_run_tip.rst"), "w") as f:
            f.write(".. tip::\n")
            f.write("    For more information on running a Telegram bot application, see the\n")
            f.write("    `python-telegram-bot documentation <https://docs.python-telegram-bot.org/>`_.\n")
except Exception as e:
    print("Running `sphinx-apidoc` failed!\n{}".format(e))

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
    "telegram": ("https://docs.python-telegram-bot.org/en/stable/", None),
}

# -- Options for sphinxcontrib.mermaid ---------------------------------------
mermaid_init_js = """
mermaid.initialize({
    startOnLoad: true,
    theme: 'dark',
});
"""
