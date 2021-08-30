@echo off

SETLOCAL

rem Root folder of the project
set LOC=%~dp0..

rem Create virtual environment
py -m venv %LOC%\venv

rem Activate virtual environment
CALL %LOC%\venv\Scripts\activate.bat

rem Update pip
py -m pip install --upgrade pip

rem Install requirements and dev requirements
pip3 install -r  %LOC%\requirements.txt
pip3 install -r  %LOC%\requirements_dev.txt

echo Done!

ENDLOCAL