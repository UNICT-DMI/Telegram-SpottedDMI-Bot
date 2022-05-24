#!/bin/bash
pip3 install sphinx sphinx_rtd_theme sphinx_autodoc_typehints sphinx-rtd-dark-mode

#######################
# Build .rts files:
# sphinx-apidoc -o docs/source .
# --Edit the .rts files--
#######################
# Windows:
# docs/make html
#######################
# Linux:
# cd docs && make html
#######################

# https://github.com/TendTo/sphinx-doc for more info