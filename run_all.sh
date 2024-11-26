#!/bin/bash

# Activate Python virtual environment
source venv/bin/activate

# Run Python scripts
echo "Running import_ftp_ecmwf.py..."
python src/data_import/import_ftp_ecmwf.py
if [ $? -ne 0 ]; then
  echo "Error running import_ftp_ecmwf.py"
  exit 1
fi

echo "Running rain_thiessen.py..."
python src/visualization/rain_thiessen.py
if [ $? -ne 0 ]; then
  echo "Error running rain_thiessen.py"
  exit 1
fi

echo "Running rain_animation.py..."
python src/animation/rain_animation.py
if [ $? -ne 0 ]; then
  echo "Error running rain_animation.py"
  exit 1
fi

# Run batch scripts using wine or a Windows emulator (if on Unix-like OS)
echo "Running import_automation.bat..."
cmd.exe /c src/data_import/import_automation.bat
if [ $? -ne 0 ]; then
  echo "Error running import_automation.bat"
  exit 1
fi

echo "Running forecast_hec_hms.bat..."
cmd.exe /c src/forecast/forecast_hec_hms.bat
if [ $? -ne 0 ]; then
  echo "Error running forecast_hec_hms.bat"
  exit 1
fi

echo "All tasks completed successfully!"
