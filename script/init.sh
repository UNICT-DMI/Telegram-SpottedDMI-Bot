#!/bin/bash

# Root folder of the project
SCRIPT=$(readlink -f "$0")
LOC=$(dirname "$SCRIPT")/..

# Create virtual environment
python3 -m venv $LOC/venv

# Activate virtual environment
source $LOC/venv/bin/activate

# Update pip
pip install --upgrade pip

# Install requirements and dev requirements
pip3 install -r $LOC/requirements.txt
pip3 install -r $LOC/requirements_dev.txt

pip3 --version