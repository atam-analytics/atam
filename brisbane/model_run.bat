@echo off
echo ////////////////
echo Running model...
echo //////////////// 

:: Set Directories
set model_dir=%cd%
echo model_dir=%model_dir%

:: Call Model Run
"%model_dir%\02_scripts\Python37\Python37\python.exe" "%model_dir%\model_run_R0003.py"

echo ////////////////
echo Run Complete.
echo //////////////// 
PAUSE