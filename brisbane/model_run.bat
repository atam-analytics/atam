@echo off

:: Set Directories
set model_dir="C:\Users\peter\Documents\GitHub\atam-analytics\atam\brisbane"

:: Call Model Run
"%model_dir%\02_scripts\Python37\Python37\python.exe" "%model_dir%\model_run_R0003.py"

PAUSE