@echo off
echo ////////////////
echo Running model...
echo //////////////// 

:: Set Directories
set model_dir=%cd%
echo model_dir=%model_dir%

:: Call Model Run #1
set model_id="R0001"
set network_case="01_BASE_NET"
set demand_case="01_BASE_DEMAND"
"%model_dir%\02_scripts\Python37\Python37\python.exe" "%model_dir%\model_run.py" %model_id% %network_case% %demand_case%

:: Call Model Run #2
set model_id="R0002"
set network_case="02_Example"
set demand_case="02_Example"
"%model_dir%\02_scripts\Python37\Python37\python.exe" "%model_dir%\model_run.py" %model_id% %network_case% %demand_case%

echo ////////////////
echo Run Complete.
echo //////////////// 
PAUSE