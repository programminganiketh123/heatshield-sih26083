@echo off
setlocal
cd /d "%~dp0"
echo.
echo [1/3] Checking project files...
python preflight.py
if errorlevel 1 (
  echo.
  echo Preflight failed. Installing dependencies...
  python -m pip install -r requirements.txt
  if errorlevel 1 exit /b 1
)
echo.
echo [2/3] Starting HEATSHIELD...
python -m streamlit run app.py
endlocal
