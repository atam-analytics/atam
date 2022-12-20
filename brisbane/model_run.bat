@echo off

:: Set Directories
set model_dir="C:\Users\peter\Documents\GitHub\atam-analytics\atam\brisbane"
set python_dir="C:\Users\peter\Documents\GitHub\Python37\python.exe"

:: Call Model Run
%python_dir% "%model_dir%\model_run_R0002.py"

PAUSE