@echo off
REM Set HEC-HMS environment
set "HMS=apps\HEC-HMS-4.10"
set "PATH=%HMS%\bin\gdal;%PATH%"
set "GDAL_DRIVER_PATH=%HMS%\bin\gdal\gdalplugins"
set "GDAL_DATA=%HMS%\bin\gdal\gdal-data"
set "PROJ_LIB=%HMS%\bin\gdal\projlib"

REM Add HEC-HMS libraries to classpath
set "CLASSPATH=%HMS%\hms.jar;%HMS%\lib\*"

REM Run Jython script
C:\jython2.7.4\bin\jython.exe -Djava.library.path="%HMS%\bin;%HMS%\bin\gdal;%HMS%\bin\hdf" src\forecast\forecast_hec_hms.py
