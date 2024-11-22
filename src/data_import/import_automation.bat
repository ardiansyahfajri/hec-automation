@echo off
REM Set up the Vortex environment
set "VORTEX_HOME=apps/vortex-0.10.28"
set "PATH=%VORTEX_HOME%\bin;%VORTEX_HOME%\bin\gdal;%PATH%"
set "GDAL_DATA=%VORTEX_HOME%\bin\gdal\gdal-data"
set "PROJ_LIB=%VORTEX_HOME%\bin\gdal\projlib"
set "CLASSPATH=%VORTEX_HOME%\lib\*"

REM Run the Jython script
C:\jython2.7.4\bin\jython.exe src\data_import\import_automation.py