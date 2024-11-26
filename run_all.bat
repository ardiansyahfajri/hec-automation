@echo off
REM Activate the Python virtual environment
call venv\Scripts\activate

REM Run the Python scripts
python src\data_import\import_ftp_ecmwf.py
if %errorlevel% neq 0 goto :error

python src\visualization\rain_thiessen.py
if %errorlevel% neq 0 goto :error

python src\animation\rain_animation.py
if %errorlevel% neq 0 goto :error

REM Run the batch scripts
call src\data_import\import_automation.bat
if %errorlevel% neq 0 goto :error

call src\forecast\forecast_hec_hms.bat
if %errorlevel% neq 0 goto :error

REM End of the process
echo All tasks completed successfully!
goto :end

:error
echo An error occurred. Process terminated.
exit /b 1

:end
exit /b 0
